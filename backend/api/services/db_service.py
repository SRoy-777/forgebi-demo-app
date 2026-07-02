import pandas as pd
from sqlalchemy import create_engine, text
from typing import List, Dict, Any
from backend.api.config import settings

class DBService:
    """
    Service to normalize, clean, and upload Business Central OData
    directly to the shared PostgreSQL database tables: `tag_list` and `customer_list`.
    Ensures identical formatting to the manual load scripts.
    """
    def __init__(self) -> None:
        self.engine = create_engine(settings.database_url)

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies identical column standardization to the load scripts:
        strip, lowercase, and replace spaces with underscores.
        """
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
        return df

    def sync_customers_to_db(self, raw_customers: List[Dict[str, Any]], incremental: bool = False) -> None:
        """
        Uploads customer data to the PostgreSQL `customer_list` table,
        applying same type casting and cleanup as `load_customer.py`.
        If incremental is True, merges with existing database records.
        """
        if not raw_customers:
            print("[DB Service] No customer data received to upload.")
            return

        # Map BC fields to intermediate Excel Headers
        mapped_data = []
        for c in raw_customers:
            mapped_data.append({
                "Phone No.": str(c.get("phoneNo", "")) if c.get("phoneNo") is not None else "",
                "Customer No.": str(c.get("customerNo", "")) if c.get("customerNo") is not None else "",
                "Name": c.get("name", ""),
                "Email": c.get("eMail", ""),
                "Whatsapp No.": str(c.get("mobilePhoneNo", "")) if c.get("mobilePhoneNo") is not None else "",
                "Father Name": c.get("fatherName", ""),
                "P.A.N. No.": c.get("pANNo", ""),
                "Birth Date": c.get("birthDate"),
                "Anniversary Date": c.get("anniversaryDate"),
                "Aadhar No.": c.get("aadharNo", 0),
                "Passport No.": c.get("passportNo", ""),
                "Driving License": c.get("drivingLicense", ""),
                "Voter ID": c.get("voterID", ""),
                "IsKYC": 1 if c.get("isKYC") is True else 0,
                "KYC Document Type": c.get("kycDocumentType", " "),
                "KYC Document No.": c.get("kycDocumentNo", ""),
                "Address": c.get("address", ""),
                "Address 2": c.get("address2", ""),
                "City": c.get("city", ""),
                "Post Code": c.get("postCode", ""),
                "Village": c.get("village", ""),
                "District": c.get("district", ""),
                "State Code": c.get("stateCode", ""),
                "Location Code": c.get("locationCode", "")
            })

        df_new = pd.DataFrame(mapped_data)
        
        # Standardize headers to lowercase/underscores
        df_new = self._standardize_columns(df_new)

        # Mirror `load_customer.py` cleaning
        df_new['phone_no.'] = (
            df_new['phone_no.']
            .astype(str)
            .str.replace('.0', '', regex=False)
            .str.strip()
        )
        df_new['customer_no.'] = (
            df_new['customer_no.']
            .astype(str)
            .str.replace('.0', '', regex=False)
            .str.strip()
        )

        table_name = "customer_list"

        # Merge with existing database table if incremental=True
        if incremental:
            print("[DB Service] Incremental sync requested. Merging new records with existing SQL table...")
            try:
                # Query old records
                df_old = pd.read_sql(f"SELECT * FROM {table_name}", con=self.engine)
                
                # Align columns
                for col in df_new.columns:
                    if col not in df_old.columns:
                        df_old[col] = None
                df_old = df_old[df_new.columns]
                
                # Explicitly remove records from the old dataset that are present in the new 3-day sync
                df_old = df_old[~df_old["customer_no."].isin(df_new["customer_no."])]
                
                # Concatenate the new records with the remaining old records
                df_combined = pd.concat([df_new, df_old], ignore_index=True)
                df_new = df_combined
                print(f"[DB Service] Merged SQL records successfully. Total rows: {len(df_new)}")
            except Exception as e:
                print(f"[DB Service] Table '{table_name}' does not exist yet or failed to read: {e}. Creating new table.")

        print(f"[DB Service] Uploading {len(df_new)} records to PostgreSQL table: {table_name}...")
        
        df_new.to_sql(
            table_name,
            con=self.engine,
            if_exists="replace",
            index=False
        )
        print(f"[DB Service] Table '{table_name}' uploaded successfully.")

    def sync_tags_to_db(self, raw_tags: List[Dict[str, Any]]) -> None:
        """
        Uploads tag data to the PostgreSQL `tag_list` table,
        applying same type casting and cleanup as `load_tag.py`.
        """
        if not raw_tags:
            print("[DB Service] No tag data received to upload.")
            return

        # Map BC fields to intermediate Excel Headers
        mapped_data = []
        for t in raw_tags:
            mapped_data.append({
                "Tag No.": t.get("tagNo", ""),
                "Tag Type": t.get("tagType", ""),
                "Job ID": t.get("jobID", ""),
                "Job Type": t.get("jobTYPE", ""),
                "Job Card Type": t.get("jobCARDTYPE", ""),
                "Item ID": t.get("itemID", ""),
                "Description": t.get("description", ""),
                "Counter Code": t.get("counterCODE", ""),
                "Purity": t.get("purity", 0),
                "NO OF PIECES": t.get("noOFPIECES", 0),
                "Gross Weight": t.get("grossWEIGHT", 0.0),
                "NET Weight": t.get("netWEIGHT", 0.0),
                "Fine Weight": t.get("fineWEIGHT", 0.0),
                "Diamond Weight": t.get("diamondWEIGHT", 0.0),
                "Target Bin Code": t.get("targetBinCode", ""),
                "Invent Location ID": t.get("inventLOCATIONID", ""),
                "Brand": t.get("brand", ""),
                "Certificate": t.get("certificate", ""),
                "Certificate No.": t.get("certificateNO", ""),
                "Collection Code": t.get("collectionCODE", ""),
                "Design Code": t.get("designCODE", ""),
                "Hallmarking": t.get("hallmarking", ""),
                "HUID": t.get("hmhuID", ""),
                "Bulk Tag": t.get("bulkTAG", 0),
                "Manual Tag": t.get("manualTAGNo", ""),
                "MRP": t.get("mrp", 0.0),
                "Ornament Category Code": t.get("ornamentCATEGORYCODE", ""),
                "Ornament Size": t.get("ornamentSIZE", ""),
                "Other Charges Amount": t.get("otherCHARGESAMOUNT", 0.0),
                "Parent Tag No": t.get("parentTAGNO", ""),
                "Stone CT Value": t.get("orgStoneCTValue", 0.0),
                "Stone Weight In GRM": t.get("orgStoneGRMValue", 0.0),
                "Tag Generated Date": t.get("tagGENERATEDDATE"),
                "Tag Received Date": t.get("tagReceivedDate"),
                "Tag Status": t.get("tagSTATUS", ""),
                "Certification Vendor": t.get("certificationVendor", ""),
                "Vendor Account": t.get("vendACCOUNT", ""),
                "Vendor Name": t.get("vendNAME", ""),
                "Diamond PCS": t.get("diamondPCS", 0),
                "Stone CPCS": t.get("stoneCPCS", 0),
                "Stone GPCS": t.get("stoneGPCS", 0),
                "Section ID": t.get("sectionID", ""),
                "No Of Tag": t.get("noOFPIECES", 1),
                "Stone Weight CT": t.get("stoneWEIGHTCT", 0.0),
                "Ornament Sub Category Code": t.get("ornamentSUBCATEGORYCODE", ""),
                "Weight Range Code": t.get("weightRANGECODE", ""),
                "Tag SubStatus": t.get("tagSubStatus", ""),
                "QC Status": t.get("qc", ""),
                "QC Date Time": t.get("systemModifiedAt"),
                "QC User ID": t.get("systemModifiedBy"),
                "QC Remark": ""
            })

        df = pd.DataFrame(mapped_data)
        
        # Standardize headers to lowercase/underscores
        df = self._standardize_columns(df)

        # Mirror `load_tag.py` date column parsing
        date_cols = ['tag_generated_date', 'tag_received_date']
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')

        table_name = "tag_list"
        print(f"[DB Service] Uploading {len(df)} records to PostgreSQL table: {table_name}...")
        
        with self.engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))

        df.to_sql(
            table_name,
            self.engine,
            if_exists='replace',
            index=False,
            chunksize=10000,
            method='multi'
        )
        print(f"[DB Service] Table '{table_name}' uploaded successfully.")
