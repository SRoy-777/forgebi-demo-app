import os
import re
import boto3
import pandas as pd
from datetime import datetime
from backend.cache.data_cache import user_access_df, rm_zm_df
from backend.services.admin_hub.dashboard_catalog_service import generate_catalog_data

# R2 Configuration
ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "").strip()
ACCESS_KEY = os.getenv("R2_ACCESS_KEY", "").strip()
SECRET_KEY = os.getenv("R2_SECRET_KEY", "").strip()
BUCKET_NAME = "orient-analytics-snapshots"
FILE_KEY = "user_access.parquet"
LOCAL_PARQUET_PATH = "snapshot/user_access.parquet"
LOCAL_CSV_PATH = "data/processed/user_access.csv"

def download_production_user_access():
    os.makedirs(os.path.dirname(LOCAL_PARQUET_PATH), exist_ok=True)
    s3 = boto3.client(
        service_name='s3',
        endpoint_url=f'https://{ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )
    s3.download_file(BUCKET_NAME, FILE_KEY, LOCAL_PARQUET_PATH)
    df = pd.read_parquet(LOCAL_PARQUET_PATH)
    df = df.fillna('')
    
    # Auto-migrate legacy dashboard IDs (e.g. roas-conversion -> roas-conversion-analytics)
    if 'dashboards' in df.columns:
        df['dashboards'] = df['dashboards'].apply(lambda x: ",".join(sorted(list(set(
            ['roas-conversion-analytics' if d.strip() == 'roas-conversion' else d.strip()
             for d in str(x).split(',') if d.strip()]
        )))))
    return df

def save_and_sync_production_user_access(df):
    # 1. Clean columns
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    
    # 2. Save locally
    os.makedirs(os.path.dirname(LOCAL_PARQUET_PATH), exist_ok=True)
    df.to_parquet(LOCAL_PARQUET_PATH, engine='pyarrow', compression='snappy', index=False)
    
    os.makedirs(os.path.dirname(LOCAL_CSV_PATH), exist_ok=True)
    df.to_csv(LOCAL_CSV_PATH, index=False)
    
    # 3. Upload to R2
    s3 = boto3.client(
        service_name='s3',
        endpoint_url=f'https://{ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY
    )
    s3.upload_file(LOCAL_PARQUET_PATH, BUCKET_NAME, FILE_KEY)
    
    # 4. Sync with local Postgres
    from sqlalchemy import create_engine
    import urllib.parse
    
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "orient_analytics")
    
    escaped_password = urllib.parse.quote_plus(DB_PASSWORD)
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{escaped_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        engine = create_engine(DATABASE_URL)
        df.to_sql(name="user_access", con=engine, if_exists="replace", index=False)
        print("PostgreSQL sync successful.")
    except Exception as e:
        print(f"PostgreSQL sync failed: {e}")
        
    # 5. Sync in-memory cache so newly added/modified users can log in immediately
    try:
        import backend.cache.data_cache as cache
        cache.user_access_df = df.copy()
        print("In-memory cache sync successful.")
    except Exception as e:
        print(f"In-memory cache sync failed: {e}")

def log_audit(logged_in_user, action, target_user):
    local_path = "data/processed/user_access_audit_log.csv"
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_row = pd.DataFrame([{
        "Timestamp": timestamp,
        "Logged In User": logged_in_user or "System",
        "Action": action,
        "Target User": target_user
    }])
    
    if os.path.exists(local_path):
        try:
            df = pd.read_csv(local_path)
            df = pd.concat([df, new_row], ignore_index=True)
        except Exception:
            df = new_row
    else:
        df = new_row
        
    df.to_csv(local_path, index=False)
    
    try:
        s3 = boto3.client(
            service_name='s3',
            endpoint_url=f'https://{ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY
        )
        s3.upload_file(local_path, BUCKET_NAME, "user_access_audit_log.csv")
    except Exception as e:
        print(f"Error uploading audit log to R2: {e}")

def validate_user_data(df, db_opts, mod_opts, loc_opts):
    errors = []
    
    # 1. Blank emails check
    blank_emails = df[df['email'].str.strip() == '']
    if not blank_emails.empty:
        errors.append("Validation Error: Email addresses cannot be blank.")
        
    # 2. Duplicate emails check
    emails = df['email'].str.strip().str.lower()
    if emails.duplicated().any():
        duplicated_list = df[emails.duplicated()]['email'].tolist()
        errors.append(f"Validation Error: Duplicate emails found: {', '.join(duplicated_list)}")
        
    # Get sets of valid IDs
    valid_dbs = {opt['value'] for opt in db_opts}
    valid_mods = {opt['value'] for opt in mod_opts}
    valid_locs = {opt['value'] for opt in loc_opts}
    
    # Dynamically inject existing production user access modules, dashboards, and locations into the valid sets
    try:
        prod_df = download_production_user_access()
        if not prod_df.empty:
            for _, row in prod_df.iterrows():
                for m in str(row.get('module', '')).split(','):
                    if m.strip():
                        valid_mods.add(m.strip())
                for d in str(row.get('dashboards', '')).split(','):
                    if d.strip():
                        valid_dbs.add(d.strip())
                for l in str(row.get('locations', '')).split(','):
                    if l.strip():
                        valid_locs.add(l.strip())
    except Exception as e:
        print(f"Warning in validation: could not load production user access for validation sets: {e}")
    
    # 3. Check dashboards, modules, and locations
    for _, row in df.iterrows():
        email = row['email']
        
        # Check dashboards
        dbs = [d.strip() for d in str(row.get('dashboards', '')).split(',') if d.strip()]
        invalid_dbs = [d for d in dbs if d not in valid_dbs]
        if invalid_dbs:
            errors.append(f"Validation Error for user '{email}': Invalid dashboard(s): {', '.join(invalid_dbs)}")
            
        # Check modules
        mods = [m.strip() for m in str(row.get('module', '')).split(',') if m.strip()]
        invalid_mods = [m for m in mods if m not in valid_mods]
        if invalid_mods:
            errors.append(f"Validation Error for user '{email}': Invalid module(s): {', '.join(invalid_mods)}")
            
        # Check locations
        locs = [l.strip() for l in str(row.get('locations', '')).split(',') if l.strip()]
        invalid_locs = [l for l in locs if l not in valid_locs and l != 'ALL']
        if invalid_locs:
            errors.append(f"Validation Error for user '{email}': Invalid location(s): {', '.join(invalid_locs)}")
            
    return errors

def load_initial_users():
    try:
        df = download_production_user_access()
        return df.to_dict('records')
    except Exception as e:
        print(f"Error downloading initial users from R2: {e}")
        df = user_access_df.copy()
        df = df.fillna('')
        return df.to_dict('records')

def get_location_options():
    locs = set(rm_zm_df['location'].dropna().unique().tolist())
    try:
        prod_df = download_production_user_access()
        if not prod_df.empty:
            for _, row in prod_df.iterrows():
                for l in str(row.get('locations', '')).split(','):
                    if l.strip() and l.strip() != 'ALL':
                        locs.add(l.strip())
    except Exception:
        pass
    options = [{'label': 'ALL (All Branches)', 'value': 'ALL'}] + [{'label': loc, 'value': loc} for loc in sorted(list(locs))]
    return options

def get_catalog_options():
    df_catalog = generate_catalog_data()
    
    db_opts_dict = {}
    for _, row in df_catalog.iterrows():
        db_opts_dict[row['Dashboard ID']] = row['Dashboard Name']
        
    modules_set = set()
    for mods in df_catalog['Module'].dropna().unique():
        for m in mods.split(','):
            modules_set.add(m.strip())
            
    try:
        prod_df = download_production_user_access()
        if not prod_df.empty:
            for _, row in prod_df.iterrows():
                for m in str(row.get('module', '')).split(','):
                    if m.strip():
                        modules_set.add(m.strip())
                for d in str(row.get('dashboards', '')).split(','):
                    if d.strip():
                        if d.strip() not in db_opts_dict:
                            label = " ".join([w.upper() if w.lower() in ('nsv', 'roas', 'it', 'hr') else w.capitalize() for w in d.strip().split('-')])
                            db_opts_dict[d.strip()] = label
    except Exception:
        pass
        
    db_options = [{'label': label, 'value': db_id} for db_id, label in sorted(db_opts_dict.items())]
    
    mod_options = []
    for mod in sorted(list(modules_set)):
        label = " ".join([w.upper() if w.lower() in ('nsv', 'roas', 'it', 'hr') else w.capitalize() for w in mod.split('-')])
        mod_options.append({
            'label': label,
            'value': mod
        })
        
    return db_options, mod_options



