import pandas as pd


# ---------------------------------------------------
# Counter Order
# ---------------------------------------------------

COUNTER_ORDER = [

    'G-BANGLE',

    'G-NECKLACE',

    'G-CHAIN',

    'G-PR',

    'G-MISC',

    'G-COIN'

]


# ---------------------------------------------------
# Prepare Bucket Data
# ---------------------------------------------------

def prepare_bucket_data(

    sold_df,

    received_df,

    start_date,

    end_date,

    locations=None,

    counters=None,

    categories=None,

    sub_categories=None

):

    # ---------------------------------------------------
    # Date Conversion
    # ---------------------------------------------------

    sold_df['invoice_date'] = pd.to_datetime(

        sold_df['invoice_date'],

        errors='coerce'

    )


    received_df['tag_received_date'] = pd.to_datetime(

        received_df['tag_received_date'],

        errors='coerce'

    )


    # ---------------------------------------------------
    # Sold Date Filter
    # ---------------------------------------------------

    filtered_sold_df = sold_df[

        (

            sold_df['invoice_date']

            >= pd.to_datetime(start_date)

        )

        &

        (

            sold_df['invoice_date']

            <= pd.to_datetime(end_date)

        )

    ].copy()


    # ---------------------------------------------------
    # Received Date Filter
    # ---------------------------------------------------

    filtered_received_df = received_df[

        (

            received_df['tag_received_date']

            >= pd.to_datetime(start_date)

        )

        &

        (

            received_df['tag_received_date']

            <= pd.to_datetime(end_date)

        )

    ].copy()


    # ---------------------------------------------------
    # Existing DF
    # No Date Filter
    # ---------------------------------------------------

    existing_received_df = received_df.copy()


    # ---------------------------------------------------
    # Common Filter Helper
    # ---------------------------------------------------

    def apply_filters(df):

        if locations:

            df = df[

                df['location_name']

                .isin(locations)

            ]


        if counters:

            counter_col = (

                'counter'

                if 'counter' in df.columns

                else 'counter_code'

            )

            df = df[

                df[counter_col]

                .isin(counters)

            ]


        if categories:

            df = df[

                df['ornament_category_code']

                .isin(categories)

            ]


        if sub_categories:

            df = df[

                df['ornament_sub_category_code']

                .isin(sub_categories)

            ]


        return df


    # ---------------------------------------------------
    # Apply Filters
    # ---------------------------------------------------

    filtered_sold_df = apply_filters(

        filtered_sold_df

    )


    filtered_received_df = apply_filters(

        filtered_received_df

    )


    existing_received_df = apply_filters(

        existing_received_df

    )


    return (

        filtered_sold_df,

        filtered_received_df,

        existing_received_df

    )

# ---------------------------------------------------
# Generate KPI Data
# ---------------------------------------------------

def generate_bucket_kpis(

    sold_df,

    received_df,

    existing_received_df

):

    # ---------------------------------------------------
    # Sales KPI Base
    # ---------------------------------------------------

    sales_kpi_df = (

        sold_df

        .groupby(

            'subcat_basket',

            as_index=False

        )

        .agg({

            'tag_no': 'count',

            'bom_qty': 'sum'

        })

        .rename(

            columns={

                'tag_no': 'pcs_sold',

                'bom_qty': 'weight_sold'

            }

        )

    )

    # ---------------------------------------------------
    # Empty Check
    # ---------------------------------------------------

    if sales_kpi_df.empty:

        return {

            'sale': {},

            'received': {},

            'existing': {}

        }    


    # ---------------------------------------------------
    # Remove Zero Rows
    # ---------------------------------------------------

    sales_kpi_df = sales_kpi_df[

        (

            sales_kpi_df['pcs_sold']

            > 0

        )

        |

        (

            sales_kpi_df['weight_sold']

            > 0

        )

    ]

    # ---------------------------------------------------
    # Empty Check After Zero Removal
    # ---------------------------------------------------

    if sales_kpi_df.empty:

        return {

            'sale': {},

            'received': {},

            'existing': {}

        }

    # ---------------------------------------------------
    # Best / Worst Sales
    # ---------------------------------------------------

    best_pcs_bucket = (

        sales_kpi_df

        .sort_values(

            by='pcs_sold',

            ascending=False

        )

        .iloc[0]

    )


    best_weight_bucket = (

        sales_kpi_df

        .sort_values(

            by='weight_sold',

            ascending=False

        )

        .iloc[0]

    )


    worst_pcs_bucket = (

        sales_kpi_df

        .sort_values(

            by='pcs_sold',

            ascending=True

        )

        .iloc[0]

    )


    worst_weight_bucket = (

        sales_kpi_df

        .sort_values(

            by='weight_sold',

            ascending=True

        )

        .iloc[0]

    )


    # ---------------------------------------------------
    # Helper Function
    # ---------------------------------------------------

    def get_bucket_metrics(

        df,

        bucket_name,

        weight_col

    ):

        temp_df = df[

            df['subcat_basket']

            == bucket_name

        ]


        return {

            'pcs': len(temp_df),

            'weight': round(

                temp_df[weight_col]

                .sum(),

                2

            )

        }


    # ---------------------------------------------------
    # KPI Dictionary
    # ---------------------------------------------------

    kpi_data = {

        'sale': {

            'best_pcs': {

                'bucket': best_pcs_bucket['subcat_basket'],

                'value': int(

                    best_pcs_bucket['pcs_sold']

                )

            },

            'best_weight': {

                'bucket': best_weight_bucket['subcat_basket'],

                'value': round(

                    best_weight_bucket['weight_sold'],

                    2

                )

            },

            'worst_pcs': {

                'bucket': worst_pcs_bucket['subcat_basket'],

                'value': int(

                    worst_pcs_bucket['pcs_sold']

                )

            },

            'worst_weight': {

                'bucket': worst_weight_bucket['subcat_basket'],

                'value': round(

                    worst_weight_bucket['weight_sold'],

                    2

                )

            }

        }

    }


    # ---------------------------------------------------
    # Received KPIs
    # ---------------------------------------------------

    received_mapping = {

        'best_pcs': best_pcs_bucket['subcat_basket'],

        'best_weight': best_weight_bucket['subcat_basket'],

        'worst_pcs': worst_pcs_bucket['subcat_basket'],

        'worst_weight': worst_weight_bucket['subcat_basket']

    }


    received_kpis = {}


    for key, bucket_name in received_mapping.items():

        metrics = get_bucket_metrics(

            df=received_df,

            bucket_name=bucket_name,

            weight_col='net_weight'

        )


        received_kpis[key] = {

            'bucket': bucket_name,

            'pcs': metrics['pcs'],

            'weight': metrics['weight']

        }


    kpi_data['received'] = received_kpis


    # ---------------------------------------------------
    # Existing KPIs
    # ---------------------------------------------------

    existing_kpis = {}


    for key, bucket_name in received_mapping.items():

        metrics = get_bucket_metrics(

            df=existing_received_df,

            bucket_name=bucket_name,

            weight_col='net_weight'

        )


        existing_kpis[key] = {

            'bucket': bucket_name,

            'pcs': metrics['pcs'],

            'weight': metrics['weight']

        }


    kpi_data['existing'] = existing_kpis


    return kpi_data

# ---------------------------------------------------
# Generate Counter Table
# ---------------------------------------------------

def generate_bucket_table(

    sold_df,

    received_df,

    existing_received_df,

    counter_name

):

    # ---------------------------------------------------
    # Counter Filters
    # ---------------------------------------------------

    sold_counter_df = sold_df[

        sold_df['counter']

        == counter_name

    ].copy()


    received_counter_df = received_df[

        received_df['counter_code']

        == counter_name

    ].copy()


    existing_counter_df = existing_received_df[

        existing_received_df['counter_code']

        == counter_name

    ].copy()


    # ---------------------------------------------------
    # Sold Grouping
    # ---------------------------------------------------

    sold_grouped_df = (

        sold_counter_df

        .groupby(

            [

                'location_name',

                'counter',

                'ornament_category_code',

                'ornament_sub_category_code',

                'basket',

                'subcat_basket'

            ],

            as_index=False,

            observed=True

        )

        .agg({

            'tag_no': 'count',

            'bom_qty': 'sum'

        })

    )


    sold_grouped_df.rename(

        columns={

            'counter': 'Counter',

            'location_name': 'Location',

            'ornament_category_code': 'Category',

            'ornament_sub_category_code': 'Subcategory',

            'basket': 'Bucket',

            'subcat_basket': 'Subcat_Bucket',

            'tag_no': 'Pcs Sold',

            'bom_qty': 'Weight Sold'

        },

        inplace=True

    )



    # ---------------------------------------------------
    # Received Grouping
    # ---------------------------------------------------

    received_grouped_df = (

        received_counter_df

        .groupby(

            [

                'location_name',

                'counter_code',

                'ornament_category_code',

                'ornament_sub_category_code',

                'basket',

                'subcat_basket'

            ],

            as_index=False,

            observed=True

        )

        .agg({

            'tag_no.': 'count',

            'net_weight': 'sum'

        })

    )


    received_grouped_df.rename(

        columns={

            'counter_code': 'Counter',

            'location_name': 'Location',

            'ornament_category_code': 'Category',

            'ornament_sub_category_code': 'Subcategory',

            'basket': 'Bucket',

            'subcat_basket': 'Subcat_Bucket',

            'tag_no.': 'Pcs Rcv',

            'net_weight': 'Weight Rcv'

        },

        inplace=True

    )

    # ---------------------------------------------------
    # Existing Metrics
    # ---------------------------------------------------

    existing_grouped_df = (

        existing_counter_df

        .groupby(

            [

                'location_name',

                'counter_code',

                'ornament_category_code',

                'ornament_sub_category_code',

                'basket',

                'subcat_basket'

            ],

            as_index=False,

            observed=True

        )

        .agg({

            'tag_no.': 'count',

            'net_weight': 'sum'

        })

    )


    existing_grouped_df.rename(

        columns={

            'location_name': 'Location',

            'counter_code': 'Counter',

            'ornament_category_code': 'Category',

            'ornament_sub_category_code': 'Subcategory',

            'basket': 'Bucket',

            'subcat_basket': 'Subcat_Bucket',

            'tag_no.': 'Existing Pcs',

            'net_weight': 'Existing Weight'

        },

        inplace=True

    )

    # ---------------------------------------------------
    # Merge
    # ---------------------------------------------------

    merged_df = pd.merge(

        existing_grouped_df,

        received_grouped_df,

        how='outer',

        on=[

            'Location',

            'Counter',

            'Category',

            'Subcategory',

            'Bucket',

            'Subcat_Bucket'

        ]

    )

    merged_df = pd.merge(

        merged_df,

        sold_grouped_df,

        how='outer',

        on=[

            'Location',

            'Counter',

            'Category',

            'Subcategory',

            'Bucket',

            'Subcat_Bucket'

        ]

    )


    # ---------------------------------------------------
    # Fill Nulls
    # ---------------------------------------------------

    numeric_cols = [

        'Pcs Rcv',

        'Weight Rcv',

        'Pcs Sold',

        'Weight Sold',

        'Existing Pcs',

        'Existing Weight'

    ]


    for col in numeric_cols:

        if col in merged_df.columns:

            merged_df[col] = (

                merged_df[col]

                .fillna(0)

            )





    # ---------------------------------------------------
    # Rounding
    # ---------------------------------------------------

    weight_cols = [

        'Weight Rcv',

        'Weight Sold',

        'Existing Weight'

    ]


    for col in weight_cols:

        merged_df[col] = (

            merged_df[col]

            .round(2)

        )


    # ---------------------------------------------------
    # Sort
    # ---------------------------------------------------

    merged_df.sort_values(

        by=[

            'Location',

            'Category',

            'Subcategory',

            'Bucket'

        ],

        inplace=True

    )

    # ---------------------------------------------------
    # Total Row
    # ---------------------------------------------------

    total_row = {

        'Location': 'TOTAL',

        'Counter': '',

        'Category': '',

        'Subcategory': '',

        'Bucket': '',

        'Subcat_Bucket': '',

        'Pcs Rcv': merged_df['Pcs Rcv'].sum(),

        'Weight Rcv': round(

            merged_df['Weight Rcv'].sum(),

            2

        ),

        'Pcs Sold': merged_df['Pcs Sold'].sum(),

        'Weight Sold': round(

            merged_df['Weight Sold'].sum(),

            2

        ),

        'Existing Pcs': merged_df['Existing Pcs'].sum(),

        'Existing Weight': round(

            merged_df['Existing Weight'].sum(),

            2

        )

    }


    merged_df = pd.concat(

        [

            merged_df,

            pd.DataFrame([total_row])

        ],

        ignore_index=True

    )

    merged_df.reset_index(

        drop=True,

        inplace=True

    )

    return merged_df

# ---------------------------------------------------
# Generate All Counter Tables
# ---------------------------------------------------

def generate_all_bucket_tables(

    sold_df,

    received_df,

    existing_received_df

):

    all_tables = {}


    for counter in COUNTER_ORDER:

        try:

            counter_table = generate_bucket_table(

                sold_df=sold_df,

                received_df=received_df,

                existing_received_df=existing_received_df,

                counter_name=counter

            )


            if not counter_table.empty:

                all_tables[counter] = counter_table


        except Exception as e:

            print(

                f"{counter} Error : {e}"

            )


    return all_tables