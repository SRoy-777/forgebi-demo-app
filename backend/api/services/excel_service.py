import os
import pandas as pd
from typing import List, Dict, Any

class ExcelService:
    """
    Service to map raw JSON records from Business Central OData responses
    to the identical column layout and headers as the manual raw Excel files.
    """
    def __init__(self) -> None:
        self.raw_dir = r"c:\Projects\orient_analytics_platform\data\raw"
        os.makedirs(self.raw_dir, exist_ok=True)

    def export_customers_to_excel(self, raw_customers: List[Dict[str, Any]], incremental: bool = False) -> str:
        """
        Saves Customer data exactly formatted as `Quick Customer List.xlsx`.
        If incremental is True, merges with existing file on 'Customer No.' to preserve history.
        """
        file_path = os.path.join(self.raw_dir, "Quick Customer List.xlsx")
        
        if not raw_customers:
            print("[Excel Service] No new customer records to export. Skipping file update.")
            return file_path
        
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
        
        # Enforce exact column order as raw sheet
        columns_order = [
            "Phone No.", "Customer No.", "Name", "Email", "Whatsapp No.", "Father Name",
            "P.A.N. No.", "Birth Date", "Anniversary Date", "Aadhar No.", "Passport No.",
            "Driving License", "Voter ID", "IsKYC", "KYC Document Type", "KYC Document No.",
            "Address", "Address 2", "City", "Post Code", "Village", "District", "State Code", "Location Code"
        ]
        df_new = df_new[columns_order]

        # Merge with existing file if incremental=True
        if incremental and os.path.exists(file_path):
            print("[Excel Service] Incremental sync requested. Merging new records with existing file...")
            try:
                df_old = pd.read_excel(
                    file_path,
                    dtype={"Phone No.": str, "Customer No.": str}
                )
                
                # Standardize columns of df_old just in case of mismatch
                for col in columns_order:
                    if col not in df_old.columns:
                        df_old[col] = ""
                df_old = df_old[columns_order]
                
                # Explicitly remove records from the old dataset that are present in the new 3-day sync
                df_old = df_old[~df_old["Customer No."].isin(df_new["Customer No."])]
                
                # Concatenate the new records with the remaining old records
                df_combined = pd.concat([df_new, df_old], ignore_index=True)
                df_new = df_combined
                print(f"[Excel Service] Merged successfully. Total records: {len(df_new)}")
            except Exception as e:
                print(f"[Excel Service] Warning: Failed to read existing Excel file: {e}. Writing only new records.")

        print(f"[Excel Service] Writing {len(df_new)} records to: {file_path}")
        df_new.to_excel(file_path, index=False)
        print("[Excel Service] Quick Customer List.xlsx updated.")
        return file_path

    def export_tags_to_excel(self, raw_tags: List[Dict[str, Any]]) -> str:
        """
        Saves Tag data exactly formatted as `Tag List.xlsx`.
        """
        file_path = os.path.join(self.raw_dir, "Tag List.xlsx")
        
        if not raw_tags:
            print("[Excel Service] No tag records to export. Skipping file update.")
            return file_path
        
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
        
        # Enforce exact column order as raw sheet
        columns_order = [
            "Tag No.", "Tag Type", "Job ID", "Job Type", "Job Card Type", "Item ID", "Description",
            "Counter Code", "Purity", "NO OF PIECES", "Gross Weight", "NET Weight", "Fine Weight",
            "Diamond Weight", "Target Bin Code", "Invent Location ID", "Brand", "Certificate",
            "Certificate No.", "Collection Code", "Design Code", "Hallmarking", "HUID", "Bulk Tag",
            "Manual Tag", "MRP", "Ornament Category Code", "Ornament Size", "Other Charges Amount",
            "Parent Tag No", "Stone CT Value", "Stone Weight In GRM", "Tag Generated Date",
            "Tag Received Date", "Tag Status", "Certification Vendor", "Vendor Account", "Vendor Name",
            "Diamond PCS", "Stone CPCS", "Stone GPCS", "Section ID", "No Of Tag", "Stone Weight CT",
            "Ornament Sub Category Code", "Weight Range Code", "Tag SubStatus", "QC Status",
            "QC Date Time", "QC User ID", "QC Remark"
        ]
        df = df[columns_order]
        
        print(f"[Excel Service] Writing {len(df)} records to: {file_path}")
        df.to_excel(file_path, index=False)
        print("[Excel Service] Tag List.xlsx updated.")
        return file_path
