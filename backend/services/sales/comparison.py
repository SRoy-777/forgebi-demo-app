import pandas as pd
import calendar

from backend.cache.data_cache import (
    merged_sales_df,
    rm_zm_df,
    scheme_df
)

from backend.services.rls import (
    get_allowed_locations
)

# ---------------------------------------------------
# Common Filter Prep
# ---------------------------------------------------

def prepare_comparison_data(
    start_date,
    end_date,
    rm=None,
    zm=None,
    location=None
    ):

    # ---------------------------------------------------
    # Copy DFs
    # ---------------------------------------------------

    sales_df = merged_sales_df.copy()

    allowed_locations = get_allowed_locations()

    if 'ALL' not in allowed_locations:

        sales_df = sales_df[

            sales_df['Location Name']

            .isin(allowed_locations)

        ]

    scheme_data = scheme_df.copy()

    if 'ALL' not in allowed_locations:

        scheme_data = scheme_data[

            scheme_data['LocationName']

            .isin(allowed_locations)

        ]

    rz_df = rm_zm_df.copy()


    # ---------------------------------------------------
    # Merge RM/ZM
    # ---------------------------------------------------

    sales_df = sales_df.merge(

        rz_df,

        left_on='Location Name',

        right_on='location',

        how='left'

    )

    scheme_data = scheme_data.merge(

        rz_df,

        left_on='LocationName',

        right_on='location',

        how='left'

    )


    # ---------------------------------------------------
    # Date Conversion
    # ---------------------------------------------------

    start_date = pd.to_datetime(start_date)

    end_date = pd.to_datetime(end_date)


    # ---------------------------------------------------
    # LY Dates
    # ---------------------------------------------------

    ly_start_date = start_date - pd.DateOffset(years=1)

    ly_end_date = end_date - pd.DateOffset(years=1)


    # ---------------------------------------------------
    # LY Full Month Range
    # ---------------------------------------------------

    ly_month_start = pd.Timestamp(

        year=start_date.year - 1,
        month=start_date.month,
        day=1

    )

    ly_month_end = pd.Timestamp(

        year=end_date.year - 1,
        month=end_date.month,
        day=calendar.monthrange(
            end_date.year - 1,
            end_date.month
        )[1]

    )


    # ---------------------------------------------------
    # Apply RM/ZM/Location Filters
    # ---------------------------------------------------

    if rm:

        sales_df = sales_df[
            sales_df['rm'] == rm
        ]

        scheme_data = scheme_data[
            scheme_data['rm'] == rm
        ]


    if zm:

        sales_df = sales_df[
            sales_df['zm'] == zm
        ]

        scheme_data = scheme_data[
            scheme_data['zm'] == zm
        ]


    if location:

        sales_df = sales_df[
            sales_df['location'] == location
        ]

        scheme_data = scheme_data[
            scheme_data['location'] == location
        ]


    return {

        'sales_df': sales_df,

        'scheme_df': scheme_data,

        'start_date': start_date,

        'end_date': end_date,

        'ly_start_date': ly_start_date,

        'ly_end_date': ly_end_date,

        'ly_month_start': ly_month_start,

        'ly_month_end': ly_month_end

    }

# ---------------------------------------------------
# Universal Comparison Table Builder
# ---------------------------------------------------

def build_comparison_table(

    sales_df,

    metric_column,

    group_name,

    ly_month_start,

    ly_month_end,

    ly_start_date,

    ly_end_date,

    start_date,

    end_date,

    filters=None,

    agg='sum',

    distinct_col=None,

    all_locations=None

):

    df = sales_df.copy()


    # ---------------------------------------------------
    # Apply Extra Filters
    # ---------------------------------------------------

    if filters:

        for column, value in filters.items():

            if value == 'NOT_NULL':

                df = df[
                    df[column].notna()
                ]

            else:

                df = df[
                    df[column] == value
                ]


    # ---------------------------------------------------
    # LYM
    # ---------------------------------------------------

    lym_df = df[

        (

            df['Invoice Date']
            >= ly_month_start

        )

        &

        (

            df['Invoice Date']
            <= ly_month_end

        )

    ]


    # ---------------------------------------------------
    # LY MTD
    # ---------------------------------------------------

    ly_mtd_df = df[

        (

            df['Invoice Date']
            >= ly_start_date

        )

        &

        (

            df['Invoice Date']
            <= ly_end_date

        )

    ]


    # ---------------------------------------------------
    # TY MTD
    # ---------------------------------------------------

    ty_mtd_df = df[

        (

            df['Invoice Date']
            >= start_date

        )

        &

        (

            df['Invoice Date']
            <= end_date

        )

    ]


    # ---------------------------------------------------
    # Aggregation Function
    # ---------------------------------------------------

    def aggregate(dataframe):

        if agg == 'sum':

            result = (

                dataframe

                .groupby(
                    'location',
                    as_index=False
                )

                [metric_column]

                .sum()

            )

        elif agg == 'nunique':

            result = (

                dataframe

                .groupby(
                    'location',
                    as_index=False
                )

                [distinct_col]

                .nunique()

            )

        return result


    # ---------------------------------------------------
    # Aggregate Data
    # ---------------------------------------------------

    lym = aggregate(lym_df)

    ly_mtd = aggregate(ly_mtd_df)

    ty_mtd = aggregate(ty_mtd_df)


    # ---------------------------------------------------
    # Rename Columns
    # ---------------------------------------------------

    lym.rename(

        columns={
            metric_column if agg == 'sum' else distinct_col: 'LYM'
        },

        inplace=True

    )

    ly_mtd.rename(

        columns={
            metric_column if agg == 'sum' else distinct_col: 'LY_MTD'
        },

        inplace=True

    )

    ty_mtd.rename(

        columns={
            metric_column if agg == 'sum' else distinct_col: 'TY_MTD'
        },

        inplace=True

    )


    # ---------------------------------------------------
    # Merge
    # ---------------------------------------------------

    if all_locations is not None:
        base_df = pd.DataFrame({'location': all_locations})
        final_df = base_df.merge(
            lym,
            on='location',
            how='left'
        ).merge(
            ly_mtd,
            on='location',
            how='left'
        ).merge(
            ty_mtd,
            on='location',
            how='left'
        )
    else:
        final_df = lym.merge(

            ly_mtd,

            on='location',

            how='outer'

        )

        final_df = final_df.merge(

            ty_mtd,

            on='location',

            how='outer'

        )


    final_df.fillna(0, inplace=True)


    # ---------------------------------------------------
    # Diff
    # ---------------------------------------------------

    final_df['V_Diff'] = (

        final_df['TY_MTD']

        -

        final_df['LY_MTD']

    )


    final_df['Pct_Diff'] = (

        (

            final_df['V_Diff']

            /

            final_df['LY_MTD'].replace(0, float('nan'))

        ) * 100

    ).fillna(0).round(2)


    # ---------------------------------------------------
    # Merge with location code
    # ---------------------------------------------------
    code_map = rm_zm_df[['location', 'code']].drop_duplicates()
    final_df = final_df.merge(code_map, on='location', how='left')

    # ---------------------------------------------------
    # Rename Location and Code
    # ---------------------------------------------------

    final_df.rename(

        columns={
            'location': 'Location',
            'code': 'Code'
        },

        inplace=True

    )

    # Reorder columns to place Code and Location first
    cols = ['Code', 'Location'] + [c for c in final_df.columns if c not in ['Code', 'Location']]
    final_df = final_df[cols]

    # ---------------------------------------------------
    # Sort
    # ---------------------------------------------------

    final_df = final_df.sort_values(
        'Code',
        na_position='last'
    )


    # ---------------------------------------------------
    # Total Row
    # ---------------------------------------------------

    total_lym = final_df['LYM'].sum()

    total_ly_mtd = final_df['LY_MTD'].sum()

    total_ty_mtd = final_df['TY_MTD'].sum()

    total_v_diff = (

        total_ty_mtd
        -
        total_ly_mtd

    )


    total_pct_diff = 0

    if total_ly_mtd != 0:

        total_pct_diff = round(

            (

                total_v_diff
                /
                total_ly_mtd

            ) * 100,

            2

        )


    total_row = pd.DataFrame([{

        'Code': '',

        'Location': 'TOTAL',

        'LYM': total_lym,

        'LY_MTD': total_ly_mtd,

        'TY_MTD': total_ty_mtd,

        'V_Diff': total_v_diff,

        'Pct_Diff': total_pct_diff

    }])


    final_df = pd.concat(

        [

            final_df,

            total_row

        ],

        ignore_index=True

    )

    # ---------------------------------------------------
    # Raw Columns For Conditional Formatting
    # ---------------------------------------------------

    final_df['raw_v_diff'] = final_df['V_Diff']

    final_df['raw_pct_diff'] = final_df['Pct_Diff']

    return final_df

# ---------------------------------------------------
# NSV
# ---------------------------------------------------

def get_nsv_comparison(prepared_data):

    return build_comparison_table(

        sales_df=prepared_data['sales_df'],

        metric_column='Bom Line Amount',

        group_name='NSV',

        ly_month_start=prepared_data['ly_month_start'],

        ly_month_end=prepared_data['ly_month_end'],

        ly_start_date=prepared_data['ly_start_date'],

        ly_end_date=prepared_data['ly_end_date'],

        start_date=prepared_data['start_date'],

        end_date=prepared_data['end_date']

    )


# ---------------------------------------------------
# GOLD
# ---------------------------------------------------

def get_gold_comparison(prepared_data):

    return build_comparison_table(

        sales_df=prepared_data['sales_df'],

        metric_column='Bom Qty',

        group_name='Gold',

        ly_month_start=prepared_data['ly_month_start'],

        ly_month_end=prepared_data['ly_month_end'],

        ly_start_date=prepared_data['ly_start_date'],

        ly_end_date=prepared_data['ly_end_date'],

        start_date=prepared_data['start_date'],

        end_date=prepared_data['end_date'],

        filters={

            'Bom UOM': 'GMS',

            'Bom Item Type': 'GOLD'

        }

    )


# ---------------------------------------------------
# DIAMOND
# ---------------------------------------------------

def get_diamond_comparison(prepared_data):

    return build_comparison_table(

        sales_df=prepared_data['sales_df'],

        metric_column='Bom Qty',

        group_name='Diamond',

        ly_month_start=prepared_data['ly_month_start'],

        ly_month_end=prepared_data['ly_month_end'],

        ly_start_date=prepared_data['ly_start_date'],

        ly_end_date=prepared_data['ly_end_date'],

        start_date=prepared_data['start_date'],

        end_date=prepared_data['end_date'],

        filters={

            'Bom UOM': 'CTS',

            'Bom Item Type': 'DIAMOND'

        }

    )


# ---------------------------------------------------
# SILVER
# ---------------------------------------------------

def get_silver_comparison(prepared_data):

    return build_comparison_table(

        sales_df=prepared_data['sales_df'],

        metric_column='Bom Qty',

        group_name='Silver',

        ly_month_start=prepared_data['ly_month_start'],

        ly_month_end=prepared_data['ly_month_end'],

        ly_start_date=prepared_data['ly_start_date'],

        ly_end_date=prepared_data['ly_end_date'],

        start_date=prepared_data['start_date'],

        end_date=prepared_data['end_date'],

        filters={

            'Bom UOM': 'GMS',

            'Bom Item Type': 'SILVER',

            'Item Type Group': 'SILVER'

        }

    )

# ---------------------------------------------------
# GEMSTONE
# ---------------------------------------------------

def get_gemstone_comparison(prepared_data):

    all_locs = prepared_data['sales_df']['location'].dropna().unique()

    return build_comparison_table(

        sales_df=prepared_data['sales_df'],

        metric_column='Bom Line Amount',

        group_name='Gemstone',

        ly_month_start=prepared_data['ly_month_start'],

        ly_month_end=prepared_data['ly_month_end'],

        ly_start_date=prepared_data['ly_start_date'],

        ly_end_date=prepared_data['ly_end_date'],

        start_date=prepared_data['start_date'],

        end_date=prepared_data['end_date'],

        filters={

            'Bom Item Type': 'STONE_CT',

            'Item Type Group': 'NONE'

        },

        all_locations=all_locs

    )


# ---------------------------------------------------
# MOHOR
# ---------------------------------------------------

def get_mohor_comparison(prepared_data):

    return build_comparison_table(

        sales_df=prepared_data['sales_df'],

        metric_column='Bom Line Amount',

        group_name='Mohor',

        ly_month_start=prepared_data['ly_month_start'],

        ly_month_end=prepared_data['ly_month_end'],

        ly_start_date=prepared_data['ly_start_date'],

        ly_end_date=prepared_data['ly_end_date'],

        start_date=prepared_data['start_date'],

        end_date=prepared_data['end_date'],

        filters={

            'Brand Id': 'MOHOR'

        }

    )


# ---------------------------------------------------
# MAKING CHARGE
# ---------------------------------------------------

def get_mc_comparison(prepared_data):

    df = prepared_data['sales_df'].copy()

    df = df[

        df['Bom Item']
        .astype(str)
        .str.startswith('MK')

    ]

    return build_comparison_table(

        sales_df=df,

        metric_column='Bom Line Amount',

        group_name='MC',

        ly_month_start=prepared_data['ly_month_start'],

        ly_month_end=prepared_data['ly_month_end'],

        ly_start_date=prepared_data['ly_start_date'],

        ly_end_date=prepared_data['ly_end_date'],

        start_date=prepared_data['start_date'],

        end_date=prepared_data['end_date']

    )


# ---------------------------------------------------
# INVOICE
# ---------------------------------------------------

def get_invoice_comparison(prepared_data):

    return build_comparison_table(

        sales_df=prepared_data['sales_df'],

        metric_column='Document No.',

        distinct_col='Document No.',

        group_name='Invoice',

        ly_month_start=prepared_data['ly_month_start'],

        ly_month_end=prepared_data['ly_month_end'],

        ly_start_date=prepared_data['ly_start_date'],

        ly_end_date=prepared_data['ly_end_date'],

        start_date=prepared_data['start_date'],

        end_date=prepared_data['end_date'],

        filters={

            'Sales Type': 'Sales'

        },

        agg='nunique'

    )


# ---------------------------------------------------
# TAGS
# ---------------------------------------------------

def get_tag_comparison(prepared_data):

    return build_comparison_table(

        sales_df=prepared_data['sales_df'],

        metric_column='Tag No',

        distinct_col='Tag No',

        group_name='Tags',

        ly_month_start=prepared_data['ly_month_start'],

        ly_month_end=prepared_data['ly_month_end'],

        ly_start_date=prepared_data['ly_start_date'],

        ly_end_date=prepared_data['ly_end_date'],

        start_date=prepared_data['start_date'],

        end_date=prepared_data['end_date'],

        filters={

            'Sales Type': 'Sales',

            'Tag No': 'NOT_NULL'

        },

        agg='nunique'

    )

# ---------------------------------------------------
# SCHEME
# ---------------------------------------------------

def get_scheme_comparison(prepared_data):

    df = prepared_data['scheme_df'].copy()


    # ---------------------------------------------------
    # Date Ranges
    # ---------------------------------------------------

    lym_df = df[

        (

            df['SCHEMEOPENINGDATE']
            >= prepared_data['ly_month_start']

        )

        &

        (

            df['SCHEMEOPENINGDATE']
            <= prepared_data['ly_month_end']

        )

    ]


    ly_mtd_df = df[

        (

            df['SCHEMEOPENINGDATE']
            >= prepared_data['ly_start_date']

        )

        &

        (

            df['SCHEMEOPENINGDATE']
            <= prepared_data['ly_end_date']

        )

    ]


    ty_mtd_df = df[

        (

            df['SCHEMEOPENINGDATE']
            >= prepared_data['start_date']

        )

        &

        (

            df['SCHEMEOPENINGDATE']
            <= prepared_data['end_date']

        )

    ]


    # ---------------------------------------------------
    # Aggregation Function
    # ---------------------------------------------------

    def aggregate(dataframe, prefix):

        grouped = (

            dataframe

            .groupby(
                'location',
                as_index=False
            )

            .agg({

                'SCHEMEENTRYNO': 'nunique',

                'SchemefirstPayamt': 'sum'

            })

        )

        grouped.rename(

            columns={

                'SCHEMEENTRYNO': f'No_{prefix}',

                'SchemefirstPayamt': f'V_{prefix}'

            },

            inplace=True

        )

        return grouped


    # ---------------------------------------------------
    # Aggregate
    # ---------------------------------------------------

    lym = aggregate(lym_df, 'LYM')

    ly_mtd = aggregate(ly_mtd_df, 'LY_MTD')

    ty_mtd = aggregate(ty_mtd_df, 'TY_MTD')


    # ---------------------------------------------------
    # Merge
    # ---------------------------------------------------

    final_df = lym.merge(

        ly_mtd,

        on='location',

        how='outer'

    )

    final_df = final_df.merge(

        ty_mtd,

        on='location',

        how='outer'

    )


    final_df.fillna(0, inplace=True)


    # ---------------------------------------------------
    # Diff Columns
    # ---------------------------------------------------

    final_df['No_Diff'] = (

        final_df['No_TY_MTD']

        -

        final_df['No_LY_MTD']

    )


    final_df['V_Diff'] = (

        final_df['V_TY_MTD']

        -

        final_df['V_LY_MTD']

    )


    # ---------------------------------------------------
    # Merge with location code
    # ---------------------------------------------------
    code_map = rm_zm_df[['location', 'code']].drop_duplicates()
    final_df = final_df.merge(code_map, on='location', how='left')

    # ---------------------------------------------------
    # Rename
    # ---------------------------------------------------

    final_df.rename(

        columns={
            'location': 'Location',
            'code': 'Code'
        },

        inplace=True

    )

    # Reorder columns to place Code and Location first
    cols = ['Code', 'Location'] + [c for c in final_df.columns if c not in ['Code', 'Location']]
    final_df = final_df[cols]

    # ---------------------------------------------------
    # Sort
    # ---------------------------------------------------

    final_df = final_df.sort_values(
        'Code',
        na_position='last'
    )

    # ---------------------------------------------------
    # Total Row
    # ---------------------------------------------------

    total_row = pd.DataFrame([{

        'Code': '',

        'Location': 'TOTAL',

        'No_LYM': final_df['No_LYM'].sum(),

        'V_LYM': final_df['V_LYM'].sum(),

        'No_LY_MTD': final_df['No_LY_MTD'].sum(),

        'No_TY_MTD': final_df['No_TY_MTD'].sum(),

        'V_LY_MTD': final_df['V_LY_MTD'].sum(),

        'V_TY_MTD': final_df['V_TY_MTD'].sum(),

        'No_Diff': final_df['No_Diff'].sum(),

        'V_Diff': final_df['V_Diff'].sum()

    }])


    final_df = pd.concat(

        [

            final_df,

            total_row

        ],

        ignore_index=True

    )

    return final_df