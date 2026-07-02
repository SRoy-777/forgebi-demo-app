import os
import requests
import pandas as pd
from urllib.parse import quote
from msal import ConfidentialClientApplication

# =====================================================
# CONFIGURATION
# =====================================================

TENANT_ID = "ca9359fb-16ff-4067-8c86-89513acaa3b2"

CLIENT_ID = "1ca09d38-262a-4b5e-ad6d-83e305d12e4f"
CLIENT_SECRET = "m2Z8Q~.OYsvrXI96ssDjci2.BwMMb4J5EwNFRcD0"

COMPANIES = [
    "DHUPGURI - LOKENATH JEWELS",
    "My Company"
]

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://api.businesscentral.dynamics.com/.default"]

OUTPUT_FILE = (
    r"D:\1_API_Config_test\BC365_Extractor\data"
    r"\Foot Fall.csv"
)

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
# FETCH DATA FOR ALL COMPANIES
# =====================================================

all_records = []

for company in COMPANIES:

    encoded_company = quote(company)

    api_url = (
        "https://api.businesscentral.dynamics.com"
        f"/v2.0/{TENANT_ID}"
        "/Production/ODataV4"
        f"/Company('{encoded_company}')"
        "/BiFootFallAPI"
    )

    next_url = api_url

    print("\n" + "=" * 60)
    print(f"COMPANY: {company}")
    print("=" * 60)

    while next_url:

        print(f"Fetching: {next_url}")

        response = requests.get(
            next_url,
            headers=headers,
            timeout=120
        )

        if response.status_code != 200:
            print(f"\nFailed for company: {company}")
            print("Status:", response.status_code)
            print(response.text)
            break

        data = response.json()

        records = data.get("value", [])

        # Add source company column
        for row in records:
            row["Company_Name"] = company

        all_records.extend(records)

        print(
            f"Retrieved {len(records):,} rows "
            f"(Total: {len(all_records):,})"
        )

        next_url = data.get("@odata.nextLink")

# =====================================================
# SAVE CSV (FULL REFRESH)
# =====================================================

df = pd.DataFrame(all_records)

# =====================================================
# RENAME COLUMNS
# =====================================================

column_mapping = {
    "_x0031_0_To_11": "10 To 11",
    "_x0031_1_To_12": "11 To 12",
    "_x0031_2_To_1": "12 To 1",
    "_x0031__To_2": "1 To 2",
    "_x0032__To_3": "2 To 3",
    "_x0033__To_4": "3 To 4",
    "_x0034__To_5": "4 To 5",
    "_x0035__To_6": "5 To 6",
    "_x0036__To_7": "6 To 7",
    "_x0037__To_8": "7 To 8",
    "_x0038__To_9": "8 To 9"
}

df.rename(columns=column_mapping, inplace=True)

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

print("\n=================================")
print("FOOT FALL EXTRACTION COMPLETED")
print("=================================")
print(f"Total Rows: {len(df):,}")
print(f"Total Columns: {len(df.columns)}")
print(f"Saved To: {OUTPUT_FILE}")