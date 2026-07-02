import requests
import pandas as pd
from msal import ConfidentialClientApplication
import os

# =====================================================
# CONFIGURATION
# =====================================================

CLIENT_ID = '1ca09d38-262a-4b5e-ad6d-83e305d12e4f'
CLIENT_SECRET = 'm2Z8Q~.OYsvrXI96ssDjci2.BwMMb4J5EwNFRcD0'
TENANT_ID = 'ca9359fb-16ff-4067-8c86-89513acaa3b2'

ODATA_URL = (
    "https://api.businesscentral.dynamics.com"
    "/v2.0/ca9359fb-16ff-4067-8c86-89513acaa3b2"
    "/Production/ODataV4"
    "/Company('My%20Company')/BiTagListAPI"
)

LOCAL_FOLDER = r'C:\Projects\orient_analytics_platform\data\raw'

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://api.businesscentral.dynamics.com/.default"]

# =====================================================
# AUTHENTICATION
# =====================================================

app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)

token_result = app.acquire_token_for_client(scopes=SCOPE)

if "access_token" in token_result:

    token = token_result["access_token"]

    headers = {
        'Authorization': f'Bearer {token}'
    }

    # =====================================================
    # FETCH DATA WITH PAGINATION
    # =====================================================

    all_data = []
    next_url = ODATA_URL

    print("Fetching data from BC365 (this may take a moment)...")

    while next_url:

        response = requests.get(
            next_url,
            headers=headers
        )

        if response.status_code == 200:

            json_response = response.json()

            all_data.extend(
                json_response.get('value', [])
            )

            next_url = json_response.get('@odata.nextLink')

            if next_url:
                print(
                    f"Fetched {len(all_data):,} rows so far, "
                    f"getting next page..."
                )

        else:

            print(
                f"Error {response.status_code}: "
                f"{response.text}"
            )
            break

    # =====================================================
    # SAVE DATA
    # =====================================================

    if all_data:

        df = pd.DataFrame(all_data)

        # =====================================================
        # RENAME COLUMNS TO MATCH EXCEL
        # =====================================================

        column_mapping = {
            "Tag_No": "Tag No.",
            "Tag_Type": "Tag Type",
            "JOB_ID": "Job ID",
            "JOB_TYPE": "Job Type",
            "JOB_CARD_TYPE": "Job Card Type",
            "ITEM_ID": "Item ID",
            "DESCRIPTION": "Description",
            "COUNTER_CODE": "Counter Code",
            "PURITY": "Purity",
            "NO_OF_PIECES": "NO OF PIECES",
            "GROSS_WEIGHT": "Gross Weight",
            "NET_WEIGHT": "NET Weight",
            "FINE_WEIGHT": "Fine Weight",
            "DIAMOND_WEIGHT": "Diamond Weight",
            "Target_Bin_Code": "Target Bin Code",
            "INVENT_LOCATION_ID": "Invent Location ID",
            "BRAND": "Brand",
            "CERTIFICATE": "Certificate",
            "CERTIFICATE_NO": "Certificate No.",
            "COLLECTION_CODE": "Collection Code",
            "DESIGN_CODE": "Design Code",
            "HALLMARKING": "Hallmarking",
            "HMHU_ID": "HUID",
            "BULK_TAG": "Bulk Tag",
            "MANUAL_TAG": "Manual Tag",
            "MRP": "MRP",
            "ORNAMENT_CATEGORY_CODE": "Ornament Category Code",
            "ORNAMENT_SIZE": "Ornament Size",
            "OTHER_CHARGES_AMOUNT": "Other Charges Amount",
            "PARENT_TAG_NO": "Parent Tag No",
            "STONE_AMOUNT": "Stone CT Value",
            "STONE_WEIGHT": "Stone Weight In GRM",
            "TAG_GENERATED_DATE": "Tag Generated Date",
            "Tag_Received_Date": "Tag Received Date",
            "TAG_STATUS": "Tag Status",
            "Certification_Vendor": "Certification Vendor",
            "VEND_ACCOUNT": "Vendor Account",
            "VEND_NAME": "Vendor Name",
            "DIAMOND_PCS": "Diamond PCS",
            "STONE_CPCS": "Stone CPCS",
            "STONE_GPCS": "Stone GPCS",
            "SECTION_ID": "Section ID",
            "QUANTITY": "No Of Tag",
            "STONE_WEIGHT_CT": "Stone Weight CT",
            "ORNAMENT_SUB_CATEGORY_CODE": "Ornament Sub Category Code",
            "WEIGHT_RANGE_CODE": "Weight Range Code",
            "Tag_SubStatus": "Tag SubStatus",
            "QC_Status": "QC Status",
            "QC_Date_Time": "QC Date Time",
            "QC_User_ID": "QC User ID",
            "QC_Remark": "QC Remark"
        }

        df.rename(columns=column_mapping, inplace=True)

        os.makedirs(LOCAL_FOLDER, exist_ok=True)

        file_path = os.path.join(
            LOCAL_FOLDER,
            'Tag List.csv'
        )

        df.to_csv(
            file_path,
            index=False,
            encoding='utf-8-sig'
        )

        print(
            f"Success! {len(df):,} rows saved to {file_path}"
        )

    else:

        print("No data retrieved.")

else:

    print(
        "Authentication failed:",
        token_result.get("error_description")
    )