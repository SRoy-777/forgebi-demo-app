
from urllib.parse import quote
import os
import requests
import pandas as pd
from msal import ConfidentialClientApplication

# =====================================================
# CONFIGURATION
# =====================================================

TENANT_ID = "ca9359fb-16ff-4067-8c86-89513acaa3b2"

CLIENT_ID = "1ca09d38-262a-4b5e-ad6d-83e305d12e4f"
CLIENT_SECRET = "m2Z8Q~.OYsvrXI96ssDjci2.BwMMb4J5EwNFRcD0"

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

SCOPE = [
    "https://api.businesscentral.dynamics.com/.default"
]

BASE_URL = (
    "https://api.businesscentral.dynamics.com"
    "/v2.0/ca9359fb-16ff-4067-8c86-89513acaa3b2"
    "/Production/ODataV4"
)

COMPANIES = [
    "DHUPGURI - LOKENATH JEWELS",
    "My Company"
]

OUTPUT_FILE = (
    r"C:\Projects\orient_analytics_platform\data\raw"
    r"\Posted Estimate.csv"
)

TIMESTAMP_COLUMN = "SystemCreatedAt"

# =====================================================
# AUTHENTICATION
# =====================================================

app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)

token_response = app.acquire_token_for_client(
    scopes=SCOPE
)

if "access_token" not in token_response:
    raise Exception(
        f"Failed to obtain access token:\n{token_response}"
    )

access_token = token_response["access_token"]

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}

# =====================================================
# DETERMINE FULL OR INCREMENTAL LOAD
# =====================================================

first_run = not os.path.exists(OUTPUT_FILE)

company_watermarks = {}
existing_cols = []

if not first_run:
    # Safely migrate existing CSV to include Company column if missing
    try:
        existing_cols = list(pd.read_csv(OUTPUT_FILE, nrows=0).columns)
        if "Company" not in existing_cols:
            print("Migrating existing Posted Estimate.csv to include 'Company' column...")
            full_existing_df = pd.read_csv(OUTPUT_FILE, low_memory=False)
            full_existing_df["Company"] = "My Company"
            existing_cols = ["Company"] + [c for c in full_existing_df.columns if c != "Company"]
            full_existing_df = full_existing_df[existing_cols]
            full_existing_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
            print("Migration complete!")
    except Exception as me:
        print(f"Warning: CSV migration check failed: {me}")

    # Load watermarks per company preserving full sub-millisecond precision
    try:
        use_cols = ["Company", TIMESTAMP_COLUMN] if "Company" in existing_cols else [TIMESTAMP_COLUMN]
        existing_df = pd.read_csv(OUTPUT_FILE, usecols=use_cols, low_memory=False)
        
        # If "Company" is not in the columns yet, default all to "My Company"
        if "Company" not in existing_df.columns:
            existing_df["Company"] = "My Company"
            
        for company, group in existing_df.groupby("Company"):
            # 1. Try to get the max string directly to preserve full 7-digit sub-millisecond precision
            non_null_timestamps = group[TIMESTAMP_COLUMN].dropna().astype(str).str.strip()
            if not non_null_timestamps.empty:
                latest_str = non_null_timestamps.max()
                # OData filters require the standard YYYY-MM-DDTHH:MM:SS.fffffffZ format
                if "T" in latest_str and (latest_str.endswith("Z") or "+" in latest_str):
                    company_watermarks[company] = latest_str
                    continue
            
            # 2. Fallback to datetime parsing if string comparison isn't reliable
            latest_dt = pd.to_datetime(group[TIMESTAMP_COLUMN], utc=True, errors="coerce").max()
            if not pd.isna(latest_dt):
                # Print full microseconds precision
                company_watermarks[company] = latest_dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    except Exception as we:
        print(f"Warning: Could not determine company watermarks: {we}")

# Construct retrieval tasks
retrieval_tasks = []
if first_run:
    print("\n=================================")
    print("FIRST RUN DETECTED")
    print("=================================")
    print("Posted Estimate.csv not found. Performing FULL LOAD for all companies.")
    for company in COMPANIES:
        url = BASE_URL + f"/Company('{quote(company)}')" + "/BiPostedEstimateAPI"
        retrieval_tasks.append((company, url))
else:
    print("\n=================================")
    print("INCREMENTAL RUN DETECTED")
    print("=================================")
    for company in COMPANIES:
        watermark = company_watermarks.get(company)
        if watermark:
            url = (
                BASE_URL
                + f"/Company('{quote(company)}')"
                + "/BiPostedEstimateAPI"
                + "?$filter="
                + f"SystemCreatedAt gt {watermark}"
            )
            print(f"Incremental watermark for '{company}': {watermark}")
        else:
            url = BASE_URL + f"/Company('{quote(company)}')" + "/BiPostedEstimateAPI"
            print(f"No watermark found for '{company}'. Performing full fetch.")
        retrieval_tasks.append((company, url))

# =====================================================
# FETCH DATA WITH PAGINATION
# =====================================================

all_records = []

for company, next_url in retrieval_tasks:
    print(f"\nProcessing company: {company}")
    company_records_count = 0
    
    while next_url:
        print(f"Fetching: {next_url}")
        response = requests.get(
            next_url,
            headers=headers,
            timeout=120
        )

        if response.status_code != 200:
            print(f"Status Code: {response.status_code}")
            print(response.text)
            raise Exception(f"API request failed for company {company}.")

        data = response.json()
        records = data.get("value", [])
        
        # Inject the Company column in each record
        for r in records:
            r["Company"] = company

        all_records.extend(records)
        company_records_count += len(records)
        print(f"Retrieved {len(records):,} rows (Company Total: {company_records_count:,})")

        next_url = data.get("@odata.nextLink")

# =====================================================
# NO NEW RECORDS
# =====================================================

if len(all_records) == 0:
    print("\n=================================")
    print("NO NEW RECORDS FOUND")
    print("=================================")
    exit()

# =====================================================
# CONVERT TO DATAFRAME
# =====================================================

df = pd.DataFrame(all_records)

# Ensure columns align properly
if not first_run and existing_cols:
    for col in existing_cols:
        if col not in df.columns:
            df[col] = None
    df = df[existing_cols]
elif "Company" in df.columns:
    cols = ["Company"] + [c for c in df.columns if c != "Company"]
    df = df[cols]

print("\n=================================")
print("API DATA RECEIVED")
print("=================================")
print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")

# =====================================================
# SAVE FILE
# =====================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

if first_run:

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n=================================")
    print("FULL LOAD COMPLETED")
    print("=================================")
    print(f"Rows Saved: {len(df):,}")

else:

    df.to_csv(
        OUTPUT_FILE,
        mode="a",
        header=False,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n=================================")
    print("INCREMENTAL LOAD COMPLETED")
    print("=================================")
    print(f"New Rows Added: {len(df):,}")

print(f"Saved To: {OUTPUT_FILE}")