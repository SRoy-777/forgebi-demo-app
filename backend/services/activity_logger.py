import os
import threading
import boto3
import pandas as pd
from datetime import datetime
from flask import request

# Lock to prevent concurrent R2 write conflicts
r2_lock = threading.Lock()

# R2 Config from environment variables or hardcoded fallback
ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "").strip()
ACCESS_KEY = os.getenv("R2_ACCESS_KEY", "").strip()
SECRET_KEY = os.getenv("R2_SECRET_KEY", "").strip()
BUCKET_NAME = "orient-analytics-snapshots"
FILE_KEY = "user_activity_log.csv"


def get_r2_client():
    return boto3.client(
        service_name='s3',
        endpoint_url=f'https://{ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )


def _log_activity_to_r2(email, dashboard_name, ip_address, action="Page View", filters=None):
    with r2_lock:
        local_path = "user_activity_log.csv"
        client = get_r2_client()

        # 1. Download existing log from R2
        try:
            client.download_file(BUCKET_NAME, FILE_KEY, local_path)
            df = pd.read_csv(local_path)
        except Exception:
            # File doesn't exist on R2 yet, create a new one
            df = pd.DataFrame(columns=["user_email", "dashboard_name", "opened_at", "ip_address", "action", "filters"])

        # Ensure new columns exist in df if not present
        if "action" not in df.columns:
            df["action"] = "Page View"
        if "filters" not in df.columns:
            df["filters"] = ""

        # 2. Append new row
        from datetime import timezone, timedelta
        ist_time = datetime.now(timezone(timedelta(hours=5, minutes=30)))
        new_row = pd.DataFrame([{
            "user_email": email,
            "dashboard_name": dashboard_name,
            "opened_at": ist_time.strftime("%Y-%m-%d %H:%M:%S"),
            "ip_address": ip_address,
            "action": action,
            "filters": str(filters) if filters is not None else ""
        }])
        df = pd.concat([df, new_row], ignore_index=True)

        # 3. Save locally and upload back to R2
        try:
            df.to_csv(local_path, index=False)
            client.upload_file(local_path, BUCKET_NAME, FILE_KEY)
        except Exception as e:
            print(f"Error writing/uploading logs: {e}")


def log_activity(email, dashboard_name, action="Page View", filters=None):
    if not email:
        return

    # Extract client IP address safely from Flask request
    try:
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
    except Exception:
        ip_address = 'Unknown'

    # Run R2 write/upload in a background thread to prevent UI blocking
    thread = threading.Thread(
        target=_log_activity_to_r2,
        args=(email, dashboard_name, ip_address, action, filters)
    )
    thread.daemon = True
    thread.start()
