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
input_file = r"C:\Projects\orient_analytics_platform\data\raw\Posted Estimate.csv"
output_path = r"C:\Projects\orient_analytics_platform\data\processed\1_live"
output_file = os.path.join(output_path, "live_posted_estimate.parquet")

def process_and_upload():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting live sales data processing...")
    
    if not os.path.exists(input_file):
        print(f"Error: Raw CSV input file not found at: {input_file}")
        return False
        
    try:
        # 1. Read input CSV
        df = pd.read_csv(
            input_file,
            usecols=[
                "Document_No",
                "Customer_Code",
                "Date",
                "Location",
                "Location_Name",
                "Final_Amount_to_Customer",
                "SystemCreatedAt"
            ],
            low_memory=False
        )
        
        # 2. Clean Customer Code and Location Code columns
        df["Customer_Code"] = df["Customer_Code"].astype(str).str.strip()
        df["Location"] = df["Location"].astype(str).str.strip()
        
        # Deduct 3% from Final_Amount_to_Customer for display adjustment (before showing aggregates)
        if "Final_Amount_to_Customer" in df.columns:
            df["Final_Amount_to_Customer"] = pd.to_numeric(df["Final_Amount_to_Customer"], errors='coerce').fillna(0) * 0.97
        
        # 3. Save to Parquet
        os.makedirs(output_path, exist_ok=True)
        df.to_parquet(output_file, index=False)
        print(f"Successfully processed sales estimates: {len(df):,} rows saved to {output_file}.")
        
        # 4. Upload to Cloudflare R2
        print(f"Uploading live_posted_estimate.parquet to R2 bucket: {BUCKET_NAME}...")
        s3 = boto3.client(
            service_name='s3',
            endpoint_url=f'https://{ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY
        )
        s3.upload_file(output_file, BUCKET_NAME, "live_posted_estimate.parquet")
        print("Upload completed successfully.")
        return True
        
    except Exception as e:
        print(f"Error during processing/uploading: {e}")
        return False

if __name__ == "__main__":
    process_and_upload()
