import os
import sys
import calendar
import pandas as pd
import numpy as np

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.cache.data_cache import (
    merged_sales_df,
    rm_zm_df,
    employee_performance_df,
    scheme_df,
    retail_sales_employee_list_df
)
from backend.services.rls import get_allowed_locations

def validate_dates(start_date, end_date):
    if start_date is None or end_date is None:
        return None, None
    try:
        start_date = pd.to_datetime(start_date).date()
        end_date = pd.to_datetime(end_date).date()
    except Exception:
        return None, None
    return start_date, end_date

def get_employee_performance_data(start_date, end_date, locations=None, rms=None, zms=None, employee_search=None):
    """
    Computes Employee Performance Dashboard Data:
    - Table containing targets, achievements, % diff and score (1-5) for each metric
    - KPI Layer 1 (Aggregated achievements)
    - KPI Layer 2 (Aggregated achievements vs targets)
    - KPI Layer 3 (Top 3 performing employees by Final Rank)
    """
    # 1. Date Conversion & Validation
    start_dt, end_dt = validate_dates(start_date, end_date)
    if start_dt is None or end_dt is None:
        return {
            'master_table': pd.DataFrame(),
            'kpis_layer1': {},
            'kpis_layer2': {},
            'top_3_employees': []
        }
    start_month_first = start_dt.replace(day=1)

    # 2. Copy Cached Dataframes and resolve employee location using the latest location overall
    df_ep = employee_performance_df.copy()
    df_ep['employee_code'] = df_ep['employee_code'].astype(str).str.strip().str.upper()
    df_ep = df_ep.sort_values(by='period')

    # Always keep the chronologically latest target record overall for each employee
    employee_df = df_ep.drop_duplicates(subset=['employee_code'], keep='last').copy()
    employee_df = employee_df[['location_code', 'location_name', 'employee_code', 'employee_name']].copy()

    # Merge job_title, date_joined, employment_status from retail_sales_employee_list
    emp_list_clean = retail_sales_employee_list_df[['employee_number', 'job_title', 'date_joined', 'employment_status']].copy()
    emp_list_clean['employee_number'] = emp_list_clean['employee_number'].astype(str).str.replace('.0', '', regex=False).str.strip().str.upper()

    employee_df = employee_df.merge(
        emp_list_clean,
        left_on='employee_code',
        right_on='employee_number',
        how='left'
    )
    employee_df.drop(columns=['employee_number'], inplace=True, errors='ignore')
    employee_df[['job_title', 'employment_status']] = employee_df[['job_title', 'employment_status']].fillna("")
    
    sales_df = merged_sales_df.copy()
    scheme_df_copy = scheme_df.copy()
    rz_df = rm_zm_df.copy()

    # 3. Standardize Location Casings and Codes
    employee_df['location_name'] = employee_df['location_name'].astype(str).str.strip().str.upper()
    sales_df['Location Name'] = sales_df['Location Name'].astype(str).str.strip().str.upper()
    scheme_df_copy['LocationName'] = scheme_df_copy['LocationName'].astype(str).str.strip().str.upper()
    rz_df['location'] = rz_df['location'].astype(str).str.strip().str.upper()

    employee_df['employee_code'] = employee_df['employee_code'].astype(str).str.strip().str.upper()
    sales_df['Sales Person Code'] = sales_df['Sales Person Code'].astype(str).str.strip().str.upper()
    scheme_df_copy['SALESPERSONCODE'] = scheme_df_copy['SALESPERSONCODE'].astype(str).str.strip().str.upper()

    # 4. Role-Based Access Control (RLS)
    try:
        allowed_locs = get_allowed_locations()
    except RuntimeError:
        allowed_locs = ['ALL']

    if 'ALL' not in allowed_locs:
        employee_df = employee_df[employee_df['location_name'].isin(allowed_locs)]
        sales_df = sales_df[sales_df['Location Name'].isin(allowed_locs)]
        scheme_df_copy = scheme_df_copy[scheme_df_copy['LocationName'].isin(allowed_locs)]
        rz_df = rz_df[rz_df['location'].isin(allowed_locs)]

    # 5. Map RM/ZM into Employee Data
    employee_df = employee_df.merge(rz_df[['location', 'rm', 'zm']].drop_duplicates(), left_on='location_name', right_on='location', how='left')
    # If location field was added by merge, keep location_name as canonical
    if 'location' in employee_df.columns:
        employee_df.drop(columns=['location'], inplace=True)

    # 6. Apply Filters to Employee List
    if locations:
        if isinstance(locations, str):
            locations = [locations]
        locations = [l.strip().upper() for l in locations]
        employee_df = employee_df[employee_df['location_name'].isin(locations)]

    if rms:
        if isinstance(rms, str):
            rms = [rms]
        rms = [r.strip() for r in rms]
        employee_df = employee_df[employee_df['rm'].isin(rms)]

    if zms:
        if isinstance(zms, str):
            zms = [zms]
        zms = [z.strip() for z in zms]
        employee_df = employee_df[employee_df['zm'].isin(zms)]

    if employee_search:
        search_val = str(employee_search).strip().upper()
        employee_df = employee_df[
            (employee_df['employee_code'].str.contains(search_val, na=False)) |
            (employee_df['employee_name'].str.upper().str.contains(search_val, na=False))
        ]

    # Filter and aggregate targets for overlapping months
    period_targets = employee_performance_df.copy()
    period_targets['employee_code'] = period_targets['employee_code'].astype(str).str.strip().str.upper()
    period_targets = period_targets[
        (period_targets['period'].dt.date >= start_month_first) &
        (period_targets['period'].dt.date <= end_dt)
    ]
    
    target_cols = [
        'nsv_target', 'gold_g_target', 'diamond_ct_target', 'silver_g_target',
        'mohor_nsv_target', 'stone_nsv_target', 'ss_count_target', 'ss_value_target'
    ]
    
    if not period_targets.empty:
        emp_targets = period_targets.groupby('employee_code')[target_cols].sum().reset_index()
    else:
        emp_targets = pd.DataFrame(columns=['employee_code'] + target_cols)
        for col in target_cols:
            emp_targets[col] = pd.Series(dtype=float)
            
    # Merge targets into filtered employee list
    employee_df = employee_df.merge(emp_targets, on='employee_code', how='left')
    employee_df[target_cols] = employee_df[target_cols].fillna(0)

    # Filter out empty employee set early
    if employee_df.empty:

        return {
            'master_table': pd.DataFrame(),
            'kpis_layer1': {},
            'kpis_layer2': {},
            'top_3_employees': []
        }

    # List of filtered employee codes
    active_emp_codes = set(employee_df['employee_code'].tolist())

    # 7. Date Filtering & Aggregating Transactional Sales Data (TY vs LY)
    sales_df['Invoice_Date_Only'] = sales_df['Invoice Date'].dt.date
    ty_sales = sales_df[
        (sales_df['Invoice_Date_Only'] >= start_dt) & 
        (sales_df['Invoice_Date_Only'] <= end_dt) &
        (sales_df['Sales Person Code'].isin(active_emp_codes))
    ]

    ly_start_dt = start_dt.replace(year=start_dt.year - 1)
    ly_end_dt = end_dt.replace(year=end_dt.year - 1)
    ly_sales = sales_df[
        (sales_df['Invoice_Date_Only'] >= ly_start_dt) & 
        (sales_df['Invoice_Date_Only'] <= ly_end_dt)
    ]

    # Schemes actuals (TY)
    scheme_df_copy['Scheme_Date_Only'] = scheme_df_copy['SCHEMEOPENINGDATE'].dt.date
    ty_schemes = scheme_df_copy[
        (scheme_df_copy['Scheme_Date_Only'] >= start_dt) & 
        (scheme_df_copy['Scheme_Date_Only'] <= end_dt) &
        (scheme_df_copy['SALESPERSONCODE'].isin(active_emp_codes))
    ]

    # Store LY NSV achieved
    store_ly_nsv = ly_sales.groupby('Location Name')['Bom Line Amount'].sum().reset_index()
    store_ly_nsv.rename(columns={'Location Name': 'location_name', 'Bom Line Amount': 'location_ly_nsv'}, inplace=True)

    # Store TY NSV achieved
    ty_location_sales = sales_df[
        (sales_df['Invoice_Date_Only'] >= start_dt) & 
        (sales_df['Invoice_Date_Only'] <= end_dt)
    ]
    store_ty_nsv = ty_location_sales.groupby('Location Name')['Bom Line Amount'].sum().reset_index()
    store_ty_nsv.rename(columns={'Location Name': 'location_name', 'Bom Line Amount': 'location_ty_nsv'}, inplace=True)

    # Store NSV Target (Sum of Targets for all employees at that location in employee_performance table for the selected months)
    store_targets = employee_performance_df.copy()
    store_targets['location_name'] = store_targets['location_name'].astype(str).str.strip().str.upper()
    if 'ALL' not in allowed_locs:
        store_targets = store_targets[store_targets['location_name'].isin(allowed_locs)]
    store_targets = store_targets[
        (store_targets['period'].dt.date >= start_month_first) & 
        (store_targets['period'].dt.date <= end_dt)
    ]
    store_target_grp = store_targets.groupby('location_name')['nsv_target'].sum().reset_index()
    store_target_grp.rename(columns={'nsv_target': 'location_nsv_target'}, inplace=True)

    # Group Sales actuals by Employee
    # Category 1: NSV
    emp_nsv = ty_sales.groupby('Sales Person Code')['Bom Line Amount'].sum().reset_index()
    emp_nsv.rename(columns={'Sales Person Code': 'employee_code', 'Bom Line Amount': 'nsv_achieved'}, inplace=True)

    # Category 2: Gold (GMS, GOLD)
    gold_sales = ty_sales[(ty_sales['Bom Item Type'] == 'GOLD') & (ty_sales['Bom UOM'] == 'GMS')]
    emp_gold = gold_sales.groupby('Sales Person Code')['Bom Qty'].sum().reset_index()
    emp_gold.rename(columns={'Sales Person Code': 'employee_code', 'Bom Qty': 'gold_achieved'}, inplace=True)

    # Category 3: Diamond (CTS, DIAMOND)
    diamond_sales = ty_sales[(ty_sales['Bom Item Type'] == 'DIAMOND') & (ty_sales['Bom UOM'] == 'CTS')]
    emp_diamond = diamond_sales.groupby('Sales Person Code')['Bom Qty'].sum().reset_index()
    emp_diamond.rename(columns={'Sales Person Code': 'employee_code', 'Bom Qty': 'diamond_achieved'}, inplace=True)

    # Category 4: Silver (GMS, SILVER & Item Type Group == 'SILVER')
    silver_sales = ty_sales[(ty_sales['Bom Item Type'] == 'SILVER') & (ty_sales['Item Type Group'] == 'SILVER') & (ty_sales['Bom UOM'] == 'GMS')]
    emp_silver = silver_sales.groupby('Sales Person Code')['Bom Qty'].sum().reset_index()
    emp_silver.rename(columns={'Sales Person Code': 'employee_code', 'Bom Qty': 'silver_achieved'}, inplace=True)

    # Category 5: Mohor (Brand Id == 'MOHOR')
    mohor_sales = ty_sales[ty_sales['Brand Id'] == 'MOHOR']
    emp_mohor = mohor_sales.groupby('Sales Person Code')['Bom Line Amount'].sum().reset_index()
    emp_mohor.rename(columns={'Sales Person Code': 'employee_code', 'Bom Line Amount': 'mohor_achieved'}, inplace=True)

    # Category 6: Gemstone (Bom Item Type == 'STONE_CT' & Item Type Group == 'NONE')
    gemstone_sales = ty_sales[(ty_sales['Bom Item Type'] == 'STONE_CT') & (ty_sales['Item Type Group'] == 'NONE')]
    emp_gemstone = gemstone_sales.groupby('Sales Person Code')['Bom Line Amount'].sum().reset_index()
    emp_gemstone.rename(columns={'Sales Person Code': 'employee_code', 'Bom Line Amount': 'gemstone_achieved'}, inplace=True)

    # Category: Platinum weight (GMS)
    plat_weight_sales = ty_sales[(ty_sales['Bom Item Type'] == 'PLATINUM') & (ty_sales['Bom UOM'] == 'GMS')]
    emp_plat_weight = plat_weight_sales.groupby('Sales Person Code')['Bom Qty'].sum().reset_index()
    emp_plat_weight.rename(columns={'Sales Person Code': 'employee_code', 'Bom Qty': 'platinum_achieved_gms'}, inplace=True)

    # Category: Platinum NSV
    plat_nsv_sales = ty_sales[ty_sales['Item Type Group'] == 'PLATINUM']
    emp_plat_nsv = plat_nsv_sales.groupby('Sales Person Code')['Bom Line Amount'].sum().reset_index()
    emp_plat_nsv.rename(columns={'Sales Person Code': 'employee_code', 'Bom Line Amount': 'platinum_achieved_nsv'}, inplace=True)

    # Category 7 & 8: Scheme counts & values
    emp_scheme = ty_schemes.groupby('SALESPERSONCODE').agg({
        'SCHEMEENTRYNO': pd.Series.nunique,
        'SchemefirstPayamt': 'sum'
    }).reset_index()
    emp_scheme.rename(columns={
        'SALESPERSONCODE': 'employee_code',
        'SCHEMEENTRYNO': 'ss_count_achieved',
        'SchemefirstPayamt': 'ss_value_achieved'
    }, inplace=True)

    # Employee LYTD NSV achieved
    emp_lytd_nsv = ly_sales.groupby('Sales Person Code')['Bom Line Amount'].sum().reset_index()
    emp_lytd_nsv.rename(columns={'Sales Person Code': 'employee_code', 'Bom Line Amount': 'nsv_lytd'}, inplace=True)

    # 8. Merge all target and actual metrics
    res = employee_df.merge(store_target_grp, on='location_name', how='left')
    res = res.merge(store_ly_nsv, on='location_name', how='left')
    res = res.merge(store_ty_nsv, on='location_name', how='left')
    res = res.merge(emp_nsv, on='employee_code', how='left')
    res = res.merge(emp_gold, on='employee_code', how='left')
    res = res.merge(emp_diamond, on='employee_code', how='left')
    res = res.merge(emp_silver, on='employee_code', how='left')
    res = res.merge(emp_mohor, on='employee_code', how='left')
    res = res.merge(emp_gemstone, on='employee_code', how='left')
    res = res.merge(emp_scheme, on='employee_code', how='left')
    res = res.merge(emp_plat_weight, on='employee_code', how='left')
    res = res.merge(emp_plat_nsv, on='employee_code', how='left')
    res = res.merge(emp_lytd_nsv, on='employee_code', how='left')

    # Fill actual achievements with 0
    achieved_cols = [
        'nsv_achieved', 'gold_achieved', 'diamond_achieved', 'silver_achieved',
        'mohor_achieved', 'gemstone_achieved', 'ss_count_achieved', 'ss_value_achieved',
        'location_nsv_target', 'location_ly_nsv', 'location_ty_nsv',
        'platinum_achieved_gms', 'platinum_achieved_nsv', 'nsv_lytd'
    ]
    res[achieved_cols] = res[achieved_cols].fillna(0)

    # Ensure targets are float
    target_cols = [
        'nsv_target', 'gold_g_target', 'diamond_ct_target', 'silver_g_target',
        'mohor_nsv_target', 'stone_nsv_target', 'ss_count_target', 'ss_value_target'
    ]
    res[target_cols] = res[target_cols].fillna(0)

    # Filter out inactive employees: must have at least one non-zero target or non-zero achieved
    res = res[
        (res[target_cols].sum(axis=1) > 0) | 
        (res[['nsv_achieved', 'gold_achieved', 'diamond_achieved', 'silver_achieved',
              'mohor_achieved', 'gemstone_achieved', 'ss_count_achieved', 'ss_value_achieved',
              'platinum_achieved_gms', 'platinum_achieved_nsv']].sum(axis=1) > 0)
    ]

    # Calculate contribution % of NSV
    res['nsv_contrib'] = np.where(
        res['location_ty_nsv'] > 0,
        (res['nsv_achieved'] / res['location_ty_nsv']) * 100.0,
        0.0
    )

    if res.empty:
        return {
            'master_table': pd.DataFrame(),
            'kpis_layer1': {},
            'kpis_layer2': {},
            'top_3_employees': []
        }

    # 9. Compute Score Points (Rank) and % Differences for each metric
    def calc_metrics(row, act_col, tgt_col):
        act = float(row[act_col])
        tgt = float(row[tgt_col])
        
        if tgt == 0:
            if act == 0:
                pct = 0.0
                score = 1
            else:
                pct = 100.0
                score = 5
        else:
            pct = (act / tgt) * 100.0
            if pct >= 100.0:
                score = 5
            elif pct >= 90.0:
                score = 4
            elif pct >= 75.0:
                score = 3
            elif pct >= 60.0:
                score = 2
            else:
                score = 1
            
        return pct, score

    # NSV
    res['nsv_pct'], res['nsv_rank'] = zip(*res.apply(lambda r: calc_metrics(r, 'nsv_achieved', 'nsv_target'), axis=1))
    # Gold
    res['gold_pct'], res['gold_rank'] = zip(*res.apply(lambda r: calc_metrics(r, 'gold_achieved', 'gold_g_target'), axis=1))
    # Diamond
    res['diamond_pct'], res['diamond_rank'] = zip(*res.apply(lambda r: calc_metrics(r, 'diamond_achieved', 'diamond_ct_target'), axis=1))
    # Silver
    res['silver_pct'], res['silver_rank'] = zip(*res.apply(lambda r: calc_metrics(r, 'silver_achieved', 'silver_g_target'), axis=1))
    # Mohor
    res['mohor_pct'], res['mohor_rank'] = zip(*res.apply(lambda r: calc_metrics(r, 'mohor_achieved', 'mohor_nsv_target'), axis=1))
    # Gemstone
    res['gemstone_pct'], res['gemstone_rank'] = zip(*res.apply(lambda r: calc_metrics(r, 'gemstone_achieved', 'stone_nsv_target'), axis=1))
    # SS Count
    res['ss_count_pct'], res['ss_count_rank'] = zip(*res.apply(lambda r: calc_metrics(r, 'ss_count_achieved', 'ss_count_target'), axis=1))
    # SS Value
    res['ss_value_pct'], res['ss_value_rank'] = zip(*res.apply(lambda r: calc_metrics(r, 'ss_value_achieved', 'ss_value_target'), axis=1))

    # 10. Compute Final Rank (Weighted Score out of 5.00)
    res['final_rank'] = (
        res['nsv_rank'] * 0.50 +
        res['gold_rank'] * 0.15 +
        res['silver_rank'] * 0.10 +
        res['diamond_rank'] * 0.05 +
        res['mohor_rank'] * 0.05 +
        res['gemstone_rank'] * 0.05 +
        res['ss_count_rank'] * 0.05 +
        res['ss_value_rank'] * 0.05
    )
    res['final_rank'] = res['final_rank'].round(2)

    # 11. Prepare Master Table output format
    cols_order = [
        'location_code', 'location_name', 'employee_code', 'employee_name',
        'job_title', 'date_joined', 'employment_status', 'final_rank',
        'location_nsv_target', 'location_ly_nsv', 'location_ty_nsv',
        'nsv_target', 'nsv_achieved', 'nsv_lytd', 'nsv_pct', 'nsv_contrib', 'nsv_rank',
        'gold_g_target', 'gold_achieved', 'gold_pct', 'gold_rank',
        'diamond_ct_target', 'diamond_achieved', 'diamond_pct', 'diamond_rank',
        'silver_g_target', 'silver_achieved', 'silver_pct', 'silver_rank',
        'mohor_nsv_target', 'mohor_achieved', 'mohor_pct', 'mohor_rank',
        'stone_nsv_target', 'gemstone_achieved', 'gemstone_pct', 'gemstone_rank',
        'ss_count_target', 'ss_count_achieved', 'ss_count_pct', 'ss_count_rank',
        'ss_value_target', 'ss_value_achieved', 'ss_value_pct', 'ss_value_rank',
        'platinum_achieved_gms', 'platinum_achieved_nsv'
    ]
    master_df = res[cols_order].sort_values(by=['final_rank', 'nsv_achieved'], ascending=[False, False])

    # 12. Aggregate KPIs
    # Manpower count
    total_manpower = int(res['employee_code'].nunique())
    
    # Layer 1: Total Achievements
    ach_nsv = float(res['nsv_achieved'].sum())
    ach_gold = float(res['gold_achieved'].sum())
    ach_diamond = float(res['diamond_achieved'].sum())
    ach_silver = float(res['silver_achieved'].sum())
    ach_mohor = float(res['mohor_achieved'].sum())
    ach_gemstone = float(res['gemstone_achieved'].sum())
    ach_ss_count = float(res['ss_count_achieved'].sum())
    ach_ss_value = float(res['ss_value_achieved'].sum())

    kpis_layer1 = {
        'total_manpower': total_manpower,
        'nsv': ach_nsv,
        'gold': ach_gold,
        'diamond': ach_diamond,
        'silver': ach_silver,
        'mohor': ach_mohor,
        'gemstone': ach_gemstone,
        'ss_count': ach_ss_count,
        'ss_value': ach_ss_value
    }

    # Layer 2: Total Target vs Achieved
    tgt_nsv = float(res['nsv_target'].sum())
    tgt_gold = float(res['gold_g_target'].sum())
    tgt_diamond = float(res['diamond_ct_target'].sum())
    tgt_silver = float(res['silver_g_target'].sum())
    tgt_mohor = float(res['mohor_nsv_target'].sum())
    tgt_gemstone = float(res['stone_nsv_target'].sum())
    tgt_ss_count = float(res['ss_count_target'].sum())
    tgt_ss_value = float(res['ss_value_target'].sum())

    def calc_layer2_pct_diff(ach, tgt):
        diff = ach - tgt
        pct = (ach / tgt) * 100.0 if tgt > 0 else 100.0
        return pct, diff

    nsv_pct, nsv_diff = calc_layer2_pct_diff(ach_nsv, tgt_nsv)
    gold_pct, gold_diff = calc_layer2_pct_diff(ach_gold, tgt_gold)
    diamond_pct, diamond_diff = calc_layer2_pct_diff(ach_diamond, tgt_diamond)
    silver_pct, silver_diff = calc_layer2_pct_diff(ach_silver, tgt_silver)
    mohor_pct, mohor_diff = calc_layer2_pct_diff(ach_mohor, tgt_mohor)
    gemstone_pct, gemstone_diff = calc_layer2_pct_diff(ach_gemstone, tgt_gemstone)
    ss_count_pct, ss_count_diff = calc_layer2_pct_diff(ach_ss_count, tgt_ss_count)
    ss_value_pct, ss_value_diff = calc_layer2_pct_diff(ach_ss_value, tgt_ss_value)

    kpis_layer2 = {
        'nsv': {'pct': nsv_pct, 'diff': nsv_diff, 'achieved': ach_nsv, 'target': tgt_nsv},
        'gold': {'pct': gold_pct, 'diff': gold_diff, 'achieved': ach_gold, 'target': tgt_gold},
        'diamond': {'pct': diamond_pct, 'diff': diamond_diff, 'achieved': ach_diamond, 'target': tgt_diamond},
        'silver': {'pct': silver_pct, 'diff': silver_diff, 'achieved': ach_silver, 'target': tgt_silver},
        'mohor': {'pct': mohor_pct, 'diff': mohor_diff, 'achieved': ach_mohor, 'target': tgt_mohor},
        'gemstone': {'pct': gemstone_pct, 'diff': gemstone_diff, 'achieved': ach_gemstone, 'target': tgt_gemstone},
        'ss_count': {'pct': ss_count_pct, 'diff': ss_count_diff, 'achieved': ach_ss_count, 'target': tgt_ss_count},
        'ss_value': {'pct': ss_value_pct, 'diff': ss_value_diff, 'achieved': ach_ss_value, 'target': tgt_ss_value}
    }

    # Layer 3: Top 3 Employees
    top_3_df = master_df.head(3)
    top_3_employees = []
    for idx, r in top_3_df.iterrows():
        top_3_employees.append({
            'name': r['employee_name'],
            'final_rank': r['final_rank'],
            'nsv': float(r['nsv_achieved']),
            'gold': float(r['gold_achieved']),
            'diamond': float(r['diamond_achieved']),
            'silver': float(r['silver_achieved']),
            'mohor': float(r['mohor_achieved']),
            'gemstone': float(r['gemstone_achieved']),
            'ss_count': float(r['ss_count_achieved']),
            'ss_value': float(r['ss_value_achieved'])
        })

    return {
        'master_table': master_df,
        'kpis_layer1': kpis_layer1,
        'kpis_layer2': kpis_layer2,
        'top_3_employees': top_3_employees
    }
