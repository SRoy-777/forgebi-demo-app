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

from dash import (
    html,
    dcc,
    dash_table,
    callback,
    Input,
    Output,
    State
)

from backend.services.rls import (
    get_allowed_locations
)

import io

import dash_bootstrap_components as dbc

import pandas as pd

from backend.services.inventory.aging_stock import (
    prepare_aging_data,
    get_counter_kpis
)

from backend.cache.data_cache import tag_list_df


# ---------------------------------------------------
# Filter Options
# ---------------------------------------------------

location_options = [

    {
        'label': location,
        'value': location
    }

    for location in sorted(
        tag_list_df['location_name']
        .dropna()
        .unique()
    )

]

counter_options = [

    {
        'label': counter,
        'value': counter
    }

    for counter in sorted(
        tag_list_df['counter_code']
        .dropna()
        .unique()
    )

]


category_options = [

    {
        'label': category,
        'value': category
    }

    for category in sorted(
        tag_list_df['ornament_category_code']
        .dropna()
        .unique()
    )

]


sub_category_options = [

    {
        'label': sub_category,
        'value': sub_category
    }

    for sub_category in sorted(
        tag_list_df['ornament_sub_category_code']
        .dropna()
        .unique()
    )

]


# ---------------------------------------------------
# Last Updated
# ---------------------------------------------------

last_updated = pd.Timestamp.now()

last_updated_text = last_updated.strftime(
    "%d-%b-%Y %I:%M %p"
)


# ---------------------------------------------------
# Layout
# ---------------------------------------------------

layout = html.Div(
    className='inv-premium-page-blue',
    children=dbc.Container(

    [

        # ---------------------------------------------------
        # Header
        # ---------------------------------------------------

        dbc.Row(

            [

                dbc.Col(

                    html.H2(

                        "Aging Stock Analysis",

                        className='fw-bold mt-3 mb-1',

                        style={'fontFamily': 'Outfit', 'color': '#0F172A'}

                    ),

                    width=8

                ),

                dbc.Col(

                    html.Div(

                        [

                            html.Div(

                                f"Last Updated: {last_updated_text}",

                                className='fw-bold small mb-1',

                                style={'color': '#1E3A8A', 'fontFamily': 'Outfit'}

                            ),

                            dcc.Loading(

                                type="circle",

                                children=[

                                    dbc.Button(

                                        "Export Data",

                                        id="export-aging-btn",

                                        className="inv-btn-blue-dark px-3 py-1 shadow-sm mt-1",

                                        size="sm"

                                    )

                                ]

                            )

                        ],

                        style={

                            'display': 'flex',

                            'flexDirection': 'column',

                            'alignItems': 'flex-end'

                        }

                    ),

                    width=4

                )

            ],

            className="mb-4 mt-2 align-items-end"

        ),

        dcc.Download(
            id="download-aging-data"
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
                                [
                                    html.Label("From Date", className="fw-bold mb-1 small text-muted"),
                                    dcc.DatePickerSingle(
                                        id='aging-from-date',
                                        display_format='DD-MMM-YYYY',
                                        date=pd.Timestamp.today()
                                    ),
                                ],
                                width=2
                            ),
                            dbc.Col(
                                [
                                    html.Label("Days", className="fw-bold mb-1 small text-muted"),
                                    dbc.Input(
                                        id='aging-days',
                                        type='number',
                                        placeholder='Days'
                                    ),
                                ],
                                width=1
                            ),
                            dbc.Col(
                                [
                                    html.Label("Location", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='aging-location-filter',
                                        options=location_options,
                                        multi=True,
                                        placeholder='Select Location'
                                    ),
                                ],
                                width=2
                            ),
                            dbc.Col(
                                [
                                    html.Label("Counter", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='aging-counter-filter',
                                        options=counter_options,
                                        multi=True,
                                        placeholder='Select Counter'
                                    ),
                                ],
                                width=2
                            ),
                            dbc.Col(
                                [
                                    html.Label("Category", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='aging-category-filter',
                                        options=category_options,
                                        multi=True,
                                        placeholder='Select Category'
                                    ),
                                ],
                                width=2
                            ),
                            dbc.Col(
                                [
                                    html.Label("Sub Category", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='aging-subcategory-filter',
                                        options=sub_category_options,
                                        multi=True,
                                        placeholder='Select Sub Category'
                                    ),
                                ],
                                width=2
                            ),
                            dbc.Col(
                                [
                                    html.Label(" ", className="fw-bold mb-1 small text-muted d-block"),
                                    dbc.Button(
                                        "Enter",
                                        id='aging-enter-btn',
                                        className='inv-btn-blue px-4 py-1 shadow-sm w-100',
                                        size='sm',
                                    ),
                                ],
                                width=1
                            )
                        ],
                        className="g-3 align-items-end"
                    )
                ]
            ),
            className='inv-blue-card mb-4'
        ),

        # ---------------------------------------------------
        # KPI Loading
        # ---------------------------------------------------

        dcc.Loading(

            children=[

                html.Div(
                    id='aging-kpi-container'
                )

            ],

            type='default'

        ),

        html.Br(),

        # ---------------------------------------------------
        # Table Loading
        # ---------------------------------------------------

        dcc.Loading(

            children=[

                html.Div(
                    id='aging-table-container'
                )

            ],

            type='default'

        )

    ],

    fluid=True,
    style={'padding': '0px'}

)
)


# ---------------------------------------------------
# KPI Card
# ---------------------------------------------------

def create_kpi_card(title, value, bg_color):
    # Map original background colors to theme text colors for consistency
    text_color = '#1E3A8A'  # Slate/navy blue
    if bg_color == '#ffe95c':
        text_color = '#0EA5E9'  # Ocean/sky blue for dynamic counters

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    title,
                    className="text-muted small fw-bold mb-1 text-center",
                    style={'fontFamily': 'Outfit'}
                ),
                html.H3(
                    value,
                    className="fw-bold text-center mb-0",
                    style={'color': text_color, 'fontFamily': 'Outfit', 'fontSize': '22px'}
                )
            ],
            style={'padding': '12px'}
        ),
        className="shadow-sm border-0 bg-white mb-2 inv-hover-card"
    )


# ---------------------------------------------------
# Main Callback
# ---------------------------------------------------

@callback(

    [

        Output(
            'aging-kpi-container',
            'children'
        ),

        Output(
            'aging-table-container',
            'children'
        )

    ],

    Input(
        'aging-enter-btn',
        'n_clicks'
    ),

    [

        State(
            'aging-from-date',
            'date'
        ),

        State(
            'aging-days',
            'value'
        ),

        State(
            'aging-location-filter',
            'value'
        ),

        State(
            'aging-counter-filter',
            'value'
        ),

        State(
            'aging-category-filter',
            'value'
        ),

        State(
            'aging-subcategory-filter',
            'value'
        )

    ]

)

def update_aging_dashboard(

    n_clicks,

    from_date,

    days,

    locations,

    counters,

    categories,

    sub_categories

):

    # ---------------------------------------------------
    # Defaults
    # ---------------------------------------------------

    if not from_date:

        from_date = pd.Timestamp.today()

    if not days:

        days = 0


    # ---------------------------------------------------
    # Prepare Data
    # ---------------------------------------------------

    df = prepare_aging_data(

        from_date=from_date,

        days=days,

        locations=locations,

        counters=counters,

        categories=categories,

        sub_categories=sub_categories

    )


    # ---------------------------------------------------
    # Empty DF
    # ---------------------------------------------------

    if df.empty:

        return (

            html.Div("No Data Found"),

            html.Div("No Data Found")

        )


    # ---------------------------------------------------
    # Static KPI Row
    # ---------------------------------------------------

    static_cards = dbc.Row(

        [

            dbc.Col(

                create_kpi_card(

                    "Total Tags",

                    f"{len(df):,}",

                    '#d6ecff'

                ),

                style={'flex': '1', 'padding': '4px'}

            ),

            dbc.Col(

                create_kpi_card(

                    "Avg Age",

                    round(df['Age'].mean(), 0),

                    '#d6ecff'

                ),

                style={'flex': '1', 'padding': '4px'}

            ),

            dbc.Col(

                create_kpi_card(

                    "Min Age",

                    int(df['Age'].min()),

                    '#d6ecff'

                ),

                style={'flex': '1', 'padding': '4px'}

            ),

            dbc.Col(

                create_kpi_card(

                    "Max Age",

                    int(df['Age'].max()),

                    '#d6ecff'

                ),

                style={'flex': '1', 'padding': '4px'}

            ),

            dbc.Col(

                create_kpi_card(

                    "Avg Shelf Life",

                    round(df['Shelf Life'].mean(), 0),

                    '#d6ecff'

                ),

                style={'flex': '1', 'padding': '4px'}

            )

        ],

        className="mb-2"

    )


    # ---------------------------------------------------
    # Dynamic Counter KPIs
    # ---------------------------------------------------

    counter_kpis = get_counter_kpis(df)

    dynamic_cards = dbc.Row(

        [

            dbc.Col(

                create_kpi_card(

                    row['Counter Code'],

                    row['Tag Count'],

                    '#ffe95c'

                ),

                style={

                    'flex': '1',

                    'minWidth': '120px',

                    'maxWidth': '140px',

                    'padding': '2px'

                }

            )

            for _, row in counter_kpis.iterrows()

        ],

        style={

            'display': 'flex',

            'flexWrap': 'wrap'

        }

    )


    # ---------------------------------------------------
    # Table
    # ---------------------------------------------------

    table = dbc.Card([
        dbc.CardHeader(
            html.H5(
                "Aging Stock Report Overview",
                className='fw-bold mb-0',
                style={'textAlign': 'left', 'color': '#0F172A', 'fontFamily': 'Outfit'},
            ),
            style={'backgroundColor': '#F8FAFC', 'borderBottom': '1px solid #E2E8F0'},
        ),
        dbc.CardBody(
            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[
                    {
                        'name': col,
                        'id': col
                    }
                    for col in df.columns
                ],
                fixed_rows={'headers': True},
                style_as_list_view=True,
                style_table={
                    'overflowX': 'auto',
                    'overflowY': 'auto',
                    'maxHeight': '700px',
                    'width': '100%',
                    'margin': '0 auto',
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px 14px',
                    'fontSize': '12px',
                    'fontFamily': "'Outfit', 'Inter', sans-serif",
                    'minWidth': '120px',
                    'width': '120px',
                    'maxWidth': '120px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'backgroundColor': '#FFFFFF',
                    'color': '#334155',
                    'borderBottom': '1px solid #F1F5F9',
                },
                style_header={
                    'fontWeight': 'bold',
                    'backgroundColor': '#1E293B',
                    'color': '#F8FAFC',
                    'fontSize': '12px',
                    'textAlign': 'center',
                    'fontFamily': "'Outfit', sans-serif",
                    'border': '1px solid #CBD5E1',
                    'padding': '12px 14px',
                },
                style_cell_conditional=[
                    {
                        'if': {
                            'column_id': 'Location Name'
                        },
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {
                            'column_id': 'Counter Code'
                        },
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {
                            'column_id': 'Ornament Category Code'
                        },
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {
                            'column_id': 'Ornament Sub Category Code'
                        },
                        'fontWeight': 'bold'
                    }
                ],
                page_size=100
            ),
            style={'padding': '6px'},
        ),
    ], className='inv-blue-card mb-4')


    return (

        [

            static_cards,

            dynamic_cards

        ],

        table

    )


# ---------------------------------------------------
# Export Callback
# ---------------------------------------------------

@callback(

    Output(
        "download-aging-data",
        "data"
    ),

    Input(
        "export-aging-btn",
        "n_clicks"
    ),

    [

        State(
            'aging-from-date',
            'date'
        ),

        State(
            'aging-days',
            'value'
        ),

        State(
            'aging-location-filter',
            'value'
        ),

        State(
            'aging-counter-filter',
            'value'
        ),

        State(
            'aging-category-filter',
            'value'
        ),

        State(
            'aging-subcategory-filter',
            'value'
        )

    ],

    prevent_initial_call=True

)

def export_aging_data(

    n_clicks,

    from_date,

    days,

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
        "Aging Stock Analysis Dashboard",
        action="Export Data",
        filters={"from_date": from_date, "days": days, "locations": locations, "counters": counters, "categories": categories, "sub_categories": sub_categories}
    )


    if not from_date:

        from_date = pd.Timestamp.today()

    if not days:

        days = 0


    df = prepare_aging_data(

        from_date=from_date,

        days=days,

        locations=locations,

        counters=counters,

        categories=categories,

        sub_categories=sub_categories

    )


    output = io.BytesIO()


    with pd.ExcelWriter(

        output,

        engine='openpyxl'

    ) as writer:

        df.to_excel(

            writer,

            sheet_name='Aging Stock',

            index=False

        )


    output.seek(0)


    return dcc.send_bytes(

        output.getvalue(),

        "aging_stock_export.xlsx"

    )

# ---------------------------------------------------
# Dynamic Location Dropdown Options RLS
# ---------------------------------------------------
from dash import callback, Output, Input

@callback(
    Output('aging-location-filter', 'options'),
    Input('aging-location-filter', 'id')
)
def populate_aging_location_filter_options(_):
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
