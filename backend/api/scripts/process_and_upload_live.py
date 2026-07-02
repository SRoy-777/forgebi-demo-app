import os
import time
import boto3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# R2 Configuration using environment variables
ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "").strip()
ACCESS_KEY = os.getenv("R2_ACCESS_KEY", "").strip()
SECRET_KEY = os.getenv("R2_SECRET_KEY", "").strip()

if not all([ACCOUNT_ID, ACCESS_KEY, SECRET_KEY]):
    raise ValueError("Missing required R2 credentials in environment variables.")

BUCKET_NAME = "orient-analytics-snapshots"

# Ensure directories exist
input_file = r"C:\Projects\orient_analytics_platform\data\raw\Quick Customer List.csv"
output_path = r"C:\Projects\orient_analytics_platform\data\processed\1_live"
output_file = os.path.join(output_path, "live_customer_list.parquet")

def process_and_upload():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting live customer data processing...")
    
    if not os.path.exists(input_file):
        print(f"Error: Raw CSV input file not found at: {input_file}")
        return False
        
    try:
        # 1. Read input CSV
        df = pd.read_csv(
            input_file,
            usecols=["Customer No.", "Location Code"],
            low_memory=False
        )
        
        # 2. Remove duplicate customers
        before_dup = len(df)
        df = df.drop_duplicates(
            subset=["Customer No."],
            keep="last"
        )
        print(f"Duplicate customers removed: {before_dup - len(df):,}")
        
        # 3. Remove DEFAULT customers
        before_def = len(df)
        df = df[
            ~df["Customer No."]
            .astype(str)
            .str.strip()
            .str.startswith("DEFAULT", na=False)
        ]
        print(f"DEFAULT customers removed: {before_def - len(df):,}")
        
        # 4. Filter out Location Codes starting with 100
        df["Location Code"] = df["Location Code"].astype(str).str.strip()
        df = df[~df["Location Code"].str.startswith("100", na=False)]
        print("Location codes starting with 100 removed")
        
        # 5. Apply location mapping
        location_mapping = {
            "103": "SILIGURI",
            "106": "JALPAIGURI",
            "113": "MALBAZAR",
            "120": "RAGHUNATHGANJ",
            "121": "BELDANGA",
            "124": "SAINTHIA",
            "125": "MOLLARPUR",
            "123": "BETHUADAHARI",
            "126": "CHAKDAHA",
            "104": "BALURGHAT",
            "105": "ISLAMPUR",
            "102": "RAIGANJ",
            "111": "KALIYAGANJ",
            "115": "RAIGANJ MEGA",
            "107": "ALIPURDUAR",
            "112": "FALAKATA",
            "127": "MATHABHANGA",
            "FRN001": "DHUPGURI",
            "116": "KALIACHAK",
            "117": "GAZOLE",
            "118": "DHULIYAN",
            "119": "SUJAPUR"
        }
        df["Location Name"] = df["Location Code"].map(location_mapping)
        print("Location mapping completed")
        
        # 6. Rename columns
        df.rename(columns={"Customer No.": "Customer Code"}, inplace=True)
        
        # 7. Filter columns
        df = df[["Location Code", "Location Name", "Customer Code"]]
        
        # 8. Save to Parquet
        os.makedirs(output_path, exist_ok=True)
        df.to_parquet(output_file, index=False)
        print(f"Successfully processed customer list: {len(df):,} rows saved to {output_file}.")
        
        # 7. Upload to Cloudflare R2
        print(f"Uploading live_customer_list.parquet to R2 bucket: {BUCKET_NAME}...")
        s3 = boto3.client(
            service_name='s3',
            endpoint_url=f'https://{ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY
        )
        s3.upload_file(output_file, BUCKET_NAME, "live_customer_list.parquet")
        print("Upload completed successfully.")
        return True
        
    except Exception as e:
        print(f"Error during processing/uploading: {e}")
        return False

if __name__ == "__main__":
    process_and_upload()
