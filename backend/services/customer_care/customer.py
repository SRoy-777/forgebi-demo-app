from backend.cache.data_cache import (

    merged_sales_df,

    customer_list_df

)

import pandas as pd

from backend.services.rls import (
    get_allowed_locations
)


# ---------------------------------------------------
# Prepare Customer Data
# ---------------------------------------------------

def prepare_customer_data(

    start_date=None,

    end_date=None,

    locations=None,

    search_query=None

):

    # ---------------------------------------------------
    # Copy Data
    # ---------------------------------------------------

    df = merged_sales_df.copy()

    allowed_locations = get_allowed_locations()

    if 'ALL' not in allowed_locations:

        df = df[

            df['Location Name']

            .isin(allowed_locations)

        ]

    customer_df = customer_list_df.copy()


    # ---------------------------------------------------
    # Date Conversion
    # ---------------------------------------------------

    df['Invoice Date'] = pd.to_datetime(

        df['Invoice Date']

    )


    # ---------------------------------------------------
    # Default Latest Date & Date Filter
    # ---------------------------------------------------

    if not search_query:

        if not start_date and not end_date:

            latest_date = df['Invoice Date'].max()

            start_date = latest_date

            end_date = latest_date


        start_date = pd.to_datetime(start_date)

        end_date = pd.to_datetime(end_date)


        df = df[

            (df['Invoice Date'] >= start_date)

            &

            (df['Invoice Date'] <= end_date)

        ]


    # ---------------------------------------------------
    # Location Filter
    # ---------------------------------------------------

    if locations:

        df = df[

            df['Location Name'].isin(locations)

        ]


    # ---------------------------------------------------
    # Remove TAR Items
    # ---------------------------------------------------

    df = df[

        ~df['Item Name']

        .astype(str)

        .str.upper()

        .str.startswith('TAR')

    ]


    # ---------------------------------------------------
    # Sort
    # ---------------------------------------------------

    df = df.sort_values(

        by=[

            'Customer Code',

            'Invoice Date'

        ]

    )


    # ---------------------------------------------------
    # Compute NSV (sum of Bom Line Amount per Customer per Day)
    # ---------------------------------------------------

    df['Bom Line Amount'] = pd.to_numeric(df['Bom Line Amount'], errors='coerce').fillna(0)

    df['nsv'] = df.groupby(['Customer Code', 'Invoice Date'])['Bom Line Amount'].transform('sum').round(2)


    # ---------------------------------------------------
    # First Customer Visit Row
    # ---------------------------------------------------

    df = df.groupby(

        [

            'Customer Code',

            'Invoice Date'

        ],

        as_index=False

    ).first()

    # ---------------------------------------------------
    # Standardize Customer Codes
    # ---------------------------------------------------

    df['Customer Code'] = (

        df['Customer Code']
        .astype(str)
        .str.strip()

    )

    customer_df['customer_no.'] = (

        customer_df['customer_no.']
        .astype(str)
        .str.strip()

    )


    # ---------------------------------------------------
    # Customer Master Merge
    # ---------------------------------------------------

    final_df = pd.merge(

        df,

        customer_df,

        left_on='Customer Code',

        right_on='customer_no.',

        how='left'

    )


    # ---------------------------------------------------
    # Old / New Logic (Based on unique dates across entire history)
    # ---------------------------------------------------

    all_sales_df = merged_sales_df.copy()

    all_sales_df['Customer Code'] = all_sales_df['Customer Code'].astype(str).str.strip()

    all_sales_df['Invoice Date Only'] = pd.to_datetime(all_sales_df['Invoice Date']).dt.date


    customer_date_counts = all_sales_df.groupby('Customer Code')['Invoice Date Only'].nunique()

    old_customers = set(customer_date_counts[customer_date_counts > 1].index)


    final_df['customer_type'] = final_df[

        'Customer Code'

    ].apply(

        lambda x:

        'Old Customer'

        if x in old_customers

        else 'New Customer'

    )


    # ---------------------------------------------------
    # Final Columns
    # ---------------------------------------------------

    final_df = final_df[[

        'Location Name',

        'Customer Code',

        'Customer Name',

        'phone_no.',

        'Invoice Date',

        'nsv',

        'Item Name',

        'birth_date',

        'anniversary_date',

        'Sales Person Name',

        'customer_type'

    ]].copy()


    # ---------------------------------------------------
    # Search Filter
    # ---------------------------------------------------

    if search_query:

        search_query = str(search_query).strip()

        final_df = final_df[

            final_df['Customer Code'].astype(str).str.contains(search_query, case=False, na=False) |

            final_df['phone_no.'].astype(str).str.contains(search_query, case=False, na=False)

        ]


    # ---------------------------------------------------
    # Rename Columns
    # ---------------------------------------------------

    final_df.rename(

        columns={

            'Location Name': 'Location',

            'phone_no.': 'Phone Number',

            'birth_date': 'Birth Date',

            'anniversary_date': 'Anniversary Date',

            'customer_type': 'Customer Type',

            'nsv': 'NSV'

        },

        inplace=True

    )


    # ---------------------------------------------------
    # Date Formatting
    # ---------------------------------------------------

    final_df['Invoice Date'] = pd.to_datetime(

        final_df['Invoice Date']

    ).dt.strftime('%d-%b-%Y')


    final_df['Birth Date'] = pd.to_datetime(

        final_df['Birth Date'],

        errors='coerce'

    ).dt.strftime('%d-%b-%Y')


    final_df['Anniversary Date'] = pd.to_datetime(

        final_df['Anniversary Date'],

        errors='coerce'

    ).dt.strftime('%d-%b-%Y')


    return final_df


# ---------------------------------------------------
# KPI Logic
# ---------------------------------------------------

def get_customer_kpis(df):

    customers = len(df)

    unique_customers = df['Customer Code'].nunique()

    old_customers = len(

        df[

            df['Customer Type']

            == 'Old Customer'

        ]

    )

    new_customers = len(

        df[

            df['Customer Type']

            == 'New Customer'

        ]

    )

    return {

        'customers': customers,

        'unique_customers': unique_customers,

        'old_customers': old_customers,

        'new_customers': new_customers

    }