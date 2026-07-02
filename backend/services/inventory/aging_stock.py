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

from backend.cache.data_cache import tag_list_df
from backend.services.rls import (
    get_allowed_locations
)

# ---------------------------------------------------
# Prepare Aging Data
# ---------------------------------------------------

def prepare_aging_data(

    from_date,

    days,

    locations=None,

    counters=None,

    categories=None,

    sub_categories=None

):

    df = tag_list_df.copy()

    allowed_locations = get_allowed_locations()

    if 'ALL' not in allowed_locations:

        df = df[

            df['location_name']

            .isin(allowed_locations)

        ]


    # ---------------------------------------------------
    # Date Conversion
    # ---------------------------------------------------

    from_date = pd.to_datetime(from_date)


    # ---------------------------------------------------
    # Age Calculations
    # ---------------------------------------------------

    df['age'] = (

        from_date

        -

        df['tag_generated_date']

    ).dt.days


    df['shelf_life'] = (

        from_date

        -

        df['tag_received_date']

    ).dt.days


    # ---------------------------------------------------
    # Days Filter
    # ---------------------------------------------------

    df = df[

        df['age'] >= int(days)

    ]


    # ---------------------------------------------------
    # Location Filter
    # ---------------------------------------------------

    if locations:

        df = df[

            df['location_name'].isin(locations)

        ]


    # ---------------------------------------------------
    # Counter Filter
    # ---------------------------------------------------

    if counters:

        df = df[

            df['counter_code'].isin(counters)

        ]


    # ---------------------------------------------------
    # Category Filter
    # ---------------------------------------------------

    if categories:

        df = df[

            df['ornament_category_code'].isin(categories)

        ]


    # ---------------------------------------------------
    # Sub Category Filter
    # ---------------------------------------------------

    if sub_categories:

        df = df[

            df['ornament_sub_category_code'].isin(sub_categories)

        ]


    # ---------------------------------------------------
    # Final Columns
    # ---------------------------------------------------

    final_df = df[[

        'tag_no.',

        'location_code',

        'location_name',

        'counter_code',

        'ornament_category_code',

        'ornament_sub_category_code',

        'net_weight',

        'tag_generated_date',

        'tag_received_date',

        'age',

        'shelf_life'

    ]].copy()


    # ---------------------------------------------------
    # Rename Columns
    # ---------------------------------------------------

    final_df.rename(

        columns={

            'tag_no.': 'Tag No',

            'location_code': 'Location Code',

            'location_name': 'Location Name',

            'counter_code': 'Counter Code',

            'ornament_category_code': 'Ornament Category Code',

            'ornament_sub_category_code': 'Ornament Sub Category Code',

            'net_weight': 'NET Weight',

            'tag_generated_date': 'Tag Generated Date',

            'tag_received_date': 'Tag Received Date',

            'age': 'Age',

            'shelf_life': 'Shelf Life'

        },

        inplace=True

    )

    final_df['Tag Generated Date'] = (

        final_df['Tag Generated Date']

        .dt.strftime('%d-%b-%Y')

    )

    final_df['Tag Received Date'] = (

        final_df['Tag Received Date']

        .dt.strftime('%d-%b-%Y')

    )


    return final_df


# ---------------------------------------------------
# KPI Cards
# ---------------------------------------------------

def get_counter_kpis(df):

    kpi_df = (

        df.groupby('Counter Code')['Tag No']

        .nunique()

        .reset_index()

    )

    kpi_df.rename(

        columns={

            'Tag No': 'Tag Count'

        },

        inplace=True

    )

    return kpi_df