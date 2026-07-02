import os
import time
import boto3
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from backend.services.rls import get_allowed_locations

load_dotenv()

# R2 Configuration using environment variables or fallback values
ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "").strip()
ACCESS_KEY = os.getenv("R2_ACCESS_KEY", "").strip()
SECRET_KEY = os.getenv("R2_SECRET_KEY", "").strip()
BUCKET_NAME = "orient-analytics-snapshots"
FILE_KEY = "live_posted_estimate.parquet"

# In-memory cache variables for pre-filtered today's sales
import threading

_cached_today_df = None
_last_fetch_time = 0.0
_r2_last_modified_time = None
CACHE_TTL = 15.0  # seconds - short TTL for live updates

_download_lock = threading.Lock()
_is_downloading = False

def get_last_sync_time() -> str:
    """
    Returns the last modified time of the parquet file on R2 in IST.
    """
    global _r2_last_modified_time
    if _r2_last_modified_time is not None:
        return _r2_last_modified_time.strftime("%I:%M:%S %p")
    return "--:--:--"


def get_live_posted_estimate_data() -> pd.DataFrame:
    """
    Downloads live_posted_estimate.parquet from R2 if needed and returns the raw DataFrame.
    (Kept for compatibility).
    """
    local_path = os.path.join("data", "processed", "1_live", "live_posted_estimate.parquet")
    if os.path.exists(local_path):
        try:
            return pd.read_parquet(local_path)
        except Exception:
            pass
    return pd.DataFrame()


def _load_and_cache_today_data():
    """
    Downloads the parquet file from R2, reads it, processes date conversions,
    filters for today's date in IST, and caches the result.
    Runs once every CACHE_TTL seconds.
    """
    global _cached_today_df, _last_fetch_time
    current_time = time.time()
    
    local_path = os.path.join("data", "processed", "1_live", "live_posted_estimate.parquet")
    
    # Try downloading from Cloudflare R2
    try:
        print(f"[Live Sales Service] Downloading {FILE_KEY} from R2...")
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        s3 = boto3.client(
            service_name='s3',
            endpoint_url=f'https://{ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY
        )
        s3.download_file(BUCKET_NAME, FILE_KEY, local_path)
        print(f"[Live Sales Service] Downloaded successfully to {local_path}.")
        
        # Get metadata to determine R2 last modified time
        try:
            metadata = s3.head_object(Bucket=BUCKET_NAME, Key=FILE_KEY)
            IST = timezone(timedelta(hours=5, minutes=30))
            global _r2_last_modified_time
            _r2_last_modified_time = metadata['LastModified'].astimezone(IST)
        except Exception as me:
            print(f"[Live Sales Service] Failed to get R2 metadata: {me}")
            
    except Exception as e:
        print(f"[Live Sales Service] Failed to download from R2: {e}. Checking local fallback...")

    # Load and pre-filter for today
    if os.path.exists(local_path):
        try:
            df = pd.read_parquet(local_path)
            if not df.empty:
                # 1. Convert Date column once
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                
                # 2. Filter for today's date in IST once
                IST = timezone(timedelta(hours=5, minutes=30))
                today_ist = datetime.now(IST).date()
                
                # Fallback to local file mtime if R2 metadata failed
                if _r2_last_modified_time is None:
                    mtime = os.path.getmtime(local_path)
                    _r2_last_modified_time = datetime.fromtimestamp(mtime, tz=IST)
                
                df_today = df[df['Date'] == today_ist].copy()
                
                _cached_today_df = df_today
                _last_fetch_time = current_time
                print(f"[Live Sales Service] Pre-filtered today's sales. Rows: {len(df_today)}")
                return
        except Exception as le:
            print(f"[Live Sales Service] Error parsing Parquet file: {le}")

    # Set fallback empty DataFrame if all fails
    _cached_today_df = pd.DataFrame(columns=[
        "Document_No", "Customer_Code", "Date", "Location", "Location_Name", "Final_Amount_to_Customer", "SystemCreatedAt"
    ])
    _last_fetch_time = current_time


def _download_in_background():
    """
    Background worker thread to pull updates from R2 and refresh the cached today's sales DataFrame.
    """
    global _cached_today_df, _last_fetch_time, _is_downloading
    with _download_lock:
        local_path = os.path.join("data", "processed", "1_live", "live_posted_estimate.parquet")
        try:
            print(f"[Live Sales Service] Background downloading {FILE_KEY} from R2...")
            s3 = boto3.client(
                service_name='s3',
                endpoint_url=f'https://{ACCOUNT_ID}.r2.cloudflarestorage.com',
                aws_access_key_id=ACCESS_KEY,
                aws_secret_access_key=SECRET_KEY
            )
            s3.download_file(BUCKET_NAME, FILE_KEY, local_path)
            print(f"[Live Sales Service] Background download completed successfully.")
            
            # Get metadata to determine R2 last modified time
            try:
                metadata = s3.head_object(Bucket=BUCKET_NAME, Key=FILE_KEY)
                IST = timezone(timedelta(hours=5, minutes=30))
                global _r2_last_modified_time
                _r2_last_modified_time = metadata['LastModified'].astimezone(IST)
            except Exception as me:
                print(f"[Live Sales Service] Failed to get R2 metadata in background: {me}")
                
        except Exception as e:
            print(f"[Live Sales Service] Background download failed: {e}")
            
        if os.path.exists(local_path):
            try:
                df = pd.read_parquet(local_path)
                if not df.empty:
                    df['Date'] = pd.to_datetime(df['Date']).dt.date
                    IST = timezone(timedelta(hours=5, minutes=30))
                    today_ist = datetime.now(IST).date()
                    
                    # Fallback to local file mtime if R2 metadata failed
                    if _r2_last_modified_time is None:
                        mtime = os.path.getmtime(local_path)
                        _r2_last_modified_time = datetime.fromtimestamp(mtime, tz=IST)
                        
                    df_today = df[df['Date'] == today_ist].copy()
                    _cached_today_df = df_today
                    _last_fetch_time = time.time()
                    print(f"[Live Sales Service] Background cache updated. Rows: {len(df_today)}")
            except Exception as ex:
                print(f"[Live Sales Service] Error parsing background parquet: {ex}")
        _is_downloading = False


def get_today_live_sales_data() -> pd.DataFrame:
    """
    Retrieves the pre-filtered today's sales data, applying only user-level RLS filters.
    Extremely fast, executing in sub-milliseconds since it bypasses raw date parsing.
    Fetches updates in a non-blocking background thread when cache TTL expires.
    """
    global _cached_today_df, _last_fetch_time, _is_downloading
    current_time = time.time()
    
    # 1. Sync load on first access (to prevent empty start)
    if _cached_today_df is None:
        _load_and_cache_today_data()
    # 2. Expired cache triggers a non-blocking background thread update
    elif (current_time - _last_fetch_time) > CACHE_TTL and not _is_downloading:
        _is_downloading = True
        thread = threading.Thread(target=_download_in_background)
        thread.daemon = True
        thread.start()
        
    df_today = _cached_today_df.copy()
    if df_today.empty:
        return df_today
        
    # Apply user allowed locations filter (RLS)
    allowed_locations = get_allowed_locations()
    if 'ALL' not in allowed_locations:
        df_today['Location_Name'] = df_today['Location_Name'].fillna("UNKNOWN").astype(str).str.strip().str.upper()
        allowed_clean = [loc.upper().strip() for loc in allowed_locations]
        df_today = df_today[df_today['Location_Name'].isin(allowed_clean)]
        
    return df_today
