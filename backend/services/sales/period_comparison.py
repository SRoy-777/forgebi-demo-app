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
    rm_zm_df

)

from backend.services.rls import (

    get_allowed_locations

)

# ---------------------------------------------------
# Safe Divide
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
# Prepare Data
# ---------------------------------------------------

def prepare_period_comparison_data(

    recent_start_date,
    recent_end_date,

    older_start_date,
    older_end_date,

    locations=None,
    rms=None,
    zms=None

):

        # ---------------------------------------------------
        # Copy Cached Data
        # ---------------------------------------------------

        sales_df = branch_daily_aggregate_df.copy()

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

        recent_start_date = pd.to_datetime(

            recent_start_date

        )

        recent_end_date = pd.to_datetime(

            recent_end_date

        )

        older_start_date = pd.to_datetime(

            older_start_date

        )

        older_end_date = pd.to_datetime(

            older_end_date

        )

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

        # ---------------------------------------------------
        # Recent Period
        # ---------------------------------------------------

        recent_df = sales_df[

            (

                sales_df['Date']
                >= recent_start_date

            )

            &

            (

                sales_df['Date']
                <= recent_end_date

            )

        ]

        # ---------------------------------------------------
        # Older Period
        # ---------------------------------------------------

        older_df = sales_df[

            (

                sales_df['Date']
                >= older_start_date

            )

            &

            (

                sales_df['Date']
                <= older_end_date

            )

        ]

        # ---------------------------------------------------
        # Operational Days
        # ---------------------------------------------------

        recent_days = recent_df['Date'].nunique()

        older_days = older_df['Date'].nunique()

        return {

            'recent_df': recent_df,

            'older_df': older_df,

            'recent_days': recent_days,

            'older_days': older_days

        }

# ---------------------------------------------------
# Aggregate Metrics
# ---------------------------------------------------

def aggregate_metrics(

    df

):

        if df.empty:

            return {

                'nsv': 0,
                'gold': 0,
                'gold_nsv': 0,

                'diamond_cts': 0,
                'diamond_nsv': 0,

                'silver_gms': 0,
                'silver_nsv': 0,

                'mohor_nsv': 0,
                'gemstone_nsv': 0,

                'invoices': 0,
                'tags': 0,
                'customers': 0,
                'scheme_count': 0,
                'scheme_payment': 0,
                'Footfall': 0,

                'Cash': 0,
                'Cheque': 0,
                'Card': 0,
                'UPI': 0,
                'NEFT/RTGS': 0

            }

        return {

            'nsv': df['nsv'].sum(),

            'gold': df['gold'].sum(),
            'gold_nsv': df['gold_nsv'].sum(),

            'diamond_cts': df['diamond_cts'].sum(),
            'diamond_nsv': df['diamond_nsv'].sum(),

            'silver_gms': df['silver_gms'].sum(),
            'silver_nsv': df['silver_nsv'].sum(),

            'mohor_nsv': df['mohor_nsv'].sum(),
            'gemstone_nsv': df['gemstone_nsv'].sum(),

            'invoices': df['invoices'].sum(),
            'tags': df['tags'].sum(),
            'customers': df['customers'].sum(),

            'scheme_count': df['scheme_count'].sum(),
            'scheme_payment': df['scheme_payment'].sum(),

            'Footfall': df['Footfall'].sum(),

            'Cash': df['Cash'].sum(),
            'Cheque': df['Cheque'].sum(),
            'Card': df['Card'].sum(),
            'UPI': df['UPI'].sum(),
            'NEFT/RTGS': df['NEFT/RTGS'].sum()

        }

# ---------------------------------------------------
# Generate Period Table
# ---------------------------------------------------

def generate_period_table(

    metrics,
    operational_days

):

    normalized_nsv = safe_divide(

        metrics['nsv'],
        operational_days

    )

    normalized_invoices = safe_divide(

        metrics['invoices'],
        operational_days

    )

    normalized_tags = safe_divide(

        metrics['tags'],
        operational_days

    )

    normalized_customers = safe_divide(

        metrics['customers'],
        operational_days

    )

    normalized_footfall = safe_divide(

        metrics['Footfall'],
        operational_days

    )

    rows = [

        {

            'Metric': 'NSV',

            'Absolute': metrics['nsv'],

            'Normalized': normalized_nsv

        },

        {

            'Metric': 'Gold_w',

            'Absolute': metrics['gold'],

            'Normalized': safe_divide(

                metrics['gold'],
                operational_days

            )

        },

        {

            'Metric': 'Silver_w',

            'Absolute': metrics['silver_gms'],

            'Normalized': safe_divide(

                metrics['silver_gms'],
                operational_days

            )

        },

        {

            'Metric': 'Diamond_Cts',

            'Absolute': metrics['diamond_cts'],

            'Normalized': safe_divide(

                metrics['diamond_cts'],
                operational_days

            )

        },

        {

            'Metric': 'Mohor_nsv',

            'Absolute': metrics['mohor_nsv'],

            'Normalized': safe_divide(

                metrics['mohor_nsv'],
                operational_days

            )

        },

        {

            'Metric': 'Gemstone_nsv',

            'Absolute': metrics['gemstone_nsv'],

            'Normalized': safe_divide(

                metrics['gemstone_nsv'],
                operational_days

            )

        },

        {

            'Metric': 'Scheme Count',

            'Absolute': metrics['scheme_count'],

            'Normalized': safe_divide(

                metrics['scheme_count'],
                operational_days

            )

        },

        {

            'Metric': 'Scheme Value',

            'Absolute': metrics['scheme_payment'],

            'Normalized': safe_divide(

                metrics['scheme_payment'],
                operational_days

            )

        },

        {

            'Metric': 'Tags',

            'Absolute': metrics['tags'],

            'Normalized': normalized_tags

        },

        {

            'Metric': 'Customers',

            'Absolute': metrics['customers'],

            'Normalized': normalized_customers

        },

        {

            'Metric': 'Footfall',

            'Absolute': metrics['Footfall'],

            'Normalized': normalized_footfall

        },

        {

            'Metric': 'Customer conversion%',

            'Absolute': (

                safe_divide(

                    metrics['customers'],
                    metrics['Footfall']

                ) * 100

            ),

            'Normalized': (

                safe_divide(

                    normalized_customers,
                    normalized_footfall

                ) * 100

            )

        },

        {

            'Metric': 'ATV',

            'Absolute': safe_divide(

                metrics['nsv'],
                metrics['invoices']

            ),

            'Normalized': safe_divide(

                normalized_nsv,
                normalized_invoices

            )

        },

        {

            'Metric': 'ASP',

            'Absolute': safe_divide(

                metrics['nsv'],
                metrics['tags']

            ),

            'Normalized': safe_divide(

                normalized_nsv,
                normalized_tags

            )

        },

        {

            'Metric': 'UPT',

            'Absolute': safe_divide(

                metrics['tags'],
                metrics['invoices']

            ),

            'Normalized': safe_divide(

                normalized_tags,
                normalized_invoices

            )

        }

    ]

    period_df = pd.DataFrame(rows)

    weight_metrics = [

        'Gold_w',
        'Silver_w',
        'Diamond_Cts',
        'UPT'

    ]

    percentage_metrics = [

        'Customer conversion%'

    ]

    for idx in period_df.index:

        metric = period_df.loc[idx, 'Metric']

        if metric in weight_metrics:

            period_df.loc[idx, 'Absolute'] = round(
                period_df.loc[idx, 'Absolute'],
                3
            )

            period_df.loc[idx, 'Normalized'] = round(
                period_df.loc[idx, 'Normalized'],
                3
            )

        elif metric in percentage_metrics:

            period_df.loc[idx, 'Absolute'] = round(
                period_df.loc[idx, 'Absolute'],
                2
            )

            period_df.loc[idx, 'Normalized'] = round(
                period_df.loc[idx, 'Normalized'],
                2
            )

        else:

            period_df.loc[idx, 'Absolute'] = round(
                period_df.loc[idx, 'Absolute'],
                0
            )

            period_df.loc[idx, 'Normalized'] = round(
                period_df.loc[idx, 'Normalized'],
                0
            )

    return period_df

# ---------------------------------------------------
# Generate Comparison Table
# ---------------------------------------------------

def generate_comparison_table(

    recent_df,
    older_df

):

        comparison_df = pd.merge(

            recent_df,
            older_df,

            on='Metric',

            suffixes=(

                '_Recent',
                '_Older'

            )

        )

        comparison_df['Absolute Difference'] = (

            comparison_df['Absolute_Recent']
            -

            comparison_df['Absolute_Older']

        )

        comparison_df['Normalized Difference'] = (

            comparison_df['Normalized_Recent']
            -

            comparison_df['Normalized_Older']

        )

        comparison_df['_abs_diff_numeric'] = (
            comparison_df['Absolute Difference']
        )

        comparison_df['_norm_diff_numeric'] = (
            comparison_df['Normalized Difference']
        )

        final_df = comparison_df[
            [
                'Metric',
                'Absolute Difference',
                'Normalized Difference',
                '_abs_diff_numeric',
                '_norm_diff_numeric'
            ]
        ]
        
        weight_metrics = [

            'Gold_w',
            'Silver_w',
            'Diamond_Cts',
            'UPT'

        ]

        percentage_metrics = [

            'Customer conversion%'

        ]

        for idx in final_df.index:

            metric = final_df.loc[idx, 'Metric']

            if metric in weight_metrics:

                final_df.loc[idx, 'Absolute Difference'] = round(

                    final_df.loc[idx, 'Absolute Difference'],

                    3

                )

                final_df.loc[idx, 'Normalized Difference'] = round(

                    final_df.loc[idx, 'Normalized Difference'],

                    3

                )

            elif metric in percentage_metrics:

                final_df.loc[idx, 'Absolute Difference'] = round(

                    final_df.loc[idx, 'Absolute Difference'],

                    2

                )

                final_df.loc[idx, 'Normalized Difference'] = round(

                    final_df.loc[idx, 'Normalized Difference'],

                    2

                )

            else:

                final_df.loc[idx, 'Absolute Difference'] = round(

                    final_df.loc[idx, 'Absolute Difference'],

                    0

                )

                final_df.loc[idx, 'Normalized Difference'] = round(

                    final_df.loc[idx, 'Normalized Difference'],

                    0

                )

        return final_df

# ---------------------------------------------------
# Export Data
# ---------------------------------------------------

def generate_export_dataframe(

    recent_table,
    older_table,
    comparison_table

):

        recent_table.insert(

            0,
            'Table',

            'RECENT'

        )

        older_table.insert(

            0,
            'Table',

            'OLDER'

        )

        comparison_table.insert(

                0,
                'Table',

                'COMPARISON'

            )

        comparison_table = comparison_table.drop(

            columns=[

                '_abs_diff_numeric',

                '_norm_diff_numeric'

            ],

            errors='ignore'

        )

        export_df = pd.concat(

            [

                comparison_table,
                recent_table,
                older_table

            ],

            ignore_index=True

        )

        return export_df

# ---------------------------------------------------
# Main Dashboard Generator
# ---------------------------------------------------

def generate_period_comparison_dashboard_data(

    recent_start_date,
    recent_end_date,

    older_start_date,
    older_end_date,

    locations=None,
    rms=None,
    zms=None

):

        prepared_data = prepare_period_comparison_data(

            recent_start_date=recent_start_date,
            recent_end_date=recent_end_date,

            older_start_date=older_start_date,
            older_end_date=older_end_date,

            locations=locations,
            rms=rms,
            zms=zms

        )

        # ---------------------------------------------------
        # Aggregate Metrics
        # ---------------------------------------------------

        recent_metrics = aggregate_metrics(

            prepared_data['recent_df']

        )

        older_metrics = aggregate_metrics(

            prepared_data['older_df']

        )

        # ---------------------------------------------------
        # Generate Tables
        # ---------------------------------------------------

        recent_table = generate_period_table(

            recent_metrics,

            prepared_data['recent_days']

        )

        older_table = generate_period_table(

            older_metrics,

            prepared_data['older_days']

        )

        comparison_table = generate_comparison_table(

            recent_table,
            older_table

        )

        # ---------------------------------------------------
        # Export
        # ---------------------------------------------------

        export_df = generate_export_dataframe(

            recent_table.copy(),
            older_table.copy(),
            comparison_table.copy()

        )

        return {

            'recent_table': recent_table,

            'older_table': older_table,

            'comparison_table': comparison_table,

            'export_df': export_df

        }