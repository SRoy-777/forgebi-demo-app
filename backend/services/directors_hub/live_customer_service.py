import os
import time
import boto3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# R2 Configuration using environment variables or fallback values
ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "").strip()
ACCESS_KEY = os.getenv("R2_ACCESS_KEY", "").strip()
SECRET_KEY = os.getenv("R2_SECRET_KEY", "").strip()
BUCKET_NAME = "orient-analytics-snapshots"
FILE_KEY = "live_customer_list.parquet"

# In-memory cache variables
_cached_df = None
_last_fetch_time = 0.0
_r2_last_modified_time = None
CACHE_TTL = 15.0  # seconds - short TTL for live updates

def get_last_sync_time() -> str:
    """
    Returns the last modified time of the parquet file on R2 in IST.
    """
    global _r2_last_modified_time
    if _r2_last_modified_time is not None:
        return _r2_last_modified_time.strftime("%I:%M:%S %p")
    return "--:--:--"

def get_live_customer_data() -> pd.DataFrame:
    """
    Downloads live_customer_list.parquet from R2 on demand,
    caching the DataFrame in memory for CACHE_TTL seconds to optimize performance.
    Falls back to the local copy if R2 download fails.
    """
    global _cached_df, _last_fetch_time, _r2_last_modified_time
    current_time = time.time()
    
    # Return cache if valid
    if _cached_df is not None and (current_time - _last_fetch_time) < CACHE_TTL:
        return _cached_df
        
    local_path = os.path.join("data", "processed", "1_live", "live_customer_list.parquet")
    
    # Try downloading from Cloudflare R2
    try:
        print(f"[Live Customer Service] Downloading {FILE_KEY} from R2...")
        
        # Ensure local directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        s3 = boto3.client(
            service_name='s3',
            endpoint_url=f'https://{ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY
        )
        
        # Download file to local path
        s3.download_file(BUCKET_NAME, FILE_KEY, local_path)
        print(f"[Live Customer Service] Downloaded successfully to {local_path}.")
        
        # Get metadata to determine R2 last modified time
        try:
            metadata = s3.head_object(Bucket=BUCKET_NAME, Key=FILE_KEY)
            from datetime import timezone, timedelta
            IST = timezone(timedelta(hours=5, minutes=30))
            _r2_last_modified_time = metadata['LastModified'].astimezone(IST)
        except Exception as me:
            print(f"[Live Customer Service] Failed to get R2 metadata: {me}")
            
    except Exception as e:
        print(f"[Live Customer Service] Failed to download from R2: {e}. Checking local fallback...")

    # Load from the local path (whether downloaded or pre-existing fallback)
    if os.path.exists(local_path):
        try:
            df = pd.read_parquet(local_path)
            
            # Basic validation
            if df.empty:
                print("[Live Customer Service] Warning: Loaded Parquet is empty.")
            
            # Fallback to local file modified time if R2 head failed
            if _r2_last_modified_time is None:
                from datetime import datetime, timezone, timedelta
                IST = timezone(timedelta(hours=5, minutes=30))
                mtime = os.path.getmtime(local_path)
                _r2_last_modified_time = datetime.fromtimestamp(mtime, tz=IST)
                
            _cached_df = df
            _last_fetch_time = current_time
            print(f"[Live Customer Service] Cache updated. Total rows: {len(df):,}")
            return df
        except Exception as le:
            print(f"[Live Customer Service] Error reading Parquet file: {le}")
            
    # Return empty fallback if all fails
    print("[Live Customer Service] Error: No data source available.")
    return pd.DataFrame(columns=["Location Code", "Location Name", "Customer Code"])
