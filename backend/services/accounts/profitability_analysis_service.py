import os
import re
import pandas as pd
from sqlalchemy import text
from backend.services.rls import get_allowed_locations
from backend.cache.data_cache import rm_zm_df

# Cache the raw dataframe in memory after loading once to speed up dashboard interactive runs
_cached_df = None

def load_data():
    global _cached_df
    if _cached_df is not None:
        return _cached_df.copy()

    # Locate the parquet file path relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parquet_path = os.path.abspath(
        os.path.join(script_dir, "../../../snapshot/consolidated_pl.parquet")
    )

    if not os.path.exists(parquet_path):
        print(f"Warning: {parquet_path} does not exist yet. Returning empty DataFrame.")
        return pd.DataFrame()

    df = pd.read_parquet(parquet_path)

    # ---------------------------------------------------
    # Parse Location and Code
    # ---------------------------------------------------
    # Examples: 'ALIPURDUAR  107' -> Location: 'ALIPURDUAR', Code: '107'
    #           'KOLKATA - ELGIN CORPORATE OFFI' -> Location: 'KOLKATA - ELGIN CORPORATE OFFI', Code: 'Office'
    #           'Total' -> Location: 'Total', Code: 'Total'
    def parse_location_and_code(loc_str):
        loc_str = str(loc_str).strip()
        
        # Exclude total rows in raw Excel if any
        if loc_str.upper() == 'TOTAL':
            return 'Total', 'Total'

        # Check if it represents a corporate office (contains "OFFICE", "OFFI", or "OFF")
        if 'OFF' in loc_str.upper() or 'ELGIN' in loc_str.upper():
            # If it has a trailing number, strip it to get the clean location name
            match = re.search(r'(.*?)\s+(\d+)$', loc_str)
            if match:
                name = match.group(1).strip()
            else:
                name = loc_str
            return name, 'Office'

        # Parse trailing digits as branch code for regular branches
        match = re.search(r'(.*?)\s+(\d+)$', loc_str)
        if match:
            name = match.group(1).strip()
            code = match.group(2).strip()
            return name, code

        return loc_str, 'N/A'

    parsed = df['location'].apply(parse_location_and_code)
    df['location_name'] = [p[0] for p in parsed]
    df['code'] = [p[1] for p in parsed]

    # Rule 1: Exclude Code = 'N/A' completely
    df = df[df['code'] != 'N/A']
    df = df[df['location_name'].str.upper() != 'TOTAL']

    # Keep cached copy
    _cached_df = df
    return _cached_df.copy()


def get_available_months():
    df = load_data()
    if df.empty or 'month_year' not in df.columns:
        return []
    
    unique_months = df['month_year'].dropna().unique().tolist()
    # Sort chronologically by converting to datetime
    try:
        sorted_months = sorted(
            unique_months,
            key=lambda m: pd.to_datetime(m, format='%b-%Y')
        )
        return sorted_months
    except Exception:
        return sorted(unique_months)


def _apply_rm_zm_location_filters(df, location_col, locations=None, rms=None, zms=None):
    rz = rm_zm_df.copy()
    rz['location'] = rz['location'].astype(str).str.strip().str.upper()
    rz['rm'] = rz['rm'].astype(str).str.strip().str.upper()
    rz['zm'] = rz['zm'].astype(str).str.strip().str.upper()
    
    df[location_col] = df[location_col].astype(str).str.strip().str.upper()
    
    if rms:
        rms = [str(i).strip().upper() for i in rms]
        rm_locations = rz[rz['rm'].isin(rms)]['location'].unique()
        df = df[df[location_col].isin(rm_locations)]
        
    if zms:
        zms = [str(i).strip().upper() for i in zms]
        zm_locations = rz[rz['zm'].isin(zms)]['location'].unique()
        df = df[df[location_col].isin(zm_locations)]
        
    if locations:
        locations = [str(i).strip().upper() for i in locations]
        df = df[df[location_col].isin(locations)]
        
    return df


def get_filtered_data(selected_months=None, locations=None, rms=None, zms=None):
    df = load_data()
    if df.empty:
        return df

    # Apply Session RLS
    allowed_locations = get_allowed_locations()
    if allowed_locations and 'ALL' not in allowed_locations:
        allowed_upper = [l.upper().strip() for l in allowed_locations]
        df = df[df['location_name'].str.upper().str.strip().isin(allowed_upper)]

    # Apply Dropdown Search Filters (RM/ZM/Location)
    df = _apply_rm_zm_location_filters(df, 'location_name', locations, rms, zms)

    # Apply Month selection filter
    if selected_months:
        df = df[df['month_year'].isin(selected_months)]

    return df


# Columns mapping dictionary
METRICS_MAP = {
    'Total Sales': 'total_sales',
    'Profit Before Tax': 'profit_before_tax',
    'GP': 'gp',
    'GP Ratio': 'gp_ratio',
    'PBT / Sales Ratio': 'pbt_sales_ratio',
    'Profit / Employee (Rs.)': 'profit_employee',
    'Employees': 'employees',
    'Profit / Sq Ft Area (Rs.)': 'profit_sq_ft',
    'Area In Sq Ft': 'area_in_sq_ft'
}


def calculate_metrics(agg_df):
    """
    Computes formulas based on business requirements.
    agg_df must contain the columns:
    - manufactured_goods_in_house_sales
    - job_work_goods_sales
    - raw_material_purchased
    - employee_cost
    - finance_cost
    - depreciation
    - other_expenses
    - csr_expenses
    - employee_count
    - sq_ft
    """
    # Total Sales = Manufactured Goods + Job Work Goods
    agg_df['total_sales'] = (
        agg_df['manufactured_goods_in_house_sales'] +
        agg_df['job_work_goods_sales']
    )
    
    # GP = Total Sales - Raw Material Purchased
    agg_df['gp'] = agg_df['total_sales'] - agg_df['raw_material_purchased']
    
    # GP Ratio = GP / Total Sales (as %)
    agg_df['gp_ratio'] = agg_df.apply(
        lambda r: (r['gp'] / r['total_sales'] * 100) if r['total_sales'] else 0.0,
        axis=1
    )
    
    # PBT = Total Sales - (Raw Material + Employee Cost + Finance Cost + Depreciation + Other Expenses + CSR Expenses)
    agg_df['profit_before_tax'] = agg_df['total_sales'] - (
        agg_df['raw_material_purchased'] +
        agg_df['employee_cost'] +
        agg_df['finance_cost'] +
        agg_df['depreciation'] +
        agg_df['other_expenses'] +
        agg_df['csr_expenses']
    )
    
    # PBT Ratio = PBT / Total Sales (as %)
    agg_df['pbt_sales_ratio'] = agg_df.apply(
        lambda r: (r['profit_before_tax'] / r['total_sales'] * 100) if r['total_sales'] else 0.0,
        axis=1
    )
    
    # Profit / Employee = PBT * 10 / employee_count
    agg_df['profit_employee'] = agg_df.apply(
        lambda r: (r['profit_before_tax'] * 10 / r['employee_count']) if r['employee_count'] else 0.0,
        axis=1
    )
    
    agg_df['employees'] = agg_df['employee_count']
    
    # Profit / Sq Ft = PBT * 10 / sq_ft
    agg_df['profit_sq_ft'] = agg_df.apply(
        lambda r: (r['profit_before_tax'] * 10 / r['sq_ft']) if r['sq_ft'] else 0.0,
        axis=1
    )
    
    agg_df['area_in_sq_ft'] = agg_df['sq_ft']
    
    # Apply Rule 2 for Code == "Office"
    office_mask = agg_df['code'] == 'Office'
    cols_to_null = [
        'gp', 'gp_ratio', 'pbt_sales_ratio',
        'profit_employee', 'profit_sq_ft', 'area_in_sq_ft'
    ]
    for col in cols_to_null:
        agg_df.loc[office_mask, col] = None
        
    return agg_df


def get_profitability_report(selected_months, mode="Consolidate", selected_metrics=None, locations=None, rms=None, zms=None):
    """
    Computes and formats the report depending on Consolidate vs Compare mode.
    """
    df = get_filtered_data(selected_months, locations, rms, zms)
    
    if df.empty:
        return pd.DataFrame(), []

    if selected_metrics is None:
        selected_metrics = list(METRICS_MAP.keys())

    # Map selected metrics to key column ids
    active_metric_ids = [METRICS_MAP[m] for m in selected_metrics if m in METRICS_MAP]

    # Convert numeric fields to numeric
    numeric_cols = [
        'manufactured_goods_in_house_sales', 'job_work_goods_sales',
        'raw_material_purchased', 'employee_cost', 'finance_cost',
        'depreciation', 'other_expenses', 'csr_expenses',
        'employee_count', 'sq_ft'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # Group and aggregate
    if mode == "Consolidate":
        # Aggregate all months
        agg_df = df.groupby(['code', 'location_name'], as_index=False).agg({
            'manufactured_goods_in_house_sales': 'sum',
            'job_work_goods_sales': 'sum',
            'raw_material_purchased': 'sum',
            'employee_cost': 'sum',
            'finance_cost': 'sum',
            'depreciation': 'sum',
            'other_expenses': 'sum',
            'csr_expenses': 'sum',
            'employee_count': 'mean', # State variable averaged over selected period
            'sq_ft': 'mean'           # State variable averaged over selected period
        })

        # Calculate metrics & ratios
        agg_df = calculate_metrics(agg_df)

        # Prepare final output structure
        cols_to_keep = ['code', 'location_name'] + active_metric_ids
        report_df = agg_df[cols_to_keep].copy()

        # Rename to clean labels
        # Header formatting (e.g. Apr-2025 to Mar-2026)
        if selected_months:
            selected_dts = pd.to_datetime(selected_months, format='%b-%Y')
            min_dt = selected_dts.min()
            max_dt = selected_dts.max()
            if min_dt == max_dt:
                period_label = min_dt.strftime('%b-%Y')
            else:
                period_label = f"{min_dt.strftime('%b-%Y')} to {max_dt.strftime('%b-%Y')}"
        else:
            period_label = "Period"

        # Format column headers for Consolidate Mode
        # Columns in Consolidated mode are named like: "Total Sales (Apr-2025 to Mar-2026)" or simply just the metric name, 
        # but the prompt says: "if a user selects Consolidate then all the months selected will consolidate themselves and over the columns will be written the Month Periods (eg, Apr-2025 to Mar-2026)"
        # So we write headers as: "Total Sales (Apr-2025 to Mar-2026)"
        datatable_columns = [
            {'name': 'Code', 'id': 'code'},
            {'name': 'Location', 'id': 'location_name'}
        ]
        
        # Build rename mapping
        rename_map = {'code': 'code', 'location_name': 'location_name'}
        for metric_label, m_id in METRICS_MAP.items():
            if m_id in active_metric_ids:
                col_header = f"{metric_label} ({period_label})"
                datatable_columns.append({'name': col_header, 'id': col_header})
                rename_map[m_id] = col_header

        report_df = report_df.rename(columns=rename_map)

        # Consolidate all Code == 'Office' rows into a single summary row at the very end
        non_office_df = report_df[report_df['code'] != 'Office']
        office_df = report_df[report_df['code'] == 'Office']
        
        if not office_df.empty:
            office_row = {'code': 'Office', 'location_name': 'Other Office'}
            for col in report_df.columns:
                if col in ['code', 'location_name']:
                    continue
                # Sum the Sales, PBT, and Employees columns, keep other metrics blank
                col_lower = col.lower()
                if any(m in col_lower for m in ['total sales', 'profit before tax', 'employees']):
                    office_row[col] = office_df[col].sum()
                else:
                    office_row[col] = None
            office_summary_df = pd.DataFrame([office_row])
        else:
            office_summary_df = pd.DataFrame(columns=report_df.columns)
            
        report_df = pd.concat([non_office_df, office_summary_df], ignore_index=True)

        return report_df, datatable_columns

    else:
        # COMPARE MODE: columns generated dynamically side-by-side grouped by metric
        # Find unique keys
        unique_keys = df[['code', 'location_name']].drop_duplicates().sort_values('location_name').values.tolist()
        base_df = pd.DataFrame(unique_keys, columns=['code', 'location_name'])

        sorted_months = sorted(
            list(df['month_year'].dropna().unique()),
            key=lambda m: pd.to_datetime(m, format='%b-%Y')
        )

        datatable_columns = [
            {'name': 'Code', 'id': 'code'},
            {'name': 'Location', 'id': 'location_name'}
        ]

        # Loop through each selected metric first, then month
        for metric_label in selected_metrics:
            m_id = METRICS_MAP[metric_label]
            for month in sorted_months:
                col_id = f"{m_id}_{month}"
                col_header = f"{metric_label} ({month})"
                datatable_columns.append({'name': col_header, 'id': col_id})

                # Calculate metrics for this specific month
                month_df = df[df['month_year'] == month].copy()
                month_df = calculate_metrics(month_df)

                # Merge back to base_df
                temp_merged = base_df.merge(
                    month_df[['code', 'location_name', m_id]],
                    on=['code', 'location_name'],
                    how='left'
                )
                base_df[col_id] = temp_merged[m_id]

        # Consolidate all Code == 'Office' rows into a single summary row at the very end
        non_office_df = base_df[base_df['code'] != 'Office']
        office_df = base_df[base_df['code'] == 'Office']
        
        if not office_df.empty:
            office_row = {'code': 'Office', 'location_name': 'Other Office'}
            for col in base_df.columns:
                if col in ['code', 'location_name']:
                    continue
                # Sum the Sales, PBT, and Employees columns, keep other metrics blank
                if col.startswith('total_sales_') or col.startswith('profit_before_tax_') or col.startswith('employees_'):
                    office_row[col] = office_df[col].sum()
                else:
                    office_row[col] = None
            office_summary_df = pd.DataFrame([office_row])
        else:
            office_summary_df = pd.DataFrame(columns=base_df.columns)
            
        report_df = pd.concat([non_office_df, office_summary_df], ignore_index=True)

        return report_df, datatable_columns
