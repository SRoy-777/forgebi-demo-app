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

from backend.cache.data_cache import (
    merged_sales_df,
    tag_list_df
)

from backend.services.rls import (
    get_allowed_locations
)


# ---------------------------------------------------
# Prepare Stock Movement Data
# ---------------------------------------------------

def prepare_stock_movement_data(

    start_date,

    end_date,

    locations=None,

    counters=None,

    categories=None,

    sub_categories=None,

):

    # ---------------------------------------------------
    # Copy Cached Data
    # ---------------------------------------------------

    sales_df = merged_sales_df.copy()

    tag_df = tag_list_df.copy()


    # ---------------------------------------------------
    # RLS
    # ---------------------------------------------------

    try:

        allowed_locations = get_allowed_locations()

    except:

        allowed_locations = ['ALL']


    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']
            .isin(allowed_locations)

        ]


        tag_df = tag_df[

            tag_df['location_name']
            .isin(allowed_locations)

        ]


    # ---------------------------------------------------
    # Standardize Columns
    # ---------------------------------------------------

    sales_df['Location Name'] = (

        sales_df['Location Name']
        .astype(str)
        .str.strip()
        .str.upper()

    )

    tag_df['location_name'] = (

        tag_df['location_name']
        .astype(str)
        .str.strip()
        .str.upper()

    )


    sales_df['Counter'] = (

        sales_df['Counter']
        .astype(str)
        .str.strip()
        .str.upper()

    )

    tag_df['counter_code'] = (

        tag_df['counter_code']
        .astype(str)
        .str.strip()
        .str.upper()

    )


    # ---------------------------------------------------
    # Date Conversion
    # ---------------------------------------------------

    start_date = pd.to_datetime(start_date)

    end_date = pd.to_datetime(end_date)


    # ---------------------------------------------------
    # Filter Tag Received Date
    # ---------------------------------------------------

    tag_df = tag_df[

        tag_df['tag_received_date']
        .notna()

    ]


    tag_df = tag_df[

        (

            tag_df['tag_received_date']
            >= start_date

        )

        &

        (

            tag_df['tag_received_date']
            <= end_date

        )

    ]


    # ---------------------------------------------------
    # Filter Sales Date
    # ---------------------------------------------------

    sales_df = sales_df[

        (

            sales_df['Invoice Date']
            >= start_date

        )

        &

        (

            sales_df['Invoice Date']
            <= end_date

        )

    ]


    # ---------------------------------------------------
    # Sales Type Filter
    # ---------------------------------------------------

    sales_df = sales_df[

        sales_df['Sales Type']
        == 'Sales'

    ]


    # ---------------------------------------------------
    # Apply Filters
    # ---------------------------------------------------

    if locations:

        sales_df = sales_df[

            sales_df['Location Name']
            .isin(locations)

        ]

        tag_df = tag_df[

            tag_df['location_name']
            .isin(locations)

        ]


    if counters:

        sales_df = sales_df[

            sales_df['Counter']
            .isin(counters)

        ]

        tag_df = tag_df[

            tag_df['counter_code']
            .isin(counters)

        ]


    if categories:

        sales_df = sales_df[

            sales_df['Ornament Category Code']
            .isin(categories)

        ]

        tag_df = tag_df[

            tag_df['ornament_category_code']
            .isin(categories)

        ]


    if sub_categories:

        sales_df = sales_df[

            sales_df['Ornament Sub Category Code']
            .isin(sub_categories)

        ]

        tag_df = tag_df[

            tag_df['ornament_sub_category_code']
            .isin(sub_categories)

        ]


    return sales_df, tag_df

# ---------------------------------------------------
# Received Data
# ---------------------------------------------------

def get_received_data(tag_df):

    received_df = (

        tag_df

        .groupby(

            [

                'counter_code',

                'location_name',

                'ornament_category_code',

                'ornament_sub_category_code'

            ],

            as_index=False

        )

        .agg({

            'tag_no.': pd.Series.nunique,

            'net_weight': 'sum'

        })

    )


    received_df.rename(

        columns={

            'counter_code': 'Counter',

            'location_name': 'Location',

            'ornament_category_code': 'Category',

            'ornament_sub_category_code': 'Subcategory',

            'tag_no.': 'Pieces Bought',

            'net_weight': 'Weight Bought'

        },

        inplace=True

    )


    received_df['Weight Bought'] = (

        received_df['Weight Bought']
        .fillna(0)
        .round(2)

    )


    return received_df

# ---------------------------------------------------
# Sales Data
# ---------------------------------------------------

def get_sales_data(

    sales_df,

    counter_name

):

    # ---------------------------------------------------
    # Gemstone
    # ---------------------------------------------------

    if counter_name == 'GEMSTONE':

        sales_df = sales_df[

            (

                sales_df['Bom Item Type']

                == 'STONE_CT'

            )

            &

            (

                sales_df['Item Type Group']

                == 'NONE'

            )

        ]


        grouped_df = (

            sales_df

            .groupby(

                [

                    'Location Name',

                    'Ornament Category Code',

                    'Ornament Sub Category Code'

                ],

                as_index=False

            )

            .agg({

                'Tag No': pd.Series.nunique,

                'Bom Line Amount': 'sum'

            })

        )


        grouped_df.rename(

            columns={

                'Location Name': 'Location',

                'Ornament Category Code': 'Category',

                'Ornament Sub Category Code': 'Subcategory',

                'Tag No': 'Pieces Sold',

                'Bom Line Amount': 'Value Sold'

            },

            inplace=True

        )


        grouped_df['Value Sold'] = (

            grouped_df['Value Sold']

            .fillna(0)

            .round(0)

        )


        return grouped_df


    # ---------------------------------------------------
    # Standard Counter Filter
    # ---------------------------------------------------

    sales_df = sales_df[

        sales_df['Counter']

        == counter_name

    ]


    # ---------------------------------------------------
    # Diamond
    # ---------------------------------------------------

    if counter_name == 'DIAMOND':

        sales_df = sales_df[

            (

                sales_df['Bom UOM']

                == 'CTS'

            )

            &

            (

                sales_df['Bom Item Type']

                == 'DIAMOND'

            )

        ]


    # ---------------------------------------------------
    # Silver
    # ---------------------------------------------------

    elif counter_name == 'SILVER':

        sales_df = sales_df[

            (

                sales_df['Bom UOM']

                == 'GMS'

            )

            &

            (

                sales_df['Bom Item Type']

                == 'SILVER'

            )

            &

            (

                sales_df['Item Type Group']

                == 'SILVER'

            )

        ]


    # ---------------------------------------------------
    # Gold
    # ---------------------------------------------------

    else:

        sales_df = sales_df[

            (

                sales_df['Bom UOM']

                == 'GMS'

            )

            &

            (

                sales_df['Bom Item Type']

                == 'GOLD'

            )

        ]


    # ---------------------------------------------------
    # Grouping
    # ---------------------------------------------------

    grouped_df = (

        sales_df

        .groupby(

            [

                'Location Name',

                'Ornament Category Code',

                'Ornament Sub Category Code'

            ],

            as_index=False

        )

        .agg({

            'Tag No': pd.Series.nunique,

            'Bom Qty': 'sum',

            'Bom Line Amount': 'sum'

        })

    )


    grouped_df.rename(

        columns={

            'Location Name': 'Location',

            'Ornament Category Code': 'Category',

            'Ornament Sub Category Code': 'Subcategory',

            'Tag No': 'Pieces Sold',

            'Bom Qty': 'Weight Sold',

            'Bom Line Amount': 'Value Sold'

        },

        inplace=True

    )


    grouped_df['Weight Sold'] = (

        grouped_df['Weight Sold']

        .fillna(0)

        .round(2)

    )


    grouped_df['Value Sold'] = (

        grouped_df['Value Sold']

        .fillna(0)

        .round(0)

    )


    return grouped_df

# ---------------------------------------------------
# Generate Counter Table
# ---------------------------------------------------

def generate_counter_table(

    sales_df,

    tag_df,

    counter_name

):

    # ---------------------------------------------------
    # Received
    # ---------------------------------------------------

    received_df = get_received_data(tag_df)


    # ---------------------------------------------------
    # Counter Filter
    # ---------------------------------------------------

    received_df = received_df[

        received_df['Counter']

        == counter_name

    ]


    # ---------------------------------------------------
    # Sales
    # ---------------------------------------------------

    sales_grouped_df = get_sales_data(

        sales_df=sales_df,

        counter_name=counter_name

    )


    # ---------------------------------------------------
    # Merge
    # ---------------------------------------------------

    final_df = received_df.merge(

        sales_grouped_df,

        on=[

            'Location',

            'Category',

            'Subcategory'

        ],

        how='outer'

    )

    if final_df.empty:

        return pd.DataFrame()

    # ---------------------------------------------------
    # Cleanup Duplicate Counter Columns
    # ---------------------------------------------------

    if 'Counter_x' in final_df.columns:

        final_df.drop(
            columns=['Counter_x'],
            inplace=True
        )


    if 'Counter_y' in final_df.columns:

        final_df.drop(
            columns=['Counter_y'],
            inplace=True
        )

    # ---------------------------------------------------
    # Fill Counter
    # ---------------------------------------------------

    final_df['Counter'] = counter_name


    # ---------------------------------------------------
    # Fill Missing
    # ---------------------------------------------------

    numeric_cols = [

        'Pieces Bought',

        'Pieces Sold',

        'Weight Bought',

        'Weight Sold',

        'Value Sold'

    ]


    for col in numeric_cols:

        if col in final_df.columns:

            final_df[col] = (

                final_df[col]
                .fillna(0)

            )

    # ---------------------------------------------------
    # Standard Counter Filter
    # ---------------------------------------------------

    if counter_name not in ['SILVER']:

        sales_df = sales_df[

            sales_df['Counter']

            == counter_name

        ]

    # ---------------------------------------------------
    # Gemstone Handling
    # ---------------------------------------------------

    if counter_name == 'GEMSTONE':

        if 'Weight Bought' in final_df.columns:

            final_df.drop(
                columns=['Weight Bought'],
                inplace=True
            )


        if 'Weight Sold' in final_df.columns:

            final_df.drop(
                columns=['Weight Sold'],
                inplace=True
            )

    # ---------------------------------------------------
    # Empty Protection
    # ---------------------------------------------------

    if final_df.empty:

        return pd.DataFrame()


    # ---------------------------------------------------
    # Sort
    # ---------------------------------------------------

    final_df = final_df.sort_values(

        [

            'Location',

            'Category',

            'Subcategory'

        ]

    )


    # ---------------------------------------------------
    # Total Row
    # ---------------------------------------------------

    total_row = {}


    for col in final_df.columns:

        if col in [

            'Pieces Bought',

            'Pieces Sold',

            'Weight Bought',

            'Weight Sold',

            'Value Sold'

        ]:

            total_row[col] = (

                final_df[col]
                .sum()

            )

        else:

            total_row[col] = ''


    total_row['Location'] = 'TOTAL'


    final_df = pd.concat(

        [

            final_df,

            pd.DataFrame([total_row])

        ],

        ignore_index=True

    )


    return final_df

# ---------------------------------------------------
# Generate All Counter Tables
# ---------------------------------------------------

def generate_all_counter_tables(

    sales_df,

    tag_df

):

    available_counters = sorted(

        tag_df['counter_code']
        .dropna()
        .unique()

    )


    all_tables = {}


    for counter in available_counters:

        try:

            counter_df = generate_counter_table(

                sales_df=sales_df,

                tag_df=tag_df,

                counter_name=counter

            )


            if not counter_df.empty:

                all_tables[counter] = counter_df


        except Exception as e:

            print(

                f"{counter} Error: {e}"

            )


    return all_tables
