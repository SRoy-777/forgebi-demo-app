from dash import (

    html,
    dcc,
    dash_table,
    callback,
    Input,
    Output,
    State

)

import pandas as pd

import dash_bootstrap_components as dbc
from flask import session

from backend.cache.data_cache import (

    tag_sold_df,
    tag_received_df

)

from backend.services.sales.basket_analysis import (

    prepare_bucket_data,

    generate_bucket_kpis,

    generate_all_bucket_tables,

    COUNTER_ORDER

)


# ---------------------------------------------------
# Filter Options
# ---------------------------------------------------

location_options = sorted(

    tag_received_df['location_name']

    .dropna()

    .unique()

)


counter_options = COUNTER_ORDER


category_options = sorted(

    tag_received_df['ornament_category_code']

    .dropna()

    .unique()

)


subcategory_options = sorted(

    tag_received_df['ornament_sub_category_code']

    .dropna()

    .unique()

)


# ---------------------------------------------------
# Default Dates
# ---------------------------------------------------

latest_invoice_date = pd.to_datetime(

    tag_sold_df['invoice_date']

).max()


default_start_date = latest_invoice_date.replace(

    day=1

)


# ---------------------------------------------------
# Layout
# ---------------------------------------------------

layout = dbc.Container(

    [

        # ---------------------------------------------------
        # Header
        # ---------------------------------------------------

        dbc.Row(

            [

                dbc.Col(

                    html.H2(

                        "Basket Analysis Dashboard",

                        className='fw-bold'

                    ),

                    width=6

                ),

                dbc.Col(

                    [

                        html.Div(

                            f"Last Updated : {latest_invoice_date.strftime('%d-%b-%Y')}",

                            className='text-end fw-bold mb-2'

                        ),

                        html.Div(

                            dbc.Button(

                                "Export Data",

                                id='basket-analysis-export-btn',

                                color='dark',

                                size='sm'

                            ),

                            className='text-end'

                        ),

                        dcc.Download(

                            id='basket-analysis-download'

                        )

                    ],

                    width=6

                )

            ],

            className='mb-3 mt-2'

        ),

        # ---------------------------------------------------
        # Filters
        # ---------------------------------------------------

        dbc.Card(

            dbc.CardBody(

                [

                    dbc.Row(

                        [

                            dbc.Col(

                                dcc.DatePickerRange(

                                    id='basket-analysis-date-filter',

                                    start_date=default_start_date,

                                    end_date=latest_invoice_date

                                ),

                                width=3

                            ),

                            dbc.Col(

                                dcc.Dropdown(

                                    id='basket-analysis-location-filter',

                                    options=[

                                        {

                                            'label': i,

                                            'value': i

                                        }

                                        for i in location_options

                                    ],

                                    multi=True,

                                    placeholder='Select Location'

                                ),

                                width=2

                            ),

                            dbc.Col(

                                dcc.Dropdown(

                                    id='basket-analysis-counter-filter',

                                    options=[

                                        {

                                            'label': i,

                                            'value': i

                                        }

                                        for i in counter_options

                                    ],

                                    multi=True,

                                    placeholder='Select Counter'

                                ),

                                width=2

                            ),

                            dbc.Col(

                                dcc.Dropdown(

                                    id='basket-analysis-category-filter',

                                    options=[

                                        {

                                            'label': i,

                                            'value': i

                                        }

                                        for i in category_options

                                    ],

                                    multi=True,

                                    placeholder='Select Category'

                                ),

                                width=2

                            ),

                            dbc.Col(

                                dcc.Dropdown(

                                    id='basket-analysis-subcategory-filter',

                                    options=[

                                        {

                                            'label': i,

                                            'value': i

                                        }

                                        for i in subcategory_options

                                    ],

                                    multi=True,

                                    placeholder='Select Subcategory'

                                ),

                                width=2

                            ),

                            dbc.Col(

                                dbc.Button(

                                    "Enter",

                                    id='basket-analysis-enter-btn',

                                    color='dark',

                                    className='w-100'

                                ),

                                width=1

                            )

                        ]

                    )

                ]

            ),

            className='shadow-sm mb-3'

        ),

        # ---------------------------------------------------
        # KPI Section
        # ---------------------------------------------------

        html.Div(

            id='basket-analysis-kpi-container'

        ),

        # ---------------------------------------------------
        # Table Section
        # ---------------------------------------------------

        dcc.Loading(

            html.Div(

                id='basket-analysis-table-container'

            ),

            type='default'

        )

    ],

    fluid=True

)

# ---------------------------------------------------
# Main Callback
# ---------------------------------------------------

@callback(

    Output(

        'basket-analysis-kpi-container',

        'children'

    ),

    Output(

        'basket-analysis-table-container',

        'children'

    ),

    Input(

        'basket-analysis-date-filter',

        'start_date'

    ),

    Input(

        'basket-analysis-enter-btn',

        'n_clicks'

    ),

    State(

        'basket-analysis-date-filter',

        'end_date'

    ),

    State(

        'basket-analysis-location-filter',

        'value'

    ),

    State(

        'basket-analysis-counter-filter',

        'value'

    ),

    State(

        'basket-analysis-category-filter',

        'value'

    ),

    State(

        'basket-analysis-subcategory-filter',

        'value'

    ),

    prevent_initial_call=False

)

def render_basket_analysis(

    start_date,

    n_clicks,

    end_date,

    locations,

    counters,

    categories,

    sub_categories

):

    # ---------------------------------------------------
    # RLS
    # ---------------------------------------------------

    allowed_locations = session.get(

        'locations',

        []

    )


    if 'ALL' not in allowed_locations:

        if locations:

            locations = [

                loc

                for loc in locations

                if loc in allowed_locations

            ]

        else:

            locations = allowed_locations

    # ---------------------------------------------------
    # Prepare Data
    # ---------------------------------------------------

    (

        filtered_sold_df,

        filtered_received_df,

        existing_received_df

    ) = prepare_bucket_data(

        sold_df=tag_sold_df,

        received_df=tag_received_df,

        start_date=start_date,

        end_date=end_date,

        locations=locations,

        counters=counters,

        categories=categories,

        sub_categories=sub_categories

    )


    # ---------------------------------------------------
    # KPI Data
    # ---------------------------------------------------

    kpi_data = generate_bucket_kpis(

        sold_df=filtered_sold_df,

        received_df=filtered_received_df,

        existing_received_df=existing_received_df

    )


    # ---------------------------------------------------
    # Tables
    # ---------------------------------------------------

    all_tables = generate_all_bucket_tables(

        sold_df=filtered_sold_df,

        received_df=filtered_received_df,

        existing_received_df=existing_received_df

    )

        # ---------------------------------------------------
    # KPI Card Helper
    # ---------------------------------------------------

    def create_kpi_card(

        title,

        bucket,

        value

    ):

        return dbc.Card(

            dbc.CardBody(

                [

                    html.Div(

                        title,

                        style={

                            'fontSize': '11px',

                            'fontWeight': 'bold',

                            'textAlign': 'center',

                            'marginBottom': '4px'

                        }

                    ),

                    html.Div(

                        bucket,

                        style={

                            'fontSize': '12px',

                            'fontWeight': 'bold',

                            'textAlign': 'center',

                            'minHeight': '38px',

                            'lineHeight': '16px'

                        }

                    ),

                    html.Div(

                        f"{value:,.2f}"

                        if isinstance(value, float)

                        else f"{value:,.0f}",

                        style={

                            'fontSize': '14px',

                            'fontWeight': 'bold',

                            'textAlign': 'center'

                        }

                    )

                ],

                style={

                    'padding': '8px'

                }

            ),

            style={

                'backgroundColor': '#ffe082',

                'border': 'none',

                'borderRadius': '8px'

            },

            className='h-100'

        )


    # ---------------------------------------------------
    # KPI Rows
    # ---------------------------------------------------

    kpi_rows = []


    kpi_sections = [

        ('SALE', 'sale'),

        ('RECEIVED', 'received'),

        ('EXISTING', 'existing')

    ]


    kpi_columns = [

        ('Best Pcs', 'best_pcs'),

        ('Best Weight', 'best_weight'),

        ('Worst Pcs', 'worst_pcs'),

        ('Worst Weight', 'worst_weight')

    ]


    for section_title, section_key in kpi_sections:

        row_cards = []


        for display_name, metric_key in kpi_columns:

            metric_data = kpi_data.get(

                section_key,

                {}

            ).get(

                metric_key,

                {

                    'bucket': '-',

                    'value': 0,

                    'pcs': 0,

                    'weight': 0

                }

            )


            value = (

                metric_data.get('value')

                if section_key == 'sale'

                else

                metric_data.get('pcs')

                if 'Pcs' in display_name

                else

                metric_data.get('weight')

            )


            row_cards.append(

                dbc.Col(

                    create_kpi_card(

                        title=display_name,

                        bucket=metric_data['bucket'],

                        value=value

                    ),

                    width=3

                )

            )


        kpi_rows.append(

            dbc.Card(

                dbc.CardBody(

                    dbc.Row(

                        [

                            dbc.Col(

                                html.Div(

                                    f"{section_title} :",

                                    style={

                                        'fontWeight': 'bold',

                                        'fontSize': '14px',

                                        'paddingTop': '28px',

                                        'textAlign': 'center'

                                    }

                                ),

                                width=1

                            ),

                            dbc.Col(

                                dbc.Row(

                                    row_cards,

                                    className='g-2'

                                ),

                                width=11

                            )

                        ],

                        className='align-items-center'

                    ),

                    style={

                        'padding': '8px'

                    }

                ),

                style={

                    'backgroundColor': '#ffe082',

                    'border': 'none',

                    'borderRadius': '10px'

                },

                className='mb-3 shadow-sm'

            )

        )


    # ---------------------------------------------------
    # KPI Section
    # ---------------------------------------------------

    kpi_section = html.Div(

        kpi_rows

    )

        # ---------------------------------------------------
    # Table Cards
    # ---------------------------------------------------

    cards = []


    for counter in COUNTER_ORDER:

        if counter not in all_tables:

            continue


        df = all_tables[counter]


        if df.empty:

            continue


        table = dash_table.DataTable(

            data=df.to_dict('records'),

            columns=[

                {

                    'name': i,

                    'id': i

                }

                for i in df.columns

                if i != 'Subcat_Bucket'

            ],

            fixed_rows={

                'headers': True

            },

            fixed_columns={

                'headers': True,

                'data': 1

            },

            page_action='none',

            style_table={

                'overflowX': 'auto',

                'overflowY': 'auto',

                'height': '420px',

                'width': '100%',

                'minWidth': '100%'

            },

            style_cell={

                'textAlign': 'center',

                'padding': '4px',

                'fontSize': '11px',

                'fontFamily': 'Arial',

                'whiteSpace': 'normal',

                'height': '30px',

                'minWidth': '90px',

                'width': '100px',

                'maxWidth': '120px'

            },

            style_data={

                'padding': '4px',

                'height': '30px'

            },

            style_header={

                'fontWeight': 'bold',

                'backgroundColor': '#f8f9fa',

                'position': 'sticky',

                'top': 0,

                'zIndex': 1

            },

            style_data_conditional=[

                # ---------------------------------------------------
                # Total Row
                # ---------------------------------------------------

                {

                    'if': {

                        'filter_query': '{Location} contains "TOTAL"'

                    },

                    'fontWeight': 'bold',

                    'backgroundColor': '#f1f1f1'

                },

                # ---------------------------------------------------
                # Weight Range Column
                # ---------------------------------------------------

                {

                    'if': {

                        'column_id': 'Bucket'

                    },

                    'fontWeight': 'bold'

                }

            ]

        )


        card = dbc.Col(

            dbc.Card(

                [

                    dbc.CardHeader(

                        html.H6(

                            counter,

                            className='fw-bold mb-0'

                        ),

                        style={

                            'padding': '8px 12px',

                            'backgroundColor': '#f8f9fa'

                        }

                    ),

                    dbc.CardBody(

                        table,

                        style={

                            'padding': '6px'

                        }

                    )

                ],

                className='shadow-sm h-100',

                style={

                    'borderRadius': '10px'

                }

            ),

            xs=12,
            sm=12,
            md=6,
            lg=6,
            xl=6,

            className='mb-3'

        )


        cards.append(

            card

        )


    # ---------------------------------------------------
    # Final Return
    # ---------------------------------------------------

    return (

        kpi_section,

        dbc.Row(

            cards

        )

    )

# ---------------------------------------------------
# Export Callback
# ---------------------------------------------------

@callback(

    Output(

        'basket-analysis-download',

        'data'

    ),

    Input(

        'basket-analysis-export-btn',

        'n_clicks'

    ),

    State(

        'basket-analysis-date-filter',

        'start_date'

    ),

    State(

        'basket-analysis-date-filter',

        'end_date'

    ),

    State(

        'basket-analysis-location-filter',

        'value'

    ),

    State(

        'basket-analysis-counter-filter',

        'value'

    ),

    State(

        'basket-analysis-category-filter',

        'value'

    ),

    State(

        'basket-analysis-subcategory-filter',

        'value'

    ),

    prevent_initial_call=True

)

def export_basket_analysis(

    n_clicks,

    start_date,

    end_date,

    locations,

    counters,

    categories,

    sub_categories

):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "Basket Analysis Dashboard",
        action="Export Data",
        filters={"start_date": start_date, "end_date": end_date, "locations": locations, "counters": counters, "categories": categories, "sub_categories": sub_categories}
    )

    
    # ---------------------------------------------------
    # RLS
    # ---------------------------------------------------

    allowed_locations = session.get(

        'locations',

        []

    )


    if 'ALL' not in allowed_locations:

        if locations:

            locations = [

                loc

                for loc in locations

                if loc in allowed_locations

            ]

        else:

            locations = allowed_locations

    # ---------------------------------------------------
    # Prepare Data
    # ---------------------------------------------------

    (

        filtered_sold_df,

        filtered_received_df,

        existing_received_df
        

    ) = prepare_bucket_data(

        sold_df=tag_sold_df,

        received_df=tag_received_df,

        start_date=start_date,

        end_date=end_date,

        locations=locations,

        counters=counters,

        categories=categories,

        sub_categories=sub_categories

    )


    # ---------------------------------------------------
    # Generate Tables
    # ---------------------------------------------------

    all_tables = generate_all_bucket_tables(

        sold_df=filtered_sold_df,

        received_df=filtered_received_df,

        existing_received_df=existing_received_df

    )


    # ---------------------------------------------------
    # Merge Export
    # ---------------------------------------------------

    export_dfs = []


    for counter in COUNTER_ORDER:

        if counter not in all_tables:

            continue


        df = all_tables[counter]


        if df.empty:

            continue


        temp_df = df.copy()

        temp_df['Dashboard Counter'] = counter

        export_dfs.append(

            temp_df

        )


    # ---------------------------------------------------
    # Empty Check
    # ---------------------------------------------------

    if not export_dfs:

        return None


    # ---------------------------------------------------
    # Final Export
    # ---------------------------------------------------

    final_export_df = pd.concat(

        export_dfs,

        ignore_index=True

    )


    return dcc.send_data_frame(

        final_export_df.to_csv,

        'basket_analysis_export.csv',

        index=False

    )

# ---------------------------------------------------
# Dynamic Location Dropdown Options RLS
# ---------------------------------------------------
from dash import callback, Output, Input

@callback(
    Output('basket-analysis-location-filter', 'options'),
    Input('basket-analysis-location-filter', 'id')
)
def populate_basket_analysis_location_filter_options(_):
    from flask import session
    from backend.cache.data_cache import rm_zm_df
    allowed_locations = session.get('locations', [])
    if not allowed_locations:
        return []
    if 'ALL' in allowed_locations:
        locs = sorted(rm_zm_df['location'].dropna().unique().tolist())
    else:
        locs = sorted(allowed_locations)
    return [{'label': i, 'value': i} for i in locs]
