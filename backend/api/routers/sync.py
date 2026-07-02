from fastapi import APIRouter, HTTPException, BackgroundTasks
import pandas as pd
from sqlalchemy import create_engine, text
import os
from backend.api.clients.bc_client import BusinessCentralClient
from backend.api.services.excel_service import ExcelService
from backend.api.services.db_service import DBService
from backend.api.services.pipeline_service import PipelineService
from backend.api.config import settings

router = APIRouter(prefix="/api/sync", tags=["sync"])

bc_client = BusinessCentralClient()
excel_service = ExcelService()
db_service = DBService()
pipeline_service = PipelineService()
engine = create_engine(settings.database_url)

def _get_max_customer_id() -> str:
    """
    Finds the maximum customer number currently in the PostgreSQL database or the raw Excel sheet.
    """
    max_id = None
    
    # 1. Try reading from PostgreSQL
    try:
        with engine.connect() as conn:
            res = conn.execute(text('SELECT max("customer_no.") FROM customer_list')).fetchone()
            if res and res[0]:
                max_id = res[0]
    except Exception as e:
        print(f"[Sync Router] DB check for max customer ID failed/table not found: {e}")

    # 2. Try reading from raw Excel backup if DB check failed
    if not max_id:
        excel_path = os.path.join(r"c:\Projects\orient_analytics_platform\data\raw", "Quick Customer List.xlsx")
        if os.path.exists(excel_path):
            try:
                print(f"[Sync Router] Reading max Customer No. from Excel backup...")
                df_excel = pd.read_excel(excel_path, usecols=["Customer No."])
                max_id = df_excel["Customer No."].max()
            except Exception as e:
                print(f"[Sync Router] Excel check for max customer ID failed: {e}")

    # Default fallback if no data exists
    if not max_id:
        max_id = "CUS00000000"
        
    print(f"[Sync Router] Found max customer ID: {max_id}")
    return max_id


def _run_full_pipeline_task():
    """
    Background worker function to run raw Excel sync followed by notebook and load pipeline.
    """
    print("[Sync Router] Background full ETL process started.")
    try:
        # Get max ID for incremental customer sync
        max_cust_id = _get_max_customer_id()
        customer_params = {"$filter": f"customerNo gt '{max_cust_id}'"}

        # 1. Fetch raw data from BC APIs
        raw_customers = bc_client.get_all_records("ACXCustomerListAPIJRS", params=customer_params)
        raw_tags = bc_client.get_all_records("ACXTagHeadersAPIJRS")
        
        # 2. Write to raw Excel sheets (data/raw/) - incremental upsert for customers
        excel_service.export_customers_to_excel(raw_customers, incremental=True)
        excel_service.export_tags_to_excel(raw_tags)
        
        # 3. Trigger Notebook and SQL Load scripts
        success = pipeline_service.trigger_full_etl()
        if success:
            print("[Sync Router] Background full ETL process completed successfully.")
        else:
            print("[Sync Router] Background full ETL process failed in one of the pipeline steps.")
    except Exception as e:
        print(f"[Sync Router] Exception in background ETL: {e}")


@router.get("/excel")
def sync_to_excel():
    """
    Strictly READ-ONLY.
    Fetches raw customers (incremental - greater than max customer ID) & tags (full refresh) and updates Excel files in data/raw/.
    """
    try:
        # Get max ID for incremental customer sync
        max_cust_id = _get_max_customer_id()
        customer_params = {"$filter": f"customerNo gt '{max_cust_id}'"}

        # 1. Fetch raw data
        raw_customers = bc_client.get_all_records("ACXCustomerListAPIJRS", params=customer_params)
        raw_tags = bc_client.get_all_records("ACXTagHeadersAPIJRS")
        
        # 2. Export to Excel files (incremental upsert for customers)
        cust_path = excel_service.export_customers_to_excel(raw_customers, incremental=True)
        tags_path = excel_service.export_tags_to_excel(raw_tags)
        
        return {
            "status": "success",
            "message": "Raw Excel files generated successfully.",
            "synced_records": {
                "customers_incremental_new": len(raw_customers),
                "tags_full": len(raw_tags)
            },
            "output_paths": {
                "customers": cust_path,
                "tags": tags_path
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel sync failed: {str(e)}")


@router.get("/db")
def sync_to_db():
    """
    Strictly READ-ONLY extraction from BC.
    Fetches newly created customers and all tags, then syncs them directly into Postgres tables.
    Also updates Excel backups in data/raw/.
    """
    try:
        # Get max ID for incremental customer sync
        max_cust_id = _get_max_customer_id()
        customer_params = {"$filter": f"customerNo gt '{max_cust_id}'"}

        # 1. Fetch raw data
        raw_customers = bc_client.get_all_records("ACXCustomerListAPIJRS", params=customer_params)
        raw_tags = bc_client.get_all_records("ACXTagHeadersAPIJRS")
        
        # 2. Sync directly to PostgreSQL
        db_service.sync_customers_to_db(raw_customers, incremental=True)
        db_service.sync_tags_to_db(raw_tags)
        
        # 3. Save raw Excel files as audit logs / safety backups
        excel_service.export_customers_to_excel(raw_customers, incremental=True)
        excel_service.export_tags_to_excel(raw_tags)
        
        return {
            "status": "success",
            "message": "Database tables (customer_list & tag_list) synced directly from Business Central.",
            "synced_records": {
                "customers": len(raw_customers),
                "tags": len(raw_tags)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database sync failed: {str(e)}")


@router.get("/all")
def sync_all_etl(background_tasks: BackgroundTasks):
    """
    Trigger full automated ingestion:
    Pulls from BC -> Overwrites Excel files -> Triggers Jupyter Notebook -> Triggers SQL Database loads.
    Runs asynchronously in the background.
    """
    background_tasks.add_task(_run_full_pipeline_task)
    return {
        "status": "success",
        "message": "Full automated ETL pipeline sync has been scheduled in the background. Check logs for progress."
    }
