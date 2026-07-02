import os
import sys
import subprocess

class PipelineService:
    """
    Service to run the existing downstream Python ETL pipeline scripts
    (Jupyter notebook processing & SQL database loading).
    """
    def __init__(self) -> None:
        self.project_root = r"c:\Projects\orient_analytics_platform"

    def run_raw_to_processed_pipeline(self) -> bool:
        """
        Runs the python script `notebooks/run_raw_to_processed.py` to process Excel files.
        """
        script_path = os.path.join(self.project_root, "notebooks", "run_raw_to_processed.py")
        print(f"[Pipeline Service] Triggering notebook pipeline: {script_path}...")
        
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                cwd=os.path.dirname(script_path),
                capture_output=True,
                text=True,
                check=True
            )
            print("[Pipeline Service] Notebook processed raw data successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[Pipeline Service] Error in notebook processing pipeline: {e.stderr}")
            return False

    def run_sql_load_pipeline(self) -> bool:
        """
        Runs the python script `etl/load/run_all_loads.py` to write processed data into PostgreSQL.
        """
        script_path = os.path.join(self.project_root, "etl", "load", "run_all_loads.py")
        print(f"[Pipeline Service] Triggering DB SQL loading: {script_path}...")
        
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                cwd=os.path.dirname(script_path),
                capture_output=True,
                text=True,
                check=True
            )
            print("[Pipeline Service] SQL load scripts executed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[Pipeline Service] Error in SQL loading pipeline: {e.stderr}")
            return False

    def trigger_full_etl(self) -> bool:
        """
        Triggers both notebook conversion and database load scripts sequentially.
        """
        success = self.run_raw_to_processed_pipeline()
        if success:
            success = self.run_sql_load_pipeline()
        return success
