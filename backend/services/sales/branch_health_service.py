import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '../..'
        )
    )
)

import pandas as pd
import numpy as np

from backend.cache.data_cache import (
    branch_daily_aggregate_df,
    daily_targets_df,
    rm_zm_df
)

from backend.services.rls import (
    get_allowed_locations
)

# ---------------------------------------------------
# Metric Config
# ---------------------------------------------------

METRIC_CONFIG = {

    'nsv': {
        'actual_col': 'nsv',
        'target_col': 'nsv_target',
        'label': 'NSV'
    },

    'gold': {
        'actual_col': 'gold',
        'target_col': 'gold_target',
        'label': 'Gold Gms'
    },

    'diamond_cts': {
        'actual_col': 'diamond_cts',
        'target_col': 'diamond_cts_target',
        'label': 'Diamond CTS'
    },

    'silver_gms': {
        'actual_col': 'silver_gms',
        'target_col': 'silver_target',
        'label': 'Silver Gms'
    },

    'mohor_nsv': {
        'actual_col': 'mohor_nsv',
        'target_col': 'mohor_target',
        'label': 'Mohor NSV'
    },

    'gemstone_nsv': {
        'actual_col': 'gemstone_nsv',
        'target_col': 'gemstone_target',
        'label': 'Gemstone NSV'
    }

}

# ---------------------------------------------------
# Financial Year Helpers
# ---------------------------------------------------

def get_financial_year_start(date):

    date = pd.to_datetime(date)

    if date.month >= 4:

        return pd.Timestamp(
            year=date.year,
            month=4,
            day=1
        )

    return pd.Timestamp(
        year=date.year - 1,
        month=4,
        day=1
    )

# ---------------------------------------------------
# Full Month Range Helper
# ---------------------------------------------------

def get_full_month_range(

    start_date,
    end_date

):

    start_date = pd.to_datetime(start_date)

    end_date = pd.to_datetime(end_date)

    month_start = start_date.replace(day=1)

    month_end = (
        end_date
        + pd.offsets.MonthEnd(0)
    )

    return month_start, month_end

# ---------------------------------------------------
# Previous Year Range
# ---------------------------------------------------

def shift_last_year(

    start_date,
    end_date

):

    return (

        pd.to_datetime(start_date)
        - pd.DateOffset(years=1),

        pd.to_datetime(end_date)
        - pd.DateOffset(years=1)

    )

# ---------------------------------------------------
# Prepare Branch Health Data
# ---------------------------------------------------

def prepare_branch_health_data(

    start_date,
    end_date,

    locations=None,
    rms=None,
    zms=None

):

    # ---------------------------------------------------
    # Copy Cached Data
    # ---------------------------------------------------

    sales_df = branch_daily_aggregate_df.copy()

    targets_df = daily_targets_df.copy()

    rm_zm = rm_zm_df.copy()

    # ---------------------------------------------------
    # Standardize Text
    # ---------------------------------------------------

    sales_df['Location'] = (

        sales_df['Location']
        .astype(str)
        .str.strip()
        .str.upper()

    )

    targets_df['Location'] = (

        targets_df['Location']
        .astype(str)
        .str.strip()
        .str.upper()

    )

    rm_zm['location'] = (

        rm_zm['location']
        .astype(str)
        .str.strip()
        .str.upper()

    )

    rm_zm['rm'] = (

        rm_zm['rm']
        .astype(str)
        .str.strip()
        .str.upper()

    )

    rm_zm['zm'] = (

        rm_zm['zm']
        .astype(str)
        .str.strip()
        .str.upper()

    )

    # ---------------------------------------------------
    # Date Conversion
    # ---------------------------------------------------

    sales_df['Date'] = pd.to_datetime(
        sales_df['Date']
    )

    targets_df['Date'] = pd.to_datetime(
        targets_df['Date']
    )

    start_date = pd.to_datetime(start_date)

    end_date = pd.to_datetime(end_date)

    # ---------------------------------------------------
    # RLS
    # ---------------------------------------------------

    try:

        allowed_locations = get_allowed_locations()

    except:

        allowed_locations = ['ALL']

    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location']
            .isin(allowed_locations)

        ]

        targets_df = targets_df[

            targets_df['Location']
            .isin(allowed_locations)

        ]

        rm_zm = rm_zm[

            rm_zm['location']
            .isin(allowed_locations)

        ]

    # ---------------------------------------------------
    # RM Filter
    # ---------------------------------------------------

    if rms:

        rm_locations = rm_zm[

            rm_zm['rm']
            .isin(rms)

        ]['location'].unique()

        sales_df = sales_df[

            sales_df['Location']
            .isin(rm_locations)

        ]

        targets_df = targets_df[

            targets_df['Location']
            .isin(rm_locations)

        ]

    # ---------------------------------------------------
    # ZM Filter
    # ---------------------------------------------------

    if zms:

        zm_locations = rm_zm[

            rm_zm['zm']
            .isin(zms)

        ]['location'].unique()

        sales_df = sales_df[

            sales_df['Location']
            .isin(zm_locations)

        ]

        targets_df = targets_df[

            targets_df['Location']
            .isin(zm_locations)

        ]

    # ---------------------------------------------------
    # Location Filter
    # ---------------------------------------------------

    if locations:

        locations = [

            str(i).strip().upper()

            for i in locations

        ]

        sales_df = sales_df[

            sales_df['Location']
            .isin(locations)

        ]

        targets_df = targets_df[

            targets_df['Location']
            .isin(locations)

        ]

    # ---------------------------------------------------
    # Current Period
    # ---------------------------------------------------

    current_sales_df = sales_df[

        (
            sales_df['Date']
            >= start_date
        )

        &

        (
            sales_df['Date']
            <= end_date
        )

    ]

    current_targets_df = targets_df[

        (
            targets_df['Date']
            >= start_date
        )

        &

        (
            targets_df['Date']
            <= end_date
        )

    ]

    # ---------------------------------------------------
    # Full Month Targets
    # ---------------------------------------------------

    month_start, month_end = get_full_month_range(

        start_date,
        end_date

    )

    month_targets_df = targets_df[

        (

            targets_df['Date']
            >= month_start

        )

        &

        (

            targets_df['Date']
            <= month_end

        )

    ]

    # ---------------------------------------------------
    # Today
    # ---------------------------------------------------

    today_sales_df = sales_df[

        sales_df['Date']
        == end_date

    ]

    today_targets_df = targets_df[

        targets_df['Date']
        == end_date

    ]

    # ---------------------------------------------------
    # LY Today
    # ---------------------------------------------------

    ly_today_date = (
        end_date
        - pd.DateOffset(years=1)
    )

    ly_today_sales_df = sales_df[

        sales_df['Date']
        == ly_today_date

    ]

    # ---------------------------------------------------
    # LY MTD
    # ---------------------------------------------------

    ly_start_date, ly_end_date = shift_last_year(

        start_date,
        end_date

    )

    ly_mtd_sales_df = sales_df[

        (
            sales_df['Date']
            >= ly_start_date
        )

        &

        (
            sales_df['Date']
            <= ly_end_date
        )

    ]

    # ---------------------------------------------------
    # LY M
    # ---------------------------------------------------

    ly_month_start, ly_month_end = get_full_month_range(

        ly_start_date,
        ly_end_date

    )

    ly_m_sales_df = sales_df[

        (
            sales_df['Date']
            >= ly_month_start
        )

        &

        (
            sales_df['Date']
            <= ly_month_end
        )

    ]

    # ---------------------------------------------------
    # TY Target
    # ---------------------------------------------------

    fy_start = get_financial_year_start(
        end_date
    )

    full_month_end = (
        end_date
        + pd.offsets.MonthEnd(0)
    )

    ty_targets_df = targets_df[

        (
            targets_df['Date']
            >= fy_start
        )

        &

        (
            targets_df['Date']
            <= full_month_end
        )

    ]

    # ---------------------------------------------------
    # YTD Target
    # ---------------------------------------------------

    ytd_targets_df = targets_df[

        (
            targets_df['Date']
            >= fy_start
        )

        &

        (
            targets_df['Date']
            <= end_date
        )

    ]

    # ---------------------------------------------------
    # LY TD
    # ---------------------------------------------------

    ly_fy_start = (
        fy_start
        - pd.DateOffset(years=1)
    )

    ly_td_end = (
        end_date
        - pd.DateOffset(years=1)
    )

    ly_td_sales_df = sales_df[

        (
            sales_df['Date']
            >= ly_fy_start
        )

        &

        (
            sales_df['Date']
            <= ly_td_end
        )

    ]

    # ---------------------------------------------------
    # TY TD
    # ---------------------------------------------------

    ty_td_sales_df = sales_df[

        (
            sales_df['Date']
            >= fy_start
        )

        &

        (
            sales_df['Date']
            <= end_date
        )

    ]

    # ---------------------------------------------------
    # LY Full
    # ---------------------------------------------------

    ly_full_start = pd.Timestamp(
        year=ly_fy_start.year,
        month=4,
        day=1
    )

    ly_full_end = pd.Timestamp(
        year=ly_fy_start.year + 1,
        month=3,
        day=31
    )

    ly_full_sales_df = sales_df[

        (
            sales_df['Date']
            >= ly_full_start
        )

        &

        (
            sales_df['Date']
            <= ly_full_end
        )

    ]

    sales_df = sales_df.fillna(0)

    targets_df = targets_df.fillna(0)

    return {

        'current_sales_df': current_sales_df,
        'current_targets_df': current_targets_df,

        'month_targets_df': month_targets_df,

        'today_sales_df': today_sales_df,
        'today_targets_df': today_targets_df,

        'ly_today_sales_df': ly_today_sales_df,

        'ly_mtd_sales_df': ly_mtd_sales_df,
        'ly_m_sales_df': ly_m_sales_df,

        'ty_targets_df': ty_targets_df,
        'ytd_targets_df': ytd_targets_df,

        'ly_td_sales_df': ly_td_sales_df,
        'ty_td_sales_df': ty_td_sales_df,

        'ly_full_sales_df': ly_full_sales_df,

        'start_date': start_date,
        'end_date': end_date

    }

# ---------------------------------------------------
# Aggregate Helper
# ---------------------------------------------------

def aggregate_metrics(

    df

):

    if df.empty:

        return {

            'nsv': 0,
            'gold': 0,
            'diamond_cts': 0,
            'silver_gms': 0,
            'mohor_nsv': 0,
            'gemstone_nsv': 0,

            'invoices': 0,
            'tags': 0,
            'customers': 0,
            'Footfall': 0,

            'Cash': 0,
            'Cheque': 0,
            'Card': 0,
            'UPI': 0,
            'NEFT/RTGS': 0
        }

    aggregation = {

        'nsv': df['nsv'].sum(),
        'gold': df['gold'].sum(),
        'diamond_cts': df['diamond_cts'].sum(),
        'silver_gms': df['silver_gms'].sum(),
        'mohor_nsv': df['mohor_nsv'].sum(),
        'gemstone_nsv': df['gemstone_nsv'].sum(),
        'gold_nsv': df['gold_nsv'].sum(),
        'diamond_nsv': df['diamond_nsv'].sum(),
        'silver_nsv': df['silver_nsv'].sum(),
        

        'invoices': df['invoices'].sum(),
        'tags': df['tags'].sum(),
        'customers': df['customers'].sum(),
        'Footfall': df['Footfall'].sum(),

        'Cash': df['Cash'].sum(),
        'Cheque': df['Cheque'].sum(),
        'Card': df['Card'].sum(),
        'UPI': df['UPI'].sum(),
        'NEFT/RTGS': df['NEFT/RTGS'].sum()

    }

    return aggregation

# ---------------------------------------------------
# Aggregate Targets
# ---------------------------------------------------

def aggregate_targets(

    df

):

    if df.empty:

        return {

            'nsv_target': 0,
            'gold_target': 0,
            'diamond_cts_target': 0,
            'silver_target': 0,
            'mohor_target': 0,
            'gemstone_target': 0
        }

    aggregation = {

        'nsv_target': df['nsv_target'].sum(),
        'gold_target': df['gold_target'].sum(),
        'diamond_cts_target': df['diamond_cts_target'].sum(),
        'silver_target': df['silver_target'].sum(),
        'mohor_target': df['mohor_target'].sum(),
        'gemstone_target': df['gemstone_target'].sum()

    }

    return aggregation

# ---------------------------------------------------
# Safe Division
# ---------------------------------------------------

def safe_divide(

    numerator,
    denominator

):

    if pd.isna(denominator) or denominator == 0:

        return 0

    try:

        return numerator / denominator

    except:

        return 0

# ---------------------------------------------------
# KPI Calculation
# ---------------------------------------------------

def calculate_kpis(

    metrics

):

    nsv = metrics.get('nsv', 0)

    invoices = metrics.get('invoices', 0)

    tags = metrics.get('tags', 0)

    customers = metrics.get('customers', 0)

    footfall = metrics.get('Footfall', 0)

    total_collection = (

        metrics.get('Cash', 0)

        +

        metrics.get('Cheque', 0)

        +

        metrics.get('Card', 0)

        +

        metrics.get('UPI', 0)

        +

        metrics.get('NEFT/RTGS', 0)

    )

    digital_collection = (

        metrics.get('UPI', 0)

    )

    return {

        # ---------------------------------------------------
        # Core KPIs
        # ---------------------------------------------------

        'NSV': nsv,

        'ATV': safe_divide(
            nsv,
            invoices
        ),

        'ASP': safe_divide(
            nsv,
            tags
        ),

        'UPT': safe_divide(
            tags,
            invoices
        ),

        'Customer Conversion %': (

            safe_divide(
                customers,
                footfall
            ) * 100
        ),

        # ---------------------------------------------------
        # Contribution %
        # ---------------------------------------------------

        'Gold %': (

            safe_divide(

                metrics.get('gold_nsv', 0),

                nsv

            ) * 100
        ),

        'Diamond %': (

            safe_divide(

                metrics.get('diamond_nsv', 0),

                nsv

            ) * 100
        ),

        'Silver %': (

            safe_divide(

                metrics.get('silver_nsv', 0),

                nsv

            ) * 100
        ),

        'Gemstone %': (

            safe_divide(

                metrics.get('gemstone_nsv', 0),

                nsv

            ) * 100
        ),

        'Mohor %': (

            safe_divide(

                metrics.get('mohor_nsv', 0),

                nsv

            ) * 100
        ),

        # ---------------------------------------------------
        # Collection KPIs
        # ---------------------------------------------------

        'Total Collection': total_collection,

        'Cash': metrics.get('Cash', 0),

        'Card': metrics.get('Card', 0),

        'Cheque': metrics.get('Cheque', 0),

        'Digital': digital_collection

    }

# ---------------------------------------------------
# KPI Section Generator
# ---------------------------------------------------

def get_kpi_sections(

    prepared_data

):

    # ---------------------------------------------------
    # Today
    # ---------------------------------------------------

    today_metrics = aggregate_metrics(

        prepared_data['today_sales_df']

    )

    today_kpis = calculate_kpis(

        today_metrics

    )

    # ---------------------------------------------------
    # MTD
    # ---------------------------------------------------

    mtd_metrics = aggregate_metrics(

        prepared_data['current_sales_df']

    )

    mtd_kpis = calculate_kpis(

        mtd_metrics

    )

    # ---------------------------------------------------
    # YTD
    # ---------------------------------------------------

    ytd_metrics = aggregate_metrics(

        prepared_data['ty_td_sales_df']

    )

    ytd_kpis = calculate_kpis(

        ytd_metrics

    )

    return {

        'today_kpis': today_kpis,

        'mtd_kpis': mtd_kpis,

        'ytd_kpis': ytd_kpis

    }

# ---------------------------------------------------
# Generate Comparison Row
# ---------------------------------------------------

def generate_comparison_row(

    metric_name,

    actual_value=0,

    target_value=0,

    ly_value=0

):

    vs_target_pct = (

        safe_divide(
            actual_value - target_value,
            target_value
        ) * 100
    )

    vs_ly_pct = (

        safe_divide(
            actual_value - ly_value,
            ly_value
        ) * 100
    )

    return {

        'Metric': metric_name,

        'Actual': round(actual_value, 2),

        'Target': round(target_value, 2),

        'LY': round(ly_value, 2),

        'Vs Target %': round(vs_target_pct, 2),

        'Vs LY %': round(vs_ly_pct, 2)

    }
# ---------------------------------------------------
# Today Table
# ---------------------------------------------------

def generate_today_table(

    prepared_data

):

    # ---------------------------------------------------
    # Metrics
    # ---------------------------------------------------

    today_metrics = aggregate_metrics(

        prepared_data['today_sales_df']

    )

    today_targets = aggregate_targets(

        prepared_data['today_targets_df']

    )

    ly_today_metrics = aggregate_metrics(

        prepared_data['ly_today_sales_df']

    )

    ly_m_metrics = aggregate_metrics(

        prepared_data['ly_m_sales_df']

    )

    ly_mtd_metrics = aggregate_metrics(

        prepared_data['ly_mtd_sales_df']

    )

    rows = []

    # ---------------------------------------------------
    # Target Metrics
    # ---------------------------------------------------

    for metric_key, config in METRIC_CONFIG.items():

        actual_value = today_metrics.get(

            config['actual_col'],
            0

        )

        target_value = today_targets.get(

            config['target_col'],
            0

        )

        ly_today_value = ly_today_metrics.get(

            config['actual_col'],
            0

        )

        ly_m_value = ly_m_metrics.get(

            config['actual_col'],
            0

        )

        ly_mtd_value = ly_mtd_metrics.get(

            config['actual_col'],
            0

        )

        vs_target_pct = (

            safe_divide(

                actual_value - target_value,
                target_value

            ) * 100

        )

        vs_ly_pct = (

            safe_divide(

                actual_value - ly_today_value,
                ly_today_value

            ) * 100

        )

        rows.append({

            'Metric': config['label'],

            'Target': round(target_value, 2),

            'LY Today': round(ly_today_value, 2),

            'Today': round(actual_value, 2),

            'LY M': round(ly_m_value, 2),

            'LY MTD': round(ly_mtd_value, 2),

            'Vs Target %': round(vs_target_pct, 2),

            'Vs LY %': round(vs_ly_pct, 2)

        })

    # ---------------------------------------------------
    # Non Target Metrics
    # ---------------------------------------------------

    non_target_metrics = {

        'Invoices': 'invoices',
        'Tags': 'tags',
        'Customers': 'customers',
        'Footfall': 'Footfall'

    }

    for label, col in non_target_metrics.items():

        actual_value = today_metrics.get(

            col,
            0

        )

        ly_today_value = ly_today_metrics.get(

            col,
            0

        )

        ly_m_value = ly_m_metrics.get(

            col,
            0

        )

        ly_mtd_value = ly_mtd_metrics.get(

            col,
            0

        )

        vs_ly_pct = (

            safe_divide(

                actual_value - ly_today_value,
                ly_today_value

            ) * 100

        )

        rows.append({

            'Metric': label,

            'Target': 0,

            'LY Today': round(ly_today_value, 2),

            'Today': round(actual_value, 2),

            'LY M': round(ly_m_value, 2),

            'LY MTD': round(ly_mtd_value, 2),

            'Vs Target %': 0,

            'Vs LY %': round(vs_ly_pct, 2)

        })

    return pd.DataFrame(rows)

# ---------------------------------------------------
# MTD Table
# ---------------------------------------------------

def generate_mtd_table(

    prepared_data

):

    # ---------------------------------------------------
    # Metrics
    # ---------------------------------------------------

    current_metrics = aggregate_metrics(

        prepared_data['current_sales_df']

    )

    current_targets = aggregate_targets(

        prepared_data['current_targets_df']

    )

    month_targets = aggregate_targets(

        prepared_data['month_targets_df']

    )

    ly_m_metrics = aggregate_metrics(

        prepared_data['ly_m_sales_df']

    )

    ly_mtd_metrics = aggregate_metrics(

        prepared_data['ly_mtd_sales_df']

    )

    rows = []

    # ---------------------------------------------------
    # Target Metrics
    # ---------------------------------------------------

    for metric_key, config in METRIC_CONFIG.items():

        actual_value = current_metrics.get(

            config['actual_col'],
            0

        )

        # ---------------------------------------------------
        # Targets
        # ---------------------------------------------------

        mtd_target_value = current_targets.get(

            config['target_col'],
            0

        )

        month_target_value = month_targets.get(

            config['target_col'],
            0

        )

        # ---------------------------------------------------
        # LY Metrics
        # ---------------------------------------------------

        ly_m_value = ly_m_metrics.get(

            config['actual_col'],
            0

        )

        ly_mtd_value = ly_mtd_metrics.get(

            config['actual_col'],
            0

        )

        # ---------------------------------------------------
        # Variance %
        # ---------------------------------------------------

        vs_target_pct = (

            safe_divide(

                actual_value - mtd_target_value,

                mtd_target_value

            ) * 100

        )

        vs_ly_pct = (

            safe_divide(

                actual_value - ly_mtd_value,

                ly_mtd_value

            ) * 100

        )

        # ---------------------------------------------------
        # Append Row
        # ---------------------------------------------------

        rows.append({

            'Metric': config['label'],

            'Month Target': round(month_target_value, 2),

            'MTD Target': round(mtd_target_value, 2),

            'LY M': round(ly_m_value, 2),

            'LY MTD': round(ly_mtd_value, 2),

            'MTD': round(actual_value, 2),

            'Vs LY %': round(vs_ly_pct, 2),

            'Vs MTD Target %': round(vs_target_pct, 2)

        })

    # ---------------------------------------------------
    # Non Target Metrics
    # ---------------------------------------------------

    non_target_metrics = {

        'Invoices': 'invoices',
        'Tags': 'tags',
        'Customers': 'customers',
        'Footfall': 'Footfall'

    }

    for label, col in non_target_metrics.items():

        actual_value = current_metrics.get(

            col,
            0

        )

        ly_m_value = ly_m_metrics.get(

            col,
            0

        )

        ly_mtd_value = ly_mtd_metrics.get(

            col,
            0

        )

        vs_ly_pct = (

            safe_divide(

                actual_value - ly_mtd_value,
                ly_mtd_value

            ) * 100

        )

        rows.append({

            'Metric': label,

            'Month Target': 0,

            'MTD Target': 0,

            'LY M': round(ly_m_value, 2),

            'LY MTD': round(ly_mtd_value, 2),

            'MTD': round(actual_value, 2),

            'Vs LY %': round(vs_ly_pct, 2),

            'Vs MTD Target %': 0

        })

    return pd.DataFrame(rows)

# ---------------------------------------------------
# YTD Table
# ---------------------------------------------------

def generate_ytd_table(

    prepared_data

):

    # ---------------------------------------------------
    # Metrics
    # ---------------------------------------------------

    ty_td_metrics = aggregate_metrics(

        prepared_data['ty_td_sales_df']

    )

    ty_targets = aggregate_targets(

        prepared_data['ty_targets_df']

    )

    ytd_targets = aggregate_targets(

        prepared_data['ytd_targets_df']

    )

    ly_full_metrics = aggregate_metrics(

        prepared_data['ly_full_sales_df']

    )

    ly_td_metrics = aggregate_metrics(

        prepared_data['ly_td_sales_df']

    )

    rows = []

    # ---------------------------------------------------
    # Target Metrics
    # ---------------------------------------------------

    for metric_key, config in METRIC_CONFIG.items():

        actual_value = ty_td_metrics.get(

            config['actual_col'],
            0

        )

        ty_target_value = ty_targets.get(

            config['target_col'],
            0

        )

        ytd_target_value = ytd_targets.get(

            config['target_col'],
            0

        )

        ly_full_value = ly_full_metrics.get(

            config['actual_col'],
            0

        )

        ly_td_value = ly_td_metrics.get(

            config['actual_col'],
            0

        )

        vs_target_pct = (

            safe_divide(

                actual_value - ytd_target_value,
                ytd_target_value

            ) * 100

        )

        vs_ly_pct = (

            safe_divide(

                actual_value - ly_td_value,
                ly_td_value

            ) * 100

        )

        rows.append({

            'Metric': config['label'],

            'TY Target': round(ty_target_value, 2),

            'YTD Target': round(ytd_target_value, 2),

            'LY Full': round(ly_full_value, 2),

            'LY TD': round(ly_td_value, 2),

            'TY TD': round(actual_value, 2),

            'Vs LY TD %': round(vs_ly_pct, 2),

            'Vs YTD Target %': round(vs_target_pct, 2)

        })

    # ---------------------------------------------------
    # Non Target Metrics
    # ---------------------------------------------------

    non_target_metrics = {

        'Invoices': 'invoices',
        'Tags': 'tags',
        'Customers': 'customers',
        'Footfall': 'Footfall'

    }

    for label, col in non_target_metrics.items():

        actual_value = ty_td_metrics.get(

            col,
            0

        )

        ly_full_value = ly_full_metrics.get(

            col,
            0

        )

        ly_td_value = ly_td_metrics.get(

            col,
            0

        )

        vs_ly_pct = (

            safe_divide(

                actual_value - ly_td_value,
                ly_td_value

            ) * 100

        )

        rows.append({

            'Metric': label,

            'TY Target': 0,

            'YTD Target': 0,

            'LY Full': round(ly_full_value, 2),

            'LY TD': round(ly_td_value, 2),

            'TY TD': round(actual_value, 2),

            'Vs LY TD %': round(vs_ly_pct, 2),

            'Vs YTD Target %': 0

        })

    return pd.DataFrame(rows)

# ---------------------------------------------------
# Generate Export Data
# ---------------------------------------------------

def generate_export_dataframe(

    prepared_data,

    start_date,
    end_date,

    locations=None,
    rms=None,
    zms=None

):

    # ---------------------------------------------------
    # KPI Sections
    # ---------------------------------------------------

    kpi_sections = get_kpi_sections(

        prepared_data

    )

    # ---------------------------------------------------
    # Filters Export
    # ---------------------------------------------------

    filters_df = pd.DataFrame([

        {

            'Selected Start Date': start_date,

            'Selected End Date': end_date,

            'Locations': ', '.join(locations) if locations else 'ALL',

            'RMs': ', '.join(rms) if rms else 'ALL',

            'ZMs': ', '.join(zms) if zms else 'ALL'

        }

    ])

    # ---------------------------------------------------
    # Tables
    # ---------------------------------------------------

    today_table = generate_today_table(

        prepared_data

    )

    mtd_table = generate_mtd_table(

        prepared_data

    )

    ytd_table = generate_ytd_table(

        prepared_data

    )

    # ---------------------------------------------------
    # KPI Export
    # ---------------------------------------------------

    kpi_export_rows = []

    for section_name, kpis in kpi_sections.items():

        for kpi_name, value in kpis.items():

            kpi_export_rows.append({

                'Section': section_name,
                'KPI': kpi_name,
                'Value': round(value, 2)

            })

    kpi_export_df = pd.DataFrame(

        kpi_export_rows

    )

    # ---------------------------------------------------
    # Add Table Name
    # ---------------------------------------------------

    today_table.insert(

        0,
        'Table',
        'TODAY'

    )

    mtd_table.insert(

        0,
        'Table',
        'MTD'

    )

    ytd_table.insert(

        0,
        'Table',
        'YTD'

    )

    # ---------------------------------------------------
    # Merge Tables
    # ---------------------------------------------------

    combined_tables_df = pd.concat(

        [

            today_table,
            mtd_table,
            ytd_table

        ],

        ignore_index=True,
        sort=False

    )

    # ---------------------------------------------------
    # Final Export
    # ---------------------------------------------------

    final_export_df = pd.concat(

        [

            filters_df,

            kpi_export_df,

            combined_tables_df

        ],

        ignore_index=True,
        sort=False

    )

    return final_export_df

# ---------------------------------------------------
# Main Dashboard Generator
# ---------------------------------------------------

def generate_branch_health_dashboard_data(

    start_date,
    end_date,

    locations=None,
    rms=None,
    zms=None

):

    prepared_data = prepare_branch_health_data(

        start_date=start_date,
        end_date=end_date,

        locations=locations,
        rms=rms,
        zms=zms

    )

    kpi_sections = get_kpi_sections(

        prepared_data

    )

    today_table = generate_today_table(

        prepared_data

    )

    mtd_table = generate_mtd_table(

        prepared_data

    )

    ytd_table = generate_ytd_table(

        prepared_data

    )

    export_df = generate_export_dataframe(

        prepared_data=prepared_data,

        start_date=start_date,
        end_date=end_date,

        locations=locations,
        rms=rms,
        zms=zms

    )

    return {

        'kpi_sections': kpi_sections,

        'today_table': today_table,

        'mtd_table': mtd_table,

        'ytd_table': ytd_table,

        'export_df': export_df

    }