import os
import boto3
import pandas as pd
import threading
from backend.services.activity_logger import r2_lock

ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "").strip()
ACCESS_KEY = os.getenv("R2_ACCESS_KEY", "").strip()
SECRET_KEY = os.getenv("R2_SECRET_KEY", "").strip()
BUCKET_NAME = "orient-analytics-snapshots"
FILE_KEY = "user_access.parquet"

def get_r2_client():
    return boto3.client(
        service_name='s3',
        endpoint_url=f'https://{ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )

def change_password(email, current_password, new_password):
    """
    Verifies the current password for the given email, updates it to the new password,
    saves the changes to the local parquet file, and uploads the updated parquet file to Cloudflare R2.
    Also updates the in-memory user_access_df cache.
    """
    local_path = "snapshot/user_access.parquet"
    client = get_r2_client()

    with r2_lock:
        # 1. Download the latest user_access.parquet from R2 to get concurrent updates
        try:
            client.download_file(BUCKET_NAME, FILE_KEY, local_path)
            df = pd.read_parquet(local_path)
        except Exception as e:
            print(f"Failed to download user_access.parquet from R2: {e}")
            # Fallback to local copy if download fails
            if os.path.exists(local_path):
                df = pd.read_parquet(local_path)
            else:
                return False, "User database not found."

        # 2. Check if the user email exists and the current password is correct
        user_row = df[(df['email'] == email) & (df['password'] == current_password)]
        if user_row.empty:
            return False, "Incorrect current password."

        # 3. Update the password in the DataFrame
        df.loc[df['email'] == email, 'password'] = new_password

        # 3.5. Update the password in PostgreSQL database automatically if engine is configured
        from database.connections.postgres_connection import engine
        from sqlalchemy import text
        if engine is not None:
            try:
                with engine.begin() as conn:
                    conn.execute(
                        text("UPDATE user_access SET password = :password WHERE email = :email"),
                        {"password": new_password, "email": email}
                    )
                print("PostgreSQL user_access table updated successfully.")
            except Exception as e:
                print(f"Warning: Failed to update password in PostgreSQL: {e}")
        else:
            print("Warning: PostgreSQL engine not initialized. Skipping database password synchronization.")

        # 4. Save locally and upload to R2
        try:
            df.to_parquet(local_path, index=False)
            client.upload_file(local_path, BUCKET_NAME, FILE_KEY)
        except Exception as e:
            print(f"Failed to upload updated user_access.parquet to R2: {e}")
            return False, "Failed to save password change to R2."

        # 5. Update the in-memory cache in backend.cache.data_cache in place
        import backend.cache.data_cache as cache
        cache.user_access_df.loc[cache.user_access_df['email'] == email, 'password'] = new_password
        
        return True, "Password updated successfully."
