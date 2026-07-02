# backend/services/old_gold_service.py

import pandas as pd

from backend.cache.data_cache import (
    old_gold_df,
    rm_zm_df,
    merged_sales_df
)

from backend.services.rls import (
    get_allowed_locations
)

# ---------------------------------------------------
# Prepare Old Gold Data
# ---------------------------------------------------

def prepare_old_gold_data(

    start_date,
    end_date,

    locations=None,
    rms=None,
    zms=None,

    metals=None,
    transaction_types=None

):

    # ---------------------------------------------------
    # Copy Cached Data
    # ---------------------------------------------------

    df = old_gold_df.copy()

    rm_zm = rm_zm_df.copy()

    # ---------------------------------------------------
    # Date Conversion
    # ---------------------------------------------------

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

        df = df[

            df['location_name']
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

        df = df[

            df['location_name']
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

        df = df[

            df['location_name']
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

        df = df[

            df['location_name']
            .isin(locations)

        ]

    # ---------------------------------------------------
    # Metal Filter
    # ---------------------------------------------------

    if metals:

        metals = [

            str(i).strip().upper()

            for i in metals

        ]

        df = df[

            df['item_type']
            .isin(metals)

        ]

    # ---------------------------------------------------
    # Transaction Type Filter
    # ---------------------------------------------------

    if transaction_types:

        transaction_types = [

            str(i).strip().upper()

            for i in transaction_types

        ]

        df = df[

            df['transaction_type']
            .isin(transaction_types)

        ]

    # ---------------------------------------------------
    # Date Filter
    # ---------------------------------------------------

    df = df[

        (

            df['posting_date']
            >= start_date

        )

        &

        (

            df['posting_date']
            <= end_date

        )

    ]

    # ---------------------------------------------------
    # Customer Type Classification (Mapped from merged_sales)
    # ---------------------------------------------------
    sales_df = merged_sales_df.copy()
    sales_df['clean_cust'] = sales_df['Customer Code'].astype(str).str.replace('.0', '', regex=False).str.strip().str.upper()
    sales_df['invoice_date_only'] = pd.to_datetime(sales_df['Invoice Date']).dt.date
    cust_date_counts = sales_df.groupby('clean_cust')['invoice_date_only'].nunique()
    old_customers_set = set(cust_date_counts[cust_date_counts >= 3].index)

    df['clean_cust'] = df['customer_code'].astype(str).str.replace('.0', '', regex=False).str.strip().str.upper()
    df['customer_type'] = df['clean_cust'].apply(
        lambda x: 'Old Customer' if x in old_customers_set else 'New Customer'
    )
    df.drop(columns=['clean_cust'], inplace=True, errors='ignore')

    return df

# ---------------------------------------------------
# Generate KPI Data
# ---------------------------------------------------

def generate_kpis(df):

    if df.empty:

        return {

            'old_gold_value': 0,
            'unique_customers': 0,
            'old_customers': 0,
            'new_customers': 0

        }

    unique_custs_in_df = df[['customer_code', 'customer_type']].drop_duplicates(subset=['customer_code'])
    old_count = int((unique_custs_in_df['customer_type'] == 'Old Customer').sum())
    new_count = int((unique_custs_in_df['customer_type'] == 'New Customer').sum())

    return {

        'old_gold_value': df['amount'].sum(),

        'unique_customers': (

            df['customer_code']
            .nunique()

        ),

        'old_customers': old_count,

        'new_customers': new_count

    }

# ---------------------------------------------------
# Generate Table
# ---------------------------------------------------

def generate_old_gold_table(df):

    if df.empty:

        return pd.DataFrame()

    table_df = df[

        [

            'posting_date',

            'location_code',
            'location_name',

            'customer_code',
            'customer_name',

            'phone_number',

            'item_type',

            'net_weight',

            'amount',

            'sale_bill_amount',

            'transaction_type',

            'customer_type'

        ]

    ].copy()

    # ---------------------------------------------------
    # Rename Columns
    # ---------------------------------------------------

    table_df.columns = [

        'Posted Date',

        'Location Code',
        'Location Name',

        'Customer Code',
        'Customer Name',

        'Phone Number',

        'Metal',

        'Net Weight',

        'Old Gold Value',

        'Sale Bill Value',

        'Transaction Type',

        'Customer Type'

    ]

    # ---------------------------------------------------
    # Date Formatting
    # ---------------------------------------------------

    table_df['Posted Date'] = pd.to_datetime(

        table_df['Posted Date']

    ).dt.strftime('%d-%m-%Y')

    # ---------------------------------------------------
    # Total Row
    # ---------------------------------------------------

    total_row = {
        'Posted Date': '',

        'Location Code': '',
        'Location Name': 'TOTAL',

        'Customer Code': (

            table_df['Customer Code']
            .nunique()

        ),

        'Customer Name': '',

        'Phone Number': '',

        'Metal': '',

        'Net Weight': (

            table_df['Net Weight']
            .sum()

        ),

        'Old Gold Value': (

            table_df['Old Gold Value']
            .sum()

        ),

        'Sale Bill Value': (

            table_df['Sale Bill Value']
            .sum()

        ),

        'Transaction Type': '',

        'Customer Type': ''

    }

    table_df = pd.concat(

        [

            table_df,

            pd.DataFrame([total_row])

        ],

        ignore_index=True

    )

    return table_df

# ---------------------------------------------------
# Export Data
# ---------------------------------------------------

def generate_export_dataframe(

    kpis,
    table_df,

    start_date,
    end_date,

    locations=None,
    rms=None,
    zms=None,

    metals=None,
    transaction_types=None

):

    filters_df = pd.DataFrame([

        {

            'Start Date': start_date,
            'End Date': end_date,

            'Locations': ', '.join(locations) if locations else 'ALL',

            'RMs': ', '.join(rms) if rms else 'ALL',

            'ZMs': ', '.join(zms) if zms else 'ALL',

            'Metals': ', '.join(metals) if metals else 'ALL',

            'Transaction Types': (

                ', '.join(transaction_types)

                if transaction_types

                else 'ALL'

            )

        }

    ])

    kpi_df = pd.DataFrame([

        {

            'KPI': 'Old Gold Value',
            'Value': kpis['old_gold_value']

        },

        {

            'KPI': 'Unique Customers',
            'Value': kpis['unique_customers']

        },

        {

            'KPI': 'Old Customers',
            'Value': kpis['old_customers']

        },

        {

            'KPI': 'New Customers',
            'Value': kpis['new_customers']

        }

    ])

    export_df = pd.concat(

        [

            filters_df,
            kpi_df,
            table_df

        ],

        ignore_index=True,
        sort=False

    )

    return export_df

# ---------------------------------------------------
# Main Dashboard Generator
# ---------------------------------------------------

def generate_old_gold_dashboard_data(

    start_date,
    end_date,

    locations=None,
    rms=None,
    zms=None,

    metals=None,
    transaction_types=None

):

    filtered_df = prepare_old_gold_data(

        start_date=start_date,
        end_date=end_date,

        locations=locations,
        rms=rms,
        zms=zms,

        metals=metals,
        transaction_types=transaction_types

    )

    kpis = generate_kpis(

        filtered_df

    )

    table_df = generate_old_gold_table(

        filtered_df

    )

    export_df = generate_export_dataframe(

        kpis=kpis,
        table_df=table_df,

        start_date=start_date,
        end_date=end_date,

        locations=locations,
        rms=rms,
        zms=zms,

        metals=metals,
        transaction_types=transaction_types

    )

    return {

        'kpis': kpis,

        'table_df': table_df,

        'export_df': export_df

    }