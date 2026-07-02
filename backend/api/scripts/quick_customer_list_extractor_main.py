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
SCOPE = ["https://api.businesscentral.dynamics.com/.default"]

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

token_response = app.acquire_token_for_client(scopes=SCOPE)

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
# FETCH ALL RECORDS
# =====================================================

all_records = []
next_url = API_URL

while next_url:

    print(f"Fetching: {next_url}")

    response = requests.get(
        next_url,
        headers=headers,
        timeout=120
    )

    if response.status_code != 200:
        print("Status:", response.status_code)
        print(response.text)
        raise Exception("API request failed.")

    data = response.json()

    records = data.get("value", [])
    all_records.extend(records)

    print(
        f"Retrieved {len(records):,} rows "
        f"(Total: {len(all_records):,})"
    )

    next_url = data.get("@odata.nextLink")

# =====================================================
# CONVERT TO DATAFRAME
# =====================================================

df = pd.DataFrame(all_records)

if df.empty:
    print("No records returned from API.")
    exit()

# =====================================================
# SAVE / APPEND LOGIC
# =====================================================

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# FIRST RUN
if not os.path.exists(OUTPUT_FILE):

    output_df = df.rename(columns=column_mapping)

    output_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n=================================")
    print("FIRST LOAD COMPLETED")
    print("=================================")
    print(f"Rows Saved: {len(output_df):,}")
    print(f"Saved To: {OUTPUT_FILE}")

# INCREMENTAL RUN
else:

    existing_keys = set(
        pd.read_csv(
            OUTPUT_FILE,
            usecols=[UNIQUE_KEY_CSV],
            dtype=str,
            low_memory=False
        )[UNIQUE_KEY_CSV]
        .astype(str)
        .str.strip()
    )

    new_rows = df[
        ~df[UNIQUE_KEY_API]
        .astype(str)
        .str.strip()
        .isin(existing_keys)
    ]

    rows_added = len(new_rows)

    if rows_added > 0:

        output_new_rows = new_rows.rename(columns=column_mapping)

        output_new_rows.to_csv(
            OUTPUT_FILE,
            mode="a",
            header=False,
            index=False,
            encoding="utf-8-sig"
        )

        print("\n=================================")
        print("INCREMENTAL LOAD COMPLETED")
        print("=================================")
        print(f"New Customers Added: {rows_added:,}")

    else:

        print("\n=================================")
        print("NO NEW CUSTOMERS FOUND")
        print("=================================")
        print(f"Existing Customers Checked: {len(existing_keys):,}")