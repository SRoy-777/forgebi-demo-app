import os
import re
import pandas as pd
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
        os.path.join(script_dir, "../../../snapshot/gl_advertisement.parquet")
    )

    if not os.path.exists(parquet_path):
        print(f"Warning: {parquet_path} does not exist yet. Returning empty DataFrame.")
        return pd.DataFrame()

    df = pd.read_parquet(parquet_path)
    df['posting_date'] = pd.to_datetime(df['posting_date'])
    df['month_year'] = df['posting_date'].dt.strftime('%b-%Y')
    
    # Store standard fields
    df['location_code'] = df['location_code'].astype(str).str.strip()
    df['location_name'] = df['location_name'].astype(str).str.strip().str.upper()

    # Keep cached copy
    _cached_df = df
    return _cached_df.copy()


def get_available_months():
    df = load_data()
    if df.empty or 'month_year' not in df.columns:
        return []
    
    unique_months = df['month_year'].dropna().unique().tolist()
    try:
        sorted_months = sorted(
            unique_months,
            key=lambda m: pd.to_datetime(m, format='%b-%Y')
        )
        return sorted_months
    except Exception:
        return sorted(unique_months)


def get_filtered_data(selected_months=None, locations=None):
    df = load_data()
    if df.empty:
        return df

    # Apply Session RLS
    allowed_locations = get_allowed_locations()
    if allowed_locations and 'ALL' not in allowed_locations:
        allowed_upper = [l.upper().strip() for l in allowed_locations]
        df = df[df['location_name'].isin(allowed_upper)]

    # Apply Dropdown Location Search Filter
    if locations:
        locations_upper = [str(i).strip().upper() for i in locations]
        df = df[df['location_name'].isin(locations_upper)]

    # Apply Months Filter
    if selected_months:
        df = df[df['month_year'].isin(selected_months)]

    return df


# Columns mapping dictionary
METRICS_MAP = {
    'Ad Expense': 'ad_expense',
    'Revenue': 'revenue',
    'Footfall': 'footfall',
    'CPF (Cost Per Footfall)': 'cpf',
    'ACoS (Ad Cost of Sales)': 'acos',
    'RPV (Revenue Per Visits)': 'rpv'
}


def calculate_metrics_row(ad_expense, revenue, footfall):
    cpf = (ad_expense / footfall) if footfall else 0.0
    acos = (ad_expense / revenue * 100.0) if revenue else 0.0
    rpv = (revenue / footfall) if footfall else 0.0
    return cpf, acos, rpv


def get_roas_conversion_kpis(selected_months, locations=None):
    df = get_filtered_data(selected_months, locations)
    if df.empty:
        return {'cpf': 0.0, 'acos': 0.0, 'rpv': 0.0}

    total_ad = df['value'].sum()
    total_revenue = df['nsv'].sum()
    total_footfall = df['footfall'].sum()

    cpf, acos, rpv = calculate_metrics_row(total_ad, total_revenue, total_footfall)
    return {
        'cpf': cpf,
        'acos': acos,
        'rpv': rpv
    }


def get_roas_conversion_report(selected_months, mode="Consolidate", selected_metrics=None, locations=None):
    df = get_filtered_data(selected_months, locations)
    
    if df.empty:
        return pd.DataFrame(), []

    if selected_metrics is None:
        selected_metrics = list(METRICS_MAP.keys())

    # Map selected metrics to key column ids
    active_metric_ids = [METRICS_MAP[m] for m in selected_metrics if m in METRICS_MAP]

    # Convert numeric fields to numeric
    for col in ['value', 'nsv', 'footfall']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # ---------------------------------------------------
    # Consolidate Mode
    # ---------------------------------------------------
    if mode == "Consolidate":
        # Aggregate all dates
        agg_df = df.groupby(['location_code', 'location_name'], as_index=False).agg({
            'value': 'sum',
            'nsv': 'sum',
            'footfall': 'sum'
        })

        # Calculate metrics & ratios
        agg_df['cpf'] = agg_df.apply(lambda r: (r['value'] / r['footfall']) if r['footfall'] else 0.0, axis=1)
        agg_df['acos'] = agg_df.apply(lambda r: (r['value'] / r['nsv'] * 100.0) if r['nsv'] else 0.0, axis=1)
        agg_df['rpv'] = agg_df.apply(lambda r: (r['nsv'] / r['footfall']) if r['footfall'] else 0.0, axis=1)
        
        # Rename internal keys to metrics names
        agg_df = agg_df.rename(columns={
            'value': 'ad_expense',
            'nsv': 'revenue'
        })

        # Generate total row
        tot_ad = agg_df['ad_expense'].sum()
        tot_revenue = agg_df['revenue'].sum()
        tot_footfall = agg_df['footfall'].sum()
        tot_cpf, tot_acos, tot_rpv = calculate_metrics_row(tot_ad, tot_revenue, tot_footfall)

        total_row = pd.DataFrame([{
            'location_code': '',
            'location_name': 'TOTAL',
            'ad_expense': tot_ad,
            'revenue': tot_revenue,
            'footfall': tot_footfall,
            'cpf': tot_cpf,
            'acos': tot_acos,
            'rpv': tot_rpv
        }])

        agg_df = pd.concat([agg_df, total_row], ignore_index=True)

        # Prepare final output structure
        cols_to_keep = ['location_code', 'location_name'] + active_metric_ids
        report_df = agg_df[cols_to_keep].copy()

        # Build column header suffix
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

        datatable_columns = [
            {'name': 'Code', 'id': 'code'},
            {'name': 'Location', 'id': 'location_name'}
        ]
        
        # Build rename mapping
        rename_map = {'location_code': 'code', 'location_name': 'location_name'}
        for metric_label, m_id in METRICS_MAP.items():
            if m_id in active_metric_ids:
                col_header = f"{metric_label} ({period_label})"
                datatable_columns.append({'name': col_header, 'id': col_header})
                rename_map[m_id] = col_header

        report_df = report_df.rename(columns=rename_map)
        return report_df, datatable_columns

    # ---------------------------------------------------
    # Compare Mode
    # ---------------------------------------------------
    else:
        # Sort months chronologically
        sorted_months = sorted(
            list(df['month_year'].dropna().unique()),
            key=lambda m: pd.to_datetime(m, format='%b-%Y')
        )

        # Find unique location keys
        unique_keys = df[['location_code', 'location_name']].drop_duplicates().sort_values('location_name').values.tolist()
        base_df = pd.DataFrame(unique_keys, columns=['location_code', 'location_name'])

        datatable_columns = [
            {'name': 'Code', 'id': 'code'},
            {'name': 'Location', 'id': 'location_name'}
        ]

        # Calculate table values for each month
        for metric_label in selected_metrics:
            m_id = METRICS_MAP[metric_label]
            for month in sorted_months:
                col_id = f"{m_id}_{month}"
                col_header = f"{metric_label} ({month})"
                datatable_columns.append({'name': col_header, 'id': col_id})

                # Isolate month records
                month_df = df[df['month_year'] == month].copy()
                
                # Group by location
                month_grouped = month_df.groupby(['location_code', 'location_name'], as_index=False).agg({
                    'value': 'sum',
                    'nsv': 'sum',
                    'footfall': 'sum'
                })
                
                # Calculate metrics
                month_grouped['ad_expense'] = month_grouped['value']
                month_grouped['revenue'] = month_grouped['nsv']
                month_grouped['cpf'] = month_grouped.apply(lambda r: (r['value'] / r['footfall']) if r['footfall'] else 0.0, axis=1)
                month_grouped['acos'] = month_grouped.apply(lambda r: (r['value'] / r['nsv'] * 100.0) if r['nsv'] else 0.0, axis=1)
                month_grouped['rpv'] = month_grouped.apply(lambda r: (r['nsv'] / r['footfall']) if r['footfall'] else 0.0, axis=1)

                # Merge back to base_df
                temp_merged = base_df.merge(
                    month_grouped[['location_code', 'location_name', m_id]],
                    on=['location_code', 'location_name'],
                    how='left'
                )
                base_df[col_id] = temp_merged[m_id].fillna(0.0)

        # Generate total row
        total_row = {'location_code': '', 'location_name': 'TOTAL'}
        
        # To compute total ratios accurately, we first aggregate base monthly metrics for all months
        month_aggregates = {}
        for month in sorted_months:
            month_df = df[df['month_year'] == month]
            tot_ad = month_df['value'].sum()
            tot_rev = month_df['nsv'].sum()
            tot_ff = month_df['footfall'].sum()
            
            tot_cpf, tot_acos, tot_rpv = calculate_metrics_row(tot_ad, tot_rev, tot_ff)
            
            month_aggregates[month] = {
                'ad_expense': tot_ad,
                'revenue': tot_rev,
                'footfall': tot_ff,
                'cpf': tot_cpf,
                'acos': tot_acos,
                'rpv': tot_rpv
            }

        # Populate total row cell values
        for metric_label in selected_metrics:
            m_id = METRICS_MAP[metric_label]
            for month in sorted_months:
                col_id = f"{m_id}_{month}"
                total_row[col_id] = month_aggregates[month][m_id]

        total_row_df = pd.DataFrame([total_row])
        base_df = pd.concat([base_df, total_row_df], ignore_index=True)

        # Rename standard columns
        base_df = base_df.rename(columns={
            'location_code': 'code',
            'location_name': 'location_name'
        })

        return base_df, datatable_columns
