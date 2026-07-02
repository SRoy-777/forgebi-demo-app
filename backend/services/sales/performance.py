
from backend.services.rls import (
    get_allowed_locations
)


from backend.cache.data_cache import (
    merged_sales_df,
    rm_zm_df,
    targets_df,
    scheme_df
)

import pandas as pd

# ---------------------------------
# Standardizing filters
# ---------------------------------

def validate_dates(start_date, end_date):

    if start_date is None or end_date is None:

        return None, None


    start_date = pd.to_datetime(start_date).date()

    end_date = pd.to_datetime(end_date).date()


    return start_date, end_date

def standardize_location_columns(sales_df, target_df, rz_df):

    sales_df['Location Name'] = (

        sales_df['Location Name']

        .astype(str)

        .str.strip()

        .str.upper()

    )

    rz_df['location'] = (

        rz_df['location']

        .astype(str)

        .str.strip()

        .str.upper()

    )

    target_df['location'] = (

        target_df['location']

        .astype(str)

        .str.strip()

        .str.upper()

    )

    return sales_df, target_df, rz_df

def standardize_sales_rz(sales_df, rz_df):

    if 'Location Name' in sales_df.columns:

        sales_df['Location Name'] = (

            sales_df['Location Name']

            .astype(str)

            .str.strip()

            .str.upper()

        )

    elif 'LocationName' in sales_df.columns:

        sales_df['LocationName'] = (

            sales_df['LocationName']

            .astype(str)

            .str.strip()

            .str.upper()

        )


    rz_df['location'] = (

        rz_df['location']

        .astype(str)

        .str.strip()

        .str.upper()

    )

    return sales_df, rz_df

#------------
# 1. NSV PERFORMANCE QUERY
#------------

import pandas as pd


def get_nsv_performance(start_date, end_date, rm=None, zm=None, location=None):

    rm_filter = ""
    zm_filter = ""
    location_filter = ""

    if rm:
        rm_filter = f"AND rz.rm = '{rm}'"

    if zm:
        zm_filter = f"AND rz.zm = '{zm}'"

    if location:
        location_filter = f"AND rz.location = '{location}'"

    # ---------------------------------------------------
    # Copy Cached Data
    # ---------------------------------------------------

    sales_df = merged_sales_df.copy()

    target_df = targets_df.copy()

    rz_df = rm_zm_df.copy()


    allowed_locations = get_allowed_locations()


    sales_df, target_df, rz_df = standardize_location_columns(

        sales_df,
        target_df,
        rz_df

    )


    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']

            .isin(allowed_locations)

        ]


        target_df = target_df[

            target_df['location']

            .isin(allowed_locations)

        ]


    # ---------------------------------------------------
    # Date Conversion
    # ---------------------------------------------------

    start_date, end_date = validate_dates(

        start_date,
        end_date

    )

    if start_date is None or end_date is None:

        return None


    # ---------------------------------------------------
    # Merge RM/ZM
    # ---------------------------------------------------

    sales_df = sales_df.merge(

        rz_df,

        left_on='Location Name',

        right_on='location',

        how='left'

    )


    target_df = target_df.merge(

        rz_df,

        on='location',

        how='left'

    )


    # ---------------------------------------------------
    # Apply Filters
    # ---------------------------------------------------

    if rm:

        sales_df = sales_df[
            sales_df['rm'] == rm
        ]

        target_df = target_df[
            target_df['rm'] == rm
        ]


    if zm:

        sales_df = sales_df[
            sales_df['zm'] == zm
        ]

        target_df = target_df[
            target_df['zm'] == zm
        ]


    if location:

        sales_df = sales_df[
            sales_df['location'] == location
        ]

        target_df = target_df[
            target_df['location'] == location
        ]


    # ---------------------------------------------------
    # Target Data
    # ---------------------------------------------------

    from_month = pd.to_datetime(start_date).replace(day=1)

    to_month = pd.to_datetime(end_date).replace(day=1)

    target_df = target_df[

        (target_df['month'] >= from_month)

        &

        (target_df['month'] <= to_month)

    ]


    target_data = (

        target_df

        .groupby('location', as_index=False)

        ['nsv']

        .sum()

    )

    target_data.rename(

        columns={
            'nsv': 'target_nsv'
        },

        inplace=True

    )


    # ---------------------------------------------------
    # Sales Data
    # ---------------------------------------------------

    sales_filtered = sales_df[

        (

            sales_df['Invoice Date'].dt.date
            >= start_date

        )

        &

        (

            sales_df['Invoice Date'].dt.date
            <= end_date

        )

    ]


    today_sales = (

        sales_filtered[

            sales_filtered['Invoice Date']
            .dt.date

            ==

            end_date

        ]

        .groupby(
            'Location Name',
            as_index=False
        )

        ['Bom Line Amount']

        .sum()

    )

    today_sales.rename(

        columns={

            'Location Name': 'location',

            'Bom Line Amount': 'today_nsv'

        },

        inplace=True

    )


    mtd_sales = (

        sales_filtered

        .groupby(
            'Location Name',
            as_index=False
        )

        ['Bom Line Amount']

        .sum()

    )

    mtd_sales.rename(

        columns={

            'Location Name': 'location',

            'Bom Line Amount': 'mtd_nsv'

        },

        inplace=True

    )


    # ---------------------------------------------------
    # Merge Final
    # ---------------------------------------------------

    df = target_data.merge(

        today_sales,

        on='location',

        how='left'

    )

    df = df.merge(

        mtd_sales,

        on='location',

        how='left'

    )


    df.fillna(0, inplace=True)


    # ---------------------------------------------------
    # Metrics
    # ---------------------------------------------------

    days_passed = end_date.day


    df['run_rate'] = (

        df['mtd_nsv']
        /
        days_passed

    ).round(0)


    import calendar

    total_days = calendar.monthrange(
        end_date.year,
        end_date.month
    )[1]


    remaining_days = max(
    total_days - end_date.day,
    1
    )


    df['required_run_rate'] = (

        (

            df['target_nsv']
            -
            df['mtd_nsv']

        )

        /

        remaining_days

    ).fillna(0).round(0)


    # ---------------------------------------------------
    # Final Columns
    # ---------------------------------------------------

    # Merge with location code
    code_map = rz_df[['location', 'code']].drop_duplicates()
    df = df.merge(code_map, on='location', how='left')

    df = df[[
        'code',
        'location',
        'target_nsv',
        'today_nsv',
        'run_rate',
        'mtd_nsv',
        'required_run_rate'
    ]]

    df = df.sort_values(
        'code',
        na_position='last'
    )


    return df    


#------------
# 2. GOLD PERFORMANCE QUERY
#------------

import pandas as pd


def get_gold_performance(start_date, end_date, rm=None, zm=None, location=None):

    rm_filter = ""
    zm_filter = ""
    location_filter = ""

    if rm:
        rm_filter = f"AND rz.rm = '{rm}'"

    if zm:
        zm_filter = f"AND rz.zm = '{zm}'"

    if location:
        location_filter = f"AND rz.location = '{location}'"



    # ---------------------------------------------------
    # Copy Cached Data
    # ---------------------------------------------------

    sales_df = merged_sales_df.copy()

    target_df = targets_df.copy()

    rz_df = rm_zm_df.copy()


    sales_df, target_df, rz_df = standardize_location_columns(

        sales_df,
        target_df,
        rz_df

    )


    allowed_locations = get_allowed_locations()


    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']

            .isin(allowed_locations)

        ]


        target_df = target_df[

            target_df['location']

            .isin(allowed_locations)

        ]



    # ---------------------------------------------------
    # Date Conversion
    # ---------------------------------------------------

    start_date, end_date = validate_dates(

        start_date,
        end_date

    )

    if start_date is None or end_date is None:

        return None

    # ---------------------------------------------------
    # Merge RM/ZM
    # ---------------------------------------------------

    sales_df = sales_df.merge(

        rz_df,

        left_on='Location Name',

        right_on='location',

        how='left'

    )

    target_df = target_df.merge(

        rz_df,

        on='location',

        how='left'

    )


    # ---------------------------------------------------
    # Gold Filter
    # ---------------------------------------------------

    sales_df = sales_df[

        (sales_df['Bom UOM'] == 'GMS')

        &

        (sales_df['Bom Item Type'] == 'GOLD')

    ]


    # ---------------------------------------------------
    # Apply Filters
    # ---------------------------------------------------

    if rm:

        sales_df = sales_df[
            sales_df['rm'] == rm
        ]

        target_df = target_df[
            target_df['rm'] == rm
        ]


    if zm:

        sales_df = sales_df[
            sales_df['zm'] == zm
        ]

        target_df = target_df[
            target_df['zm'] == zm
        ]


    if location:

        sales_df = sales_df[
            sales_df['location'] == location
        ]

        target_df = target_df[
            target_df['location'] == location
        ]


    # ---------------------------------------------------
    # Target Data
    # ---------------------------------------------------

    from_month = pd.to_datetime(start_date).replace(day=1)

    to_month = pd.to_datetime(end_date).replace(day=1)

    target_df = target_df[

        (target_df['month'] >= from_month)

        &

        (target_df['month'] <= to_month)

    ]


    target_data = (

        target_df

        .groupby('location', as_index=False)

        ['gold_w']

        .sum()

    )

    target_data.rename(

        columns={
            'gold_w': 'target_gold'
        },

        inplace=True

    )


    # ---------------------------------------------------
    # Sales Data
    # ---------------------------------------------------

    sales_filtered = sales_df[

        (

            sales_df['Invoice Date'].dt.date
            >= start_date

        )

        &

        (

            sales_df['Invoice Date'].dt.date
            <= end_date

        )

    ]


    today_sales = (

        sales_filtered[

            sales_filtered['Invoice Date']
            .dt.date

            ==

            end_date

        ]

        .groupby(
            'Location Name',
            as_index=False
        )

        ['Bom Qty']

        .sum()

    )

    today_sales.rename(

        columns={

            'Location Name': 'location',

            'Bom Qty': 'today_gold'

        },

        inplace=True

    )


    mtd_sales = (

        sales_filtered

        .groupby(
            'Location Name',
            as_index=False
        )

        ['Bom Qty']

        .sum()

    )

    mtd_sales.rename(

        columns={

            'Location Name': 'location',

            'Bom Qty': 'mtd_gold'

        },

        inplace=True

    )


    # ---------------------------------------------------
    # Merge Final
    # ---------------------------------------------------

    df = target_data.merge(

        today_sales,

        on='location',

        how='left'

    )

    df = df.merge(

        mtd_sales,

        on='location',

        how='left'

    )


    df.fillna(0, inplace=True)


    # ---------------------------------------------------
    # Metrics
    # ---------------------------------------------------

    days_passed = end_date.day


    df['run_rate'] = (

        df['mtd_gold']
        /
        days_passed

    ).round(2)


    import calendar

    total_days = calendar.monthrange(
        end_date.year,
        end_date.month
    )[1]


    remaining_days = max(
        total_days - end_date.day,
    1
    )


    df['required_run_rate'] = (

        (

            df['target_gold']
            -
            df['mtd_gold']

        )

        /

        remaining_days

    ).fillna(0).round(2)


    # ---------------------------------------------------
    # Final Columns
    # ---------------------------------------------------

    # Merge with location code
    code_map = rz_df[['location', 'code']].drop_duplicates()
    df = df.merge(code_map, on='location', how='left')

    df = df[[
        'code',
        'location',
        'target_gold',
        'today_gold',
        'run_rate',
        'mtd_gold',
        'required_run_rate'
    ]]

    df = df.sort_values(
        'code',
        na_position='last'
    )


    return df



#------------
# 3. SILVER PERFORMANCE QUERY
#------------

import pandas as pd



def get_silver_performance(start_date, end_date, rm=None, zm=None, location=None):

    rm_filter = ""
    zm_filter = ""
    location_filter = ""

    if rm:
        rm_filter = f"AND rz.rm = '{rm}'"

    if zm:
        zm_filter = f"AND rz.zm = '{zm}'"

    if location:
        location_filter = f"AND rz.location = '{location}'"



    # ---------------------------------------------------
    # Copy Cached Data
    # ---------------------------------------------------

    sales_df = merged_sales_df.copy()

    target_df = targets_df.copy()

    rz_df = rm_zm_df.copy()


    sales_df, target_df, rz_df = standardize_location_columns(

        sales_df,
        target_df,
        rz_df

    )


    allowed_locations = get_allowed_locations()


    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']

            .isin(allowed_locations)

        ]


        target_df = target_df[

            target_df['location']

            .isin(allowed_locations)

        ]



    # ---------------------------------------------------
    # Date Conversion
    # ---------------------------------------------------

    start_date, end_date = validate_dates(

        start_date,
        end_date

    )

    if start_date is None or end_date is None:

        return None

    # ---------------------------------------------------
    # Merge RM/ZM
    # ---------------------------------------------------

    sales_df = sales_df.merge(

        rz_df,

        left_on='Location Name',

        right_on='location',

        how='left'

    )

    target_df = target_df.merge(

        rz_df,

        on='location',

        how='left'

    )


    # ---------------------------------------------------
    # Silver Filter
    # ---------------------------------------------------

    sales_df = sales_df[

        (sales_df['Bom UOM'] == 'GMS')

        &

        (sales_df['Bom Item Type'] == 'SILVER')

        &

        (sales_df['Item Type Group'] == 'SILVER')

    ]


    # ---------------------------------------------------
    # Apply Filters
    # ---------------------------------------------------

    if rm:

        sales_df = sales_df[
            sales_df['rm'] == rm
        ]

        target_df = target_df[
            target_df['rm'] == rm
        ]


    if zm:

        sales_df = sales_df[
            sales_df['zm'] == zm
        ]

        target_df = target_df[
            target_df['zm'] == zm
        ]


    if location:

        sales_df = sales_df[
            sales_df['location'] == location
        ]

        target_df = target_df[
            target_df['location'] == location
        ]


    # ---------------------------------------------------
    # Target Data
    # ---------------------------------------------------

    from_month = pd.to_datetime(start_date).replace(day=1)

    to_month = pd.to_datetime(end_date).replace(day=1)

    target_df = target_df[

        (target_df['month'] >= from_month)

        &

        (target_df['month'] <= to_month)

    ]


    target_data = (

        target_df

        .groupby('location', as_index=False)

        ['silver_w']

        .sum()

    )

    target_data.rename(

        columns={
            'silver_w': 'target_silver'
        },

        inplace=True

    )


    # ---------------------------------------------------
    # Sales Data
    # ---------------------------------------------------

    sales_filtered = sales_df[

        (

            sales_df['Invoice Date'].dt.date
            >= start_date

        )

        &

        (

            sales_df['Invoice Date'].dt.date
            <= end_date

        )

    ]


    today_sales = (

        sales_filtered[

            sales_filtered['Invoice Date']
            .dt.date

            ==

            end_date

        ]

        .groupby(
            'Location Name',
            as_index=False
        )

        ['Bom Qty']

        .sum()

    )

    today_sales.rename(

        columns={

            'Location Name': 'location',

            'Bom Qty': 'today_silver'

        },

        inplace=True

    )


    mtd_sales = (

        sales_filtered

        .groupby(
            'Location Name',
            as_index=False
        )

        ['Bom Qty']

        .sum()

    )

    mtd_sales.rename(

        columns={

            'Location Name': 'location',

            'Bom Qty': 'mtd_silver'

        },

        inplace=True

    )


    # ---------------------------------------------------
    # Merge Final
    # ---------------------------------------------------

    df = target_data.merge(

        today_sales,

        on='location',

        how='left'

    )

    df = df.merge(

        mtd_sales,

        on='location',

        how='left'

    )


    df.fillna(0, inplace=True)


    # ---------------------------------------------------
    # Metrics
    # ---------------------------------------------------

    days_passed = end_date.day


    df['run_rate'] = (

        df['mtd_silver']
        /
        days_passed

    ).round(2)


    import calendar

    total_days = calendar.monthrange(
        end_date.year,
        end_date.month
    )[1]


    remaining_days = max(
    total_days - end_date.day,
    1
    )


    df['required_run_rate'] = (

        (

            df['target_silver']
            -
            df['mtd_silver']

        )

        /

        remaining_days

    ).fillna(0).round(2)


    # ---------------------------------------------------
    # Final Columns
    # ---------------------------------------------------

    # Merge with location code
    code_map = rz_df[['location', 'code']].drop_duplicates()
    df = df.merge(code_map, on='location', how='left')

    df = df[[
        'code',
        'location',
        'target_silver',
        'today_silver',
        'run_rate',
        'mtd_silver',
        'required_run_rate'
    ]]

    df = df.sort_values(
        'code',
        na_position='last'
    )


    return df


#------------
# 4. DIAMOND PERFORMANCE QUERY
#------------

import pandas as pd



def get_diamond_performance(start_date, end_date, rm=None, zm=None, location=None):

    rm_filter = ""
    zm_filter = ""
    location_filter = ""

    if rm:
        rm_filter = f"AND rz.rm = '{rm}'"

    if zm:
        zm_filter = f"AND rz.zm = '{zm}'"

    if location:
        location_filter = f"AND rz.location = '{location}'"



    # ---------------------------------------------------
    # Copy Cached Data
    # ---------------------------------------------------

    sales_df = merged_sales_df.copy()

    target_df = targets_df.copy()

    rz_df = rm_zm_df.copy()


    sales_df, target_df, rz_df = standardize_location_columns(

        sales_df,
        target_df,
        rz_df

    )


    allowed_locations = get_allowed_locations()


    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']

            .isin(allowed_locations)

        ]


        target_df = target_df[

            target_df['location']

            .isin(allowed_locations)

        ]



    # ---------------------------------------------------
    # Date Conversion
    # ---------------------------------------------------

    start_date, end_date = validate_dates(

        start_date,
        end_date

    )

    if start_date is None or end_date is None:

        return None


    # ---------------------------------------------------
    # Merge RM/ZM
    # ---------------------------------------------------

    sales_df = sales_df.merge(

        rz_df,

        left_on='Location Name',

        right_on='location',

        how='left'

    )

    target_df = target_df.merge(

        rz_df,

        on='location',

        how='left'

    )


    # ---------------------------------------------------
    # Diamond Filter
    # ---------------------------------------------------

    sales_df = sales_df[

        (sales_df['Bom UOM'] == 'CTS')

        &

        (sales_df['Bom Item Type'] == 'DIAMOND')

    ]


    # ---------------------------------------------------
    # Apply Filters
    # ---------------------------------------------------

    if rm:

        sales_df = sales_df[
            sales_df['rm'] == rm
        ]

        target_df = target_df[
            target_df['rm'] == rm
        ]


    if zm:

        sales_df = sales_df[
            sales_df['zm'] == zm
        ]

        target_df = target_df[
            target_df['zm'] == zm
        ]


    if location:

        sales_df = sales_df[
            sales_df['location'] == location
        ]

        target_df = target_df[
            target_df['location'] == location
        ]


    # ---------------------------------------------------
    # Target Data
    # ---------------------------------------------------

    from_month = pd.to_datetime(start_date).replace(day=1)

    to_month = pd.to_datetime(end_date).replace(day=1)

    target_df = target_df[

        (target_df['month'] >= from_month)

        &

        (target_df['month'] <= to_month)

    ]


    target_data = (

        target_df

        .groupby('location', as_index=False)

        ['diamond_cts']

        .sum()

    )

    target_data.rename(

        columns={
            'diamond_cts': 'target_diamond'
        },

        inplace=True

    )


    # ---------------------------------------------------
    # Sales Data
    # ---------------------------------------------------

    sales_filtered = sales_df[

        (

            sales_df['Invoice Date'].dt.date
            >= start_date

        )

        &

        (

            sales_df['Invoice Date'].dt.date
            <= end_date

        )

    ]


    today_sales = (

        sales_filtered[

            sales_filtered['Invoice Date']
            .dt.date

            ==

            end_date

        ]

        .groupby(
            'Location Name',
            as_index=False
        )

        .agg({

            'Bom Qty': 'sum',

            'Bom Line Amount': 'sum'

        })

    )

    today_sales.rename(

        columns={

            'Location Name': 'location',

            'Bom Qty': 'today_diamond',

            'Bom Line Amount': 'today_diamond_nsv'

        },

        inplace=True

    )


    mtd_sales = (

        sales_filtered

        .groupby(
            'Location Name',
            as_index=False
        )

        .agg({

            'Bom Qty': 'sum',

            'Bom Line Amount': 'sum'

        })

    )

    mtd_sales.rename(

        columns={

            'Location Name': 'location',

            'Bom Qty': 'mtd_diamond',

            'Bom Line Amount': 'mtd_diamond_nsv'

        },

        inplace=True

    )


    # ---------------------------------------------------
    # Merge Final
    # ---------------------------------------------------

    df = target_data.merge(

        today_sales,

        on='location',

        how='left'

    )

    df = df.merge(

        mtd_sales,

        on='location',

        how='left'

    )


    df.fillna(0, inplace=True)


    # ---------------------------------------------------
    # Metrics
    # ---------------------------------------------------

    days_passed = end_date.day


    df['run_rate'] = (

        df['mtd_diamond']
        /
        days_passed

    ).round(2)


    import calendar

    total_days = calendar.monthrange(
        end_date.year,
        end_date.month
    )[1]


    remaining_days = max(
    total_days - end_date.day,
    1
    )


    df['required_run_rate'] = (

        (

            df['target_diamond']
            -
            df['mtd_diamond']

        )

        /

        remaining_days

    ).fillna(0).round(2)


    # ---------------------------------------------------
    # Final Columns
    # ---------------------------------------------------

    # Merge with location code
    code_map = rz_df[['location', 'code']].drop_duplicates()
    df = df.merge(code_map, on='location', how='left')

    df = df[[
        'code',
        'location',
        'target_diamond',
        'today_diamond',
        'run_rate',
        'mtd_diamond',
        'required_run_rate',
        'today_diamond_nsv',
        'mtd_diamond_nsv'
    ]]

    df = df.sort_values(
        'code',
        na_position='last'
    )


    return df



#------------
# 5. GEMSTONE PERFORMANCE QUERY
#------------

import pandas as pd



def get_gemstone_performance(start_date, end_date, rm=None, zm=None, location=None):

    rm_filter = ""
    zm_filter = ""
    location_filter = ""

    if rm:
        rm_filter = f"AND rz.rm = '{rm}'"

    if zm:
        zm_filter = f"AND rz.zm = '{zm}'"

    if location:
        location_filter = f"AND rz.location = '{location}'"


    sales_df = merged_sales_df.copy()

    target_df = targets_df.copy()

    rz_df = rm_zm_df.copy()


    sales_df, target_df, rz_df = standardize_location_columns(

        sales_df,
        target_df,
        rz_df

    )


    allowed_locations = get_allowed_locations()


    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']

            .isin(allowed_locations)

        ]


        target_df = target_df[

            target_df['location']

            .isin(allowed_locations)

        ]


    start_date, end_date = validate_dates(

        start_date,
        end_date

    )

    if start_date is None or end_date is None:

        return None

    sales_df = sales_df.merge(
        rz_df,
        left_on='Location Name',
        right_on='location',
        how='left'
    )

    target_df = target_df.merge(
        rz_df,
        on='location',
        how='left'
    )

    sales_df = sales_df[
        (sales_df['Bom Item Type'] == 'STONE_CT')
        &
        (sales_df['Item Type Group'] == 'NONE')
    ]

    if rm:
        sales_df = sales_df[sales_df['rm'] == rm]
        target_df = target_df[target_df['rm'] == rm]

    if zm:
        sales_df = sales_df[sales_df['zm'] == zm]
        target_df = target_df[target_df['zm'] == zm]

    if location:
        sales_df = sales_df[sales_df['location'] == location]
        target_df = target_df[target_df['location'] == location]

    from_month = pd.to_datetime(start_date).replace(day=1)

    to_month = pd.to_datetime(end_date).replace(day=1)

    target_df = target_df[

        (target_df['month'] >= from_month)

        &

        (target_df['month'] <= to_month)

    ]

    target_data = (
        target_df
        .groupby('location', as_index=False)
        ['gemstone_nsv']
        .sum()
    )

    target_data.rename(
        columns={
            'gemstone_nsv': 'target_gemstone'
        },
        inplace=True
    )

    sales_filtered = sales_df[
        (sales_df['Invoice Date'].dt.date >= start_date)
        &
        (sales_df['Invoice Date'].dt.date <= end_date)
    ]

    today_sales = (
        sales_filtered[
            sales_filtered['Invoice Date'].dt.date
            ==
            end_date
        ]
        .groupby('Location Name', as_index=False)
        ['Bom Line Amount']
        .sum()
    )

    today_sales.rename(
        columns={
            'Location Name': 'location',
            'Bom Line Amount': 'today_gemstone'
        },
        inplace=True
    )

    mtd_sales = (
        sales_filtered
        .groupby('Location Name', as_index=False)
        ['Bom Line Amount']
        .sum()
    )

    mtd_sales.rename(
        columns={
            'Location Name': 'location',
            'Bom Line Amount': 'mtd_gemstone'
        },
        inplace=True
    )

    df = target_data.merge(
        today_sales,
        on='location',
        how='left'
    )

    df = df.merge(
        mtd_sales,
        on='location',
        how='left'
    )

    df.fillna(0, inplace=True)

    days_passed = end_date.day

    df['run_rate'] = (
        df['mtd_gemstone']
        /
        days_passed
    ).round(0)

    import calendar

    total_days = calendar.monthrange(
        end_date.year,
        end_date.month
    )[1]

    remaining_days = max(
    total_days - end_date.day,
    1
    )

    df['required_run_rate'] = (
        (
            df['target_gemstone']
            -
            df['mtd_gemstone']
        )
        /
        remaining_days
    ).fillna(0).round(0)

    # Merge with location code
    code_map = rz_df[['location', 'code']].drop_duplicates()
    df = df.merge(code_map, on='location', how='left')

    df = df[[
        'code',
        'location',
        'target_gemstone',
        'today_gemstone',
        'run_rate',
        'mtd_gemstone',
        'required_run_rate'
    ]]

    df = df.sort_values(
        'code',
        na_position='last'
    )

    return df


#------------
# 6. MOHOR PERFORMANCE QUERY
#------------

import pandas as pd



def get_mohor_performance(start_date, end_date, rm=None, zm=None, location=None):

    rm_filter = ""
    zm_filter = ""
    location_filter = ""

    if rm:
        rm_filter = f"AND rz.rm = '{rm}'"

    if zm:
        zm_filter = f"AND rz.zm = '{zm}'"

    if location:
        location_filter = f"AND rz.location = '{location}'"


    sales_df = merged_sales_df.copy()

    target_df = targets_df.copy()

    rz_df = rm_zm_df.copy()


    sales_df, target_df, rz_df = standardize_location_columns(

        sales_df,
        target_df,
        rz_df

    )


    allowed_locations = get_allowed_locations()


    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']

            .isin(allowed_locations)

        ]


        target_df = target_df[

            target_df['location']

            .isin(allowed_locations)

        ]


    start_date, end_date = validate_dates(

        start_date,
        end_date

    )

    if start_date is None or end_date is None:

        return None

    sales_df = sales_df.merge(
        rz_df,
        left_on='Location Name',
        right_on='location',
        how='left'
    )

    target_df = target_df.merge(
        rz_df,
        on='location',
        how='left'
    )

    sales_df = sales_df[
        sales_df['Brand Id'] == 'MOHOR'
    ]

    if rm:
        sales_df = sales_df[sales_df['rm'] == rm]
        target_df = target_df[target_df['rm'] == rm]

    if zm:
        sales_df = sales_df[sales_df['zm'] == zm]
        target_df = target_df[target_df['zm'] == zm]

    if location:
        sales_df = sales_df[sales_df['location'] == location]
        target_df = target_df[target_df['location'] == location]

    from_month = pd.to_datetime(start_date).replace(day=1)

    to_month = pd.to_datetime(end_date).replace(day=1)

    target_df = target_df[

        (target_df['month'] >= from_month)

        &

        (target_df['month'] <= to_month)

    ]

    target_data = (
        target_df
        .groupby('location', as_index=False)
        ['mohor_nsv']
        .sum()
    )

    target_data.rename(
        columns={
            'mohor_nsv': 'target_mohor_nsv'
        },
        inplace=True
    )

    sales_filtered = sales_df[
        (sales_df['Invoice Date'].dt.date >= start_date)
        &
        (sales_df['Invoice Date'].dt.date <= end_date)
    ]

    today_sales = (
        sales_filtered[
            sales_filtered['Invoice Date'].dt.date
            ==
            end_date
        ]
        .groupby('Location Name', as_index=False)
        .agg({
            'Bom Qty': 'sum',
            'Bom Line Amount': 'sum'
        })
    )

    today_sales.rename(
        columns={
            'Location Name': 'location',
            'Bom Qty': 'today_mohor_w',
            'Bom Line Amount': 'today_mohor_nsv'
        },
        inplace=True
    )

    mtd_sales = (
        sales_filtered
        .groupby('Location Name', as_index=False)
        .agg({
            'Bom Qty': 'sum',
            'Bom Line Amount': 'sum'
        })
    )

    mtd_sales.rename(
        columns={
            'Location Name': 'location',
            'Bom Qty': 'mtd_mohor_w',
            'Bom Line Amount': 'mtd_mohor_nsv'
        },
        inplace=True
    )

    df = target_data.merge(
        today_sales,
        on='location',
        how='left'
    )

    df = df.merge(
        mtd_sales,
        on='location',
        how='left'
    )

    df.fillna(0, inplace=True)

    days_passed = end_date.day

    df['run_rate'] = (
        df['mtd_mohor_w']
        /
        days_passed
    ).round(2)

    import calendar

    total_days = calendar.monthrange(
        end_date.year,
        end_date.month
    )[1]

    remaining_days = max(
    total_days - end_date.day,
    1
    )

    df['required_run_rate'] = (
        (
            df['target_mohor_nsv']
            -
            df['mtd_mohor_nsv']
        )
        /
        remaining_days
    ).fillna(0).round(0)

    # Merge with location code
    code_map = rz_df[['location', 'code']].drop_duplicates()
    df = df.merge(code_map, on='location', how='left')

    df = df[[
        'code',
        'location',
        'target_mohor_nsv',
        'today_mohor_w',
        'mtd_mohor_w',
        'today_mohor_nsv',
        'mtd_mohor_nsv',
        'run_rate',
        'required_run_rate'
    ]]

    df = df.sort_values(
        'code',
        na_position='last'
    )

    return df




#------------
# 7. MAKING CHARGE PERFORMANCE QUERY
#------------

import pandas as pd



def get_making_charge_performance(start_date, end_date, rm=None, zm=None, location=None):

    rm_filter = ""
    zm_filter = ""
    location_filter = ""

    if rm:
        rm_filter = f"AND rz.rm = '{rm}'"

    if zm:
        zm_filter = f"AND rz.zm = '{zm}'"

    if location:
        location_filter = f"AND rz.location = '{location}'"


    sales_df = merged_sales_df.copy()
    allowed_locations = get_allowed_locations()

    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']

            .isin(allowed_locations)

        ]

    rz_df = rm_zm_df.copy()

    sales_df, rz_df = standardize_sales_rz(

        sales_df,
        rz_df

    )

    start_date, end_date = validate_dates(

        start_date,
        end_date

    )

    if start_date is None or end_date is None:

        return None


    # ---------------------------------------------------
    # Merge RM/ZM
    # ---------------------------------------------------

    sales_df = sales_df.merge(

        rz_df,

        left_on='Location Name',

        right_on='location',

        how='left'

    )


    # ---------------------------------------------------
    # Date Filter
    # ---------------------------------------------------

    sales_df = sales_df[

        (

            sales_df['Invoice Date'].dt.date
            >= start_date

        )

        &

        (

            sales_df['Invoice Date'].dt.date
            <= end_date

        )

    ]


    # ---------------------------------------------------
    # Making Charge Filter
    # ---------------------------------------------------

    sales_df = sales_df[

        sales_df['Bom Item']
        .astype(str)
        .str.startswith('MK')

    ]


    # ---------------------------------------------------
    # Apply Filters
    # ---------------------------------------------------

    if rm:

        sales_df = sales_df[
            sales_df['rm'] == rm
        ]


    if zm:

        sales_df = sales_df[
            sales_df['zm'] == zm
        ]


    if location:

        sales_df = sales_df[
            sales_df['location'] == location
        ]


    # ---------------------------------------------------
    # Aggregate
    # ---------------------------------------------------

    df = (

        sales_df

        .groupby(
            'Location Name',
            as_index=False
        )

        .agg({

            'Bom Line Amount': [

                lambda x: x[
                    sales_df.loc[x.index, 'Item Type Group']
                    == 'DIAMOND'
                ].sum(),

                lambda x: x[
                    sales_df.loc[x.index, 'Item Type Group']
                    == 'GOLD'
                ].sum(),

                lambda x: x[
                    sales_df.loc[x.index, 'Item Type Group']
                    == 'SILVER'
                ].sum(),

                lambda x: x[
                    sales_df.loc[x.index, 'Item Type Group']
                    == 'PLATINUM'
                ].sum()

            ]

        })

    )


    # ---------------------------------------------------
    # Flatten Columns
    # ---------------------------------------------------

    df.columns = [

        'location',

        'diamond_mc',

        'gold_mc',

        'silver_mc',

        'platinum_mc'

    ]


    # ---------------------------------------------------
    # Round Values
    # ---------------------------------------------------

    df['diamond_mc'] = df['diamond_mc'].round(0)

    df['gold_mc'] = df['gold_mc'].round(0)

    df['silver_mc'] = df['silver_mc'].round(0)

    df['platinum_mc'] = df['platinum_mc'].round(0)

    # Merge with location code
    code_map = rz_df[['location', 'code']].drop_duplicates()
    df = df.merge(code_map, on='location', how='left')

    df = df[[
        'code',
        'location',
        'diamond_mc',
        'gold_mc',
        'silver_mc',
        'platinum_mc'
    ]]

    df = df.sort_values(
        'code',
        na_position='last'
    )


    return df




#------------
# 8. SCHEME PERFORMANCE QUERY
#------------

import pandas as pd



def get_scheme_performance(start_date, end_date, rm=None, zm=None, location=None):

    rm_filter = ""
    zm_filter = ""
    location_filter = ""

    if rm:
        rm_filter = f"AND rz.rm = '{rm}'"

    if zm:
        zm_filter = f"AND rz.zm = '{zm}'"

    if location:
        location_filter = f"AND rz.location = '{location}'"


    sales_df = scheme_df.copy()
    allowed_locations = get_allowed_locations()

    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['LocationName']

            .isin(allowed_locations)

        ]

    rz_df = rm_zm_df.copy()

    sales_df, rz_df = standardize_sales_rz(

        sales_df,
        rz_df

    )

    start_date, end_date = validate_dates(

        start_date,
        end_date

    )

    if start_date is None or end_date is None:

        return None


    # ---------------------------------------------------
    # Merge RM/ZM
    # ---------------------------------------------------

    sales_df = sales_df.merge(

        rz_df,

        left_on='LocationName',

        right_on='location',

        how='left'

    )


    # ---------------------------------------------------
    # Date Filter
    # ---------------------------------------------------

    sales_df = sales_df[

        (

            sales_df['SCHEMEOPENINGDATE']
            .dt.date

            >= start_date

        )

        &

        (

            sales_df['SCHEMEOPENINGDATE']
            .dt.date

            <= end_date

        )

    ]


    # ---------------------------------------------------
    # Apply Filters
    # ---------------------------------------------------

    if rm:

        sales_df = sales_df[
            sales_df['rm'] == rm
        ]


    if zm:

        sales_df = sales_df[
            sales_df['zm'] == zm
        ]


    if location:

        sales_df = sales_df[
            sales_df['location'] == location
        ]


    # ---------------------------------------------------
    # Today's Data
    # ---------------------------------------------------

    today_df = sales_df[

        sales_df['SCHEMEOPENINGDATE']
        .dt.date

        ==

        end_date

    ]


    today_data = (

        today_df

        .groupby(
            'LocationName',
            as_index=False
        )

        .agg({

            'SCHEMEENTRYNO': pd.Series.nunique,

            'SchemefirstPayamt': 'sum'

        })

    )

    today_data.rename(

        columns={

            'LocationName': 'location',

            'SCHEMEENTRYNO': 'today_scheme_count',

            'SchemefirstPayamt': 'today_scheme_collection'

        },

        inplace=True

    )


    # ---------------------------------------------------
    # MTD Data
    # ---------------------------------------------------

    mtd_data = (

        sales_df

        .groupby(
            'LocationName',
            as_index=False
        )

        .agg({

            'SCHEMEENTRYNO': pd.Series.nunique,

            'SchemefirstPayamt': 'sum'

        })

    )

    mtd_data.rename(

        columns={

            'LocationName': 'location',

            'SCHEMEENTRYNO': 'mtd_scheme_count',

            'SchemefirstPayamt': 'mtd_scheme_collection'

        },

        inplace=True

    )


    # ---------------------------------------------------
    # Merge Final
    # ---------------------------------------------------

    df = today_data.merge(

        mtd_data,

        on='location',

        how='outer'

    )


    for col in df.columns:

        if pd.api.types.is_numeric_dtype(df[col]):

            df[col] = df[col].fillna(0)

        else:

            df[col] = df[col].fillna("")


    # ---------------------------------------------------
    # Round Values
    # ---------------------------------------------------

    df['today_scheme_collection'] = (

        df['today_scheme_collection']
        .round(0)

    )

    df['mtd_scheme_collection'] = (

        df['mtd_scheme_collection']
        .round(0)

    )

    # Merge with location code
    code_map = rz_df[['location', 'code']].drop_duplicates()
    df = df.merge(code_map, on='location', how='left')

    df = df[[
        'code',
        'location',
        'today_scheme_count',
        'today_scheme_collection',
        'mtd_scheme_count',
        'mtd_scheme_collection'
    ]]

    df = df.sort_values(
        'code',
        na_position='last'
    )


    return df


#---------------------------GAUGE-----------------------#

#------------
# NSV GAUGE QUERY
#------------

import pandas as pd



def get_nsv_gauge(start_date, end_date, rm=None, zm=None, location=None):

    rm_filter = ""
    zm_filter = ""
    location_filter = ""

    if rm:
        rm_filter = f"AND rz.rm = '{rm}'"

    if zm:
        zm_filter = f"AND rz.zm = '{zm}'"

    if location:
        location_filter = f"AND rz.location = '{location}'"


    sales_df = merged_sales_df.copy()

    target_df = targets_df.copy()

    rz_df = rm_zm_df.copy()


    sales_df, target_df, rz_df = standardize_location_columns(

        sales_df,
        target_df,
        rz_df

    )


    allowed_locations = get_allowed_locations()


    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']

            .isin(allowed_locations)

        ]


        target_df = target_df[

            target_df['location']

            .isin(allowed_locations)

        ]

    start_date, end_date = validate_dates(

        start_date,
        end_date

    )

    if start_date is None or end_date is None:

        return 0


    # ---------------------------------------------------
    # Merge RM/ZM
    # ---------------------------------------------------

    sales_df = sales_df.merge(

        rz_df,

        left_on='Location Name',

        right_on='location',

        how='left'

    )

    target_df = target_df.merge(

        rz_df,

        on='location',

        how='left'

    )


    # ---------------------------------------------------
    # Apply Filters
    # ---------------------------------------------------

    if rm:

        sales_df = sales_df[
            sales_df['rm'] == rm
        ]

        target_df = target_df[
            target_df['rm'] == rm
        ]


    if zm:

        sales_df = sales_df[
            sales_df['zm'] == zm
        ]

        target_df = target_df[
            target_df['zm'] == zm
        ]


    if location:

        sales_df = sales_df[
            sales_df['location'] == location
        ]

        target_df = target_df[
            target_df['location'] == location
        ]


    # ---------------------------------------------------
    # Filter Month
    # ---------------------------------------------------

    from_month = pd.to_datetime(start_date).replace(day=1)

    to_month = pd.to_datetime(end_date).replace(day=1)

    target_df = target_df[

        (target_df['month'] >= from_month)

        &

        (target_df['month'] <= to_month)

    ]


    # ---------------------------------------------------
    # Target
    # ---------------------------------------------------

    target_nsv = target_df['nsv'].sum()


    # ---------------------------------------------------
    # Achieved
    # ---------------------------------------------------

    achieved_nsv = (

        sales_df[

            (

                sales_df['Invoice Date'].dt.date
                >= start_date

            )

            &

            (

                sales_df['Invoice Date'].dt.date
                <= end_date

            )

        ]

        ['Bom Line Amount']

        .sum()

    )


    # ---------------------------------------------------
    # Achievement %
    # ---------------------------------------------------

    achievement_percent = 0

    if target_nsv != 0:

        achievement_percent = round(

            (

                achieved_nsv
                /
                target_nsv

            ) * 100,

            0

        )


    # ---------------------------------------------------
    # Final DF
    # ---------------------------------------------------

    df = pd.DataFrame({

        'achieved_nsv': [
            round(achieved_nsv, 0)
        ],

        'target_nsv': [
            round(target_nsv, 0)
        ],

        'achievement_percent': [
            achievement_percent
        ]

    })


    return df


#------------
# GOLD GAUGE QUERY
#------------

import pandas as pd



def get_gold_gauge(start_date, end_date, rm=None, zm=None, location=None):

    rm_filter = ""
    zm_filter = ""
    location_filter = ""

    if rm:
        rm_filter = f"AND rz.rm = '{rm}'"

    if zm:
        zm_filter = f"AND rz.zm = '{zm}'"

    if location:
        location_filter = f"AND rz.location = '{location}'"



    sales_df = merged_sales_df.copy()

    target_df = targets_df.copy()

    rz_df = rm_zm_df.copy()


    sales_df, target_df, rz_df = standardize_location_columns(

        sales_df,
        target_df,
        rz_df

    )


    allowed_locations = get_allowed_locations()


    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']

            .isin(allowed_locations)

        ]


        target_df = target_df[

            target_df['location']

            .isin(allowed_locations)

        ]



    start_date, end_date = validate_dates(

        start_date,
        end_date

    )

    if start_date is None or end_date is None:

        return 0


    # ---------------------------------------------------
    # Merge RM/ZM
    # ---------------------------------------------------

    sales_df = sales_df.merge(

        rz_df,

        left_on='Location Name',

        right_on='location',

        how='left'

    )

    target_df = target_df.merge(

        rz_df,

        on='location',

        how='left'

    )


    # ---------------------------------------------------
    # Gold Filter
    # ---------------------------------------------------

    sales_df = sales_df[

        (sales_df['Bom UOM'] == 'GMS')

        &

        (sales_df['Bom Item Type'] == 'GOLD')

    ]


    # ---------------------------------------------------
    # Apply Filters
    # ---------------------------------------------------

    if rm:

        sales_df = sales_df[
            sales_df['rm'] == rm
        ]

        target_df = target_df[
            target_df['rm'] == rm
        ]


    if zm:

        sales_df = sales_df[
            sales_df['zm'] == zm
        ]

        target_df = target_df[
            target_df['zm'] == zm
        ]


    if location:

        sales_df = sales_df[
            sales_df['location'] == location
        ]

        target_df = target_df[
            target_df['location'] == location
        ]


    # ---------------------------------------------------
    # Filter Month
    # ---------------------------------------------------

    from_month = pd.to_datetime(start_date).replace(day=1)

    to_month = pd.to_datetime(end_date).replace(day=1)

    target_df = target_df[

        (target_df['month'] >= from_month)

        &

        (target_df['month'] <= to_month)

    ]

    # ---------------------------------------------------
    # Target
    # ---------------------------------------------------

    target_gold = target_df['gold_w'].sum()


    # ---------------------------------------------------
    # Achieved
    # ---------------------------------------------------

    achieved_gold = (

        sales_df[

            (

                sales_df['Invoice Date'].dt.date
                >= start_date

            )

            &

            (

                sales_df['Invoice Date'].dt.date
                <= end_date

            )

        ]

        ['Bom Qty']

        .sum()

    )


    # ---------------------------------------------------
    # Achievement %
    # ---------------------------------------------------

    achievement_percent = 0

    if target_gold != 0:

        achievement_percent = round(

            (

                achieved_gold
                /
                target_gold

            ) * 100,

            2

        )


    # ---------------------------------------------------
    # Final DF
    # ---------------------------------------------------

    df = pd.DataFrame({

        'achieved_gold': [
            round(achieved_gold, 2)
        ],

        'target_gold': [
            round(target_gold, 2)
        ],

        'achievement_percent': [
            achievement_percent
        ]

    })


    return df



#------------
# DIAMOND GAUGE QUERY
#------------

import pandas as pd



def get_diamond_gauge(start_date, end_date, rm=None, zm=None, location=None):

    rm_filter = ""
    zm_filter = ""
    location_filter = ""

    if rm:
        rm_filter = f"AND rz.rm = '{rm}'"

    if zm:
        zm_filter = f"AND rz.zm = '{zm}'"

    if location:
        location_filter = f"AND rz.location = '{location}'"

    sales_df = merged_sales_df.copy()

    target_df = targets_df.copy()

    rz_df = rm_zm_df.copy()


    sales_df, target_df, rz_df = standardize_location_columns(

        sales_df,
        target_df,
        rz_df

    )


    allowed_locations = get_allowed_locations()


    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']

            .isin(allowed_locations)

        ]


        target_df = target_df[

            target_df['location']

            .isin(allowed_locations)

        ]

    start_date, end_date = validate_dates(

        start_date,
        end_date

    )

    if start_date is None or end_date is None:

        return 0


    # ---------------------------------------------------
    # Merge RM/ZM
    # ---------------------------------------------------

    sales_df = sales_df.merge(

        rz_df,

        left_on='Location Name',

        right_on='location',

        how='left'

    )

    target_df = target_df.merge(

        rz_df,

        on='location',

        how='left'

    )


    # ---------------------------------------------------
    # Diamond Filter
    # ---------------------------------------------------

    sales_df = sales_df[

        (sales_df['Bom UOM'] == 'CTS')

        &

        (sales_df['Bom Item Type'] == 'DIAMOND')

    ]


    # ---------------------------------------------------
    # Apply Filters
    # ---------------------------------------------------

    if rm:

        sales_df = sales_df[
            sales_df['rm'] == rm
        ]

        target_df = target_df[
            target_df['rm'] == rm
        ]


    if zm:

        sales_df = sales_df[
            sales_df['zm'] == zm
        ]

        target_df = target_df[
            target_df['zm'] == zm
        ]


    if location:

        sales_df = sales_df[
            sales_df['location'] == location
        ]

        target_df = target_df[
            target_df['location'] == location
        ]


    # ---------------------------------------------------
    # Filter Month
    # ---------------------------------------------------

    from_month = pd.to_datetime(start_date).replace(day=1)

    to_month = pd.to_datetime(end_date).replace(day=1)

    target_df = target_df[

        (target_df['month'] >= from_month)

        &

        (target_df['month'] <= to_month)

    ]


    # ---------------------------------------------------
    # Target
    # ---------------------------------------------------

    target_diamond = target_df['diamond_cts'].sum()


    # ---------------------------------------------------
    # Achieved
    # ---------------------------------------------------

    achieved_diamond = (

        sales_df[

            (

                sales_df['Invoice Date'].dt.date
                >= start_date

            )

            &

            (

                sales_df['Invoice Date'].dt.date
                <= end_date

            )

        ]

        ['Bom Qty']

        .sum()

    )


    # ---------------------------------------------------
    # Achievement %
    # ---------------------------------------------------

    achievement_percent = 0

    if target_diamond != 0:

        achievement_percent = round(

            (

                achieved_diamond
                /
                target_diamond

            ) * 100,

            2

        )


    # ---------------------------------------------------
    # Final DF
    # ---------------------------------------------------

    df = pd.DataFrame({

        'achieved_diamond': [
            round(achieved_diamond, 2)
        ],

        'target_diamond': [
            round(target_diamond, 2)
        ],

        'achievement_percent': [
            achievement_percent
        ]

    })


    return df



#------------
# SILVER GAUGE QUERY
#------------

import pandas as pd



def get_silver_gauge(start_date, end_date, rm=None, zm=None, location=None):

    rm_filter = ""
    zm_filter = ""
    location_filter = ""

    if rm:
        rm_filter = f"AND rz.rm = '{rm}'"

    if zm:
        zm_filter = f"AND rz.zm = '{zm}'"

    if location:
        location_filter = f"AND rz.location = '{location}'"

    sales_df = merged_sales_df.copy()

    target_df = targets_df.copy()

    rz_df = rm_zm_df.copy()


    sales_df, target_df, rz_df = standardize_location_columns(

        sales_df,
        target_df,
        rz_df

    )


    allowed_locations = get_allowed_locations()


    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']

            .isin(allowed_locations)

        ]


        target_df = target_df[

            target_df['location']

            .isin(allowed_locations)

        ]

    start_date, end_date = validate_dates(

        start_date,
        end_date

    )

    if start_date is None or end_date is None:

        return 0


    # ---------------------------------------------------
    # Merge RM/ZM
    # ---------------------------------------------------

    sales_df = sales_df.merge(

        rz_df,

        left_on='Location Name',

        right_on='location',

        how='left'

    )

    target_df = target_df.merge(

        rz_df,

        on='location',

        how='left'

    )


    # ---------------------------------------------------
    # Silver Filter
    # ---------------------------------------------------

    sales_df = sales_df[

        (sales_df['Bom UOM'] == 'GMS')

        &

        (sales_df['Bom Item Type'] == 'SILVER')

        &

        (sales_df['Item Type Group'] == 'SILVER')

    ]


    # ---------------------------------------------------
    # Apply Filters
    # ---------------------------------------------------

    if rm:

        sales_df = sales_df[
            sales_df['rm'] == rm
        ]

        target_df = target_df[
            target_df['rm'] == rm
        ]


    if zm:

        sales_df = sales_df[
            sales_df['zm'] == zm
        ]

        target_df = target_df[
            target_df['zm'] == zm
        ]


    if location:

        sales_df = sales_df[
            sales_df['location'] == location
        ]

        target_df = target_df[
            target_df['location'] == location
        ]


    # ---------------------------------------------------
    # Filter Month
    # ---------------------------------------------------

    from_month = pd.to_datetime(start_date).replace(day=1)

    to_month = pd.to_datetime(end_date).replace(day=1)

    target_df = target_df[

        (target_df['month'] >= from_month)

        &

        (target_df['month'] <= to_month)

    ]


    # ---------------------------------------------------
    # Target
    # ---------------------------------------------------

    target_silver = target_df['silver_w'].sum()


    # ---------------------------------------------------
    # Achieved
    # ---------------------------------------------------

    achieved_silver = (

        sales_df[

            (

                sales_df['Invoice Date'].dt.date
                >= start_date

            )

            &

            (

                sales_df['Invoice Date'].dt.date
                <= end_date

            )

        ]

        ['Bom Qty']

        .sum()

    )


    # ---------------------------------------------------
    # Achievement %
    # ---------------------------------------------------

    achievement_percent = 0

    if target_silver != 0:

        achievement_percent = round(

            (

                achieved_silver
                /
                target_silver

            ) * 100,

            2

        )


    # ---------------------------------------------------
    # Final DF
    # ---------------------------------------------------

    df = pd.DataFrame({

        'achieved_silver': [
            round(achieved_silver, 2)
        ],

        'target_silver': [
            round(target_silver, 2)
        ],

        'achievement_percent': [
            achievement_percent
        ]

    })


    return df



#------------
# GEMSTONE GAUGE QUERY
#------------

import pandas as pd



def get_gemstone_gauge(start_date, end_date, rm=None, zm=None, location=None):

    rm_filter = ""
    zm_filter = ""
    location_filter = ""

    if rm:
        rm_filter = f"AND rz.rm = '{rm}'"

    if zm:
        zm_filter = f"AND rz.zm = '{zm}'"

    if location:
        location_filter = f"AND rz.location = '{location}'"

    sales_df = merged_sales_df.copy()

    target_df = targets_df.copy()

    rz_df = rm_zm_df.copy()


    sales_df, target_df, rz_df = standardize_location_columns(

        sales_df,
        target_df,
        rz_df

    )


    allowed_locations = get_allowed_locations()


    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']

            .isin(allowed_locations)

        ]


        target_df = target_df[

            target_df['location']

            .isin(allowed_locations)

        ]

    start_date, end_date = validate_dates(

        start_date,
        end_date

    )

    if start_date is None or end_date is None:

        return 0


    # ---------------------------------------------------
    # Merge RM/ZM
    # ---------------------------------------------------

    sales_df = sales_df.merge(

        rz_df,

        left_on='Location Name',

        right_on='location',

        how='left'

    )

    target_df = target_df.merge(

        rz_df,

        on='location',

        how='left'

    )


    # ---------------------------------------------------
    # Gemstone Filter
    # ---------------------------------------------------

    sales_df = sales_df[

        (sales_df['Bom Item Type'] == 'STONE_CT')

        &

        (sales_df['Item Type Group'] == 'NONE')

    ]


    # ---------------------------------------------------
    # Apply Filters
    # ---------------------------------------------------

    if rm:

        sales_df = sales_df[
            sales_df['rm'] == rm
        ]

        target_df = target_df[
            target_df['rm'] == rm
        ]


    if zm:

        sales_df = sales_df[
            sales_df['zm'] == zm
        ]

        target_df = target_df[
            target_df['zm'] == zm
        ]


    if location:

        sales_df = sales_df[
            sales_df['location'] == location
        ]

        target_df = target_df[
            target_df['location'] == location
        ]


    # ---------------------------------------------------
    # Filter Month
    # ---------------------------------------------------

    from_month = pd.to_datetime(start_date).replace(day=1)

    to_month = pd.to_datetime(end_date).replace(day=1)

    target_df = target_df[

        (target_df['month'] >= from_month)

        &

        (target_df['month'] <= to_month)

    ]


    # ---------------------------------------------------
    # Target
    # ---------------------------------------------------

    target_gemstone = target_df['gemstone_nsv'].sum()


    # ---------------------------------------------------
    # Achieved
    # ---------------------------------------------------

    achieved_gemstone = (

        sales_df[

            (

                sales_df['Invoice Date'].dt.date
                >= start_date

            )

            &

            (

                sales_df['Invoice Date'].dt.date
                <= end_date

            )

        ]

        ['Bom Line Amount']

        .sum()

    )


    # ---------------------------------------------------
    # Achievement %
    # ---------------------------------------------------

    achievement_percent = 0

    if target_gemstone != 0:

        achievement_percent = round(

            (

                achieved_gemstone
                /
                target_gemstone

            ) * 100,

            0

        )


    # ---------------------------------------------------
    # Final DF
    # ---------------------------------------------------

    df = pd.DataFrame({

        'achieved_gemstone': [
            round(achieved_gemstone, 0)
        ],

        'target_gemstone': [
            round(target_gemstone, 0)
        ],

        'achievement_percent': [
            achievement_percent
        ]

    })


    return df


#------------
# MOHOR GAUGE QUERY
#------------

import pandas as pd



def get_mohor_gauge(start_date, end_date, rm=None, zm=None, location=None):

    rm_filter = ""
    zm_filter = ""
    location_filter = ""

    if rm:
        rm_filter = f"AND rz.rm = '{rm}'"

    if zm:
        zm_filter = f"AND rz.zm = '{zm}'"

    if location:
        location_filter = f"AND rz.location = '{location}'"

    sales_df = merged_sales_df.copy()

    target_df = targets_df.copy()

    rz_df = rm_zm_df.copy()


    sales_df, target_df, rz_df = standardize_location_columns(

        sales_df,
        target_df,
        rz_df

    )


    allowed_locations = get_allowed_locations()


    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']

            .isin(allowed_locations)

        ]


        target_df = target_df[

            target_df['location']

            .isin(allowed_locations)

        ]

    start_date, end_date = validate_dates(

        start_date,
        end_date

    )

    if start_date is None or end_date is None:

        return 0


    # ---------------------------------------------------
    # Merge RM/ZM
    # ---------------------------------------------------

    sales_df = sales_df.merge(

        rz_df,

        left_on='Location Name',

        right_on='location',

        how='left'

    )

    target_df = target_df.merge(

        rz_df,

        on='location',

        how='left'

    )


    # ---------------------------------------------------
    # Mohor Filter
    # ---------------------------------------------------

    sales_df = sales_df[

        sales_df['Brand Id'] == 'MOHOR'

    ]


    # ---------------------------------------------------
    # Apply Filters
    # ---------------------------------------------------

    if rm:

        sales_df = sales_df[
            sales_df['rm'] == rm
        ]

        target_df = target_df[
            target_df['rm'] == rm
        ]


    if zm:

        sales_df = sales_df[
            sales_df['zm'] == zm
        ]

        target_df = target_df[
            target_df['zm'] == zm
        ]


    if location:

        sales_df = sales_df[
            sales_df['location'] == location
        ]

        target_df = target_df[
            target_df['location'] == location
        ]


    # ---------------------------------------------------
    # Filter Month
    # ---------------------------------------------------

    from_month = pd.to_datetime(start_date).replace(day=1)

    to_month = pd.to_datetime(end_date).replace(day=1)

    target_df = target_df[

        (target_df['month'] >= from_month)

        &

        (target_df['month'] <= to_month)

    ]


    # ---------------------------------------------------
    # Target
    # ---------------------------------------------------

    target_mohor = target_df['mohor_nsv'].sum()


    # ---------------------------------------------------
    # Achieved
    # ---------------------------------------------------

    achieved_mohor = (

        sales_df[

            (

                sales_df['Invoice Date'].dt.date
                >= start_date

            )

            &

            (

                sales_df['Invoice Date'].dt.date
                <= end_date

            )

        ]

        ['Bom Line Amount']

        .sum()

    )


    # ---------------------------------------------------
    # Achievement %
    # ---------------------------------------------------

    achievement_percent = 0

    if target_mohor != 0:

        achievement_percent = round(

            (

                achieved_mohor
                /
                target_mohor

            ) * 100,

            0

        )


    # ---------------------------------------------------
    # Final DF
    # ---------------------------------------------------

    df = pd.DataFrame({

        'achieved_mohor': [
            round(achieved_mohor, 0)
        ],

        'target_mohor': [
            round(target_mohor, 0)
        ],

        'achievement_percent': [
            achievement_percent
        ]

    })


    return df