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

API_URL = (
    "https://api.businesscentral.dynamics.com"
    "/v2.0/ca9359fb-16ff-4067-8c86-89513acaa3b2"
    "/Production/ODataV4"
    "/Company('My%20Company')/BiCustomerAPI"
)

OUTPUT_FILE = (
    r"C:\Projects\orient_analytics_platform\data\raw"
    r"\Quick Customer List.csv"
)

UNIQUE_KEY_API = "No"
UNIQUE_KEY_CSV = "Customer No."

# =====================================================
# COLUMN MAPPING
# =====================================================

column_mapping = {
    "_Phone_No": "Phone No.",
    "No": "Customer No.",
    "E_Mail": "Email",
    "Whatsapp_No": "Whatsapp No.",
    "Father_Name": "Father Name",
    "P_A_N_No": "P.A.N. No.",
    "Birth_Date": "Birth Date",
    "Anniversary_Date": "Anniversary Date",
    "Aadhar_No": "Aadhar No.",
    "PassPort_No": "Passport No.",
    "Driving_License": "Driving License",
    "Voter_ID": "Voter ID",
    "KYC_Document_Type": "KYC Document Type",
    "KYC_Document_No": "KYC Document No.",
    "Address_2": "Address 2",
    "Post_Code": "Post Code",
    "State_Code": "State Code",
    "Location_Code": "Location Code"
}

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
# FIRST RUN OR INCREMENTAL RUN
# =====================================================

first_run = not os.path.exists(OUTPUT_FILE)

if first_run:

    print("\n=================================")
    print("FIRST RUN DETECTED")
    print("=================================")
    print("Customer file not found.")
    print("Performing FULL LOAD from BC.")

else:

    print("\n=================================")
    print("INCREMENTAL RUN DETECTED")
    print("=================================")

# =====================================================
# FIND LATEST CUSTOMER CODES
# =====================================================

latest_dcu = None
latest_cusd = None
latest_cus = None

if not first_run:

    existing_df = pd.read_csv(
        OUTPUT_FILE,
        usecols=[UNIQUE_KEY_CSV],
        dtype=str,
        low_memory=False
    )

    customer_codes = (
        existing_df[UNIQUE_KEY_CSV]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Ignore DEFAULT customers
    customer_codes = customer_codes[
        ~customer_codes.str.startswith("DEFAULT")
    ]

    customer_codes = customer_codes[
        customer_codes.str.startswith(
            ("DCU", "CUSD", "CUS")
        )
    ]

    dcu_codes = customer_codes[
        customer_codes.str.startswith("DCU")
    ]

    cusd_codes = customer_codes[
        customer_codes.str.startswith("CUSD")
    ]

    cus_codes = customer_codes[
        customer_codes.str.startswith("CUS")
        & ~customer_codes.str.startswith("CUSD")
    ]

    if len(dcu_codes) > 0:
        latest_dcu = dcu_codes.max()

    if len(cusd_codes) > 0:
        latest_cusd = cusd_codes.max()

    if len(cus_codes) > 0:
        latest_cus = cus_codes.max()

    print(f"Latest DCU  : {latest_dcu}")
    print(f"Latest CUSD : {latest_cusd}")
    print(f"Latest CUS  : {latest_cus}")

# =====================================================
# BUILD FILTER URLS
# =====================================================

filter_urls = []

if first_run:

    filter_urls.append(API_URL)

else:

    if latest_dcu:

        filter_urls.append(
            API_URL +
            f"?$filter=startswith(No,'DCU') "
            f"and No gt '{latest_dcu}'"
        )

    if latest_cusd:

        filter_urls.append(
            API_URL +
            f"?$filter=startswith(No,'CUSD') "
            f"and No gt '{latest_cusd}'"
        )

    if latest_cus:

        filter_urls.append(
            API_URL +
            f"?$filter=startswith(No,'CUS') "
            f"and No gt '{latest_cus}'"
        )

# =====================================================
# FETCH ONLY NEW CUSTOMERS
# =====================================================

all_records = []

for base_url in filter_urls:

    next_url = base_url

    while next_url:

        print(f"\nFetching: {next_url}")

        response = requests.get(
            next_url,
            headers=headers,
            timeout=120
        )

        if response.status_code != 200:

            print("Status:", response.status_code)
            print(response.text)

            raise Exception(
                "API request failed."
            )

        data = response.json()

        records = data.get("value", [])

        all_records.extend(records)

        print(
            f"Retrieved {len(records):,} rows "
            f"(Total: {len(all_records):,})"
        )

        next_url = data.get("@odata.nextLink")

# =====================================================
# NO NEW CUSTOMERS
# =====================================================

if len(all_records) == 0:

    print("\n=================================")
    print("NO NEW CUSTOMERS FOUND")
    print("=================================")

    exit()

# =====================================================
# CONVERT TO DATAFRAME
# =====================================================

df = pd.DataFrame(all_records)

if latest_cus:

    df = df[
        ~(
            df["No"].str.startswith("CUSD", na=False)
            &
            (df["No"] <= latest_cusd)
        )
    ]

# Remove duplicate API overlap
df = df.drop_duplicates(
    subset=["No"],
    keep="last"
)

# Keep only:
# - DCUS...
# - CUSD...
# - CUS... (but NOT CUSD...)
df = df[
    df["No"].str.startswith("DCUS", na=False)
    |
    df["No"].str.startswith("CUSD", na=False)
    |
    (
        df["No"].str.startswith("CUS", na=False)
        &
        ~df["No"].str.startswith("CUSD", na=False)
    )
]

if not first_run:

    existing_keys = set(
        pd.read_csv(
            OUTPUT_FILE,
            usecols=["Customer No."],
            dtype=str,
            low_memory=False
        )["Customer No."]
        .astype(str)
        .str.strip()
    )

    df = df[
        ~df["No"]
        .astype(str)
        .str.strip()
        .isin(existing_keys)
    ]

if df.empty:

    print("\n=================================")
    print("NO NEW CUSTOMERS FOUND")
    print("=================================")

    exit()

# =====================================================
# RENAME COLUMNS
# =====================================================

df.rename(
    columns=column_mapping,
    inplace=True
)

# =====================================================
# APPEND TO EXISTING CSV
# =====================================================

if first_run:

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

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
print(f"New Customers Added: {len(df):,}")
print(f"Saved To: {OUTPUT_FILE}")