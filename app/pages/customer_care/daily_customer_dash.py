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

import io

import dash_bootstrap_components as dbc

import pandas as pd

from backend.services.customer_care.customer import (
    prepare_customer_data,
    get_customer_kpis
)

from backend.cache.data_cache import (
    merged_sales_df
)


# ---------------------------------------------------
# Filter Options
# ---------------------------------------------------

location_options = [

    {
        'label': location,
        'value': location
    }

    for location in sorted(
        merged_sales_df['Location Name']
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
    className='inv-premium-page-red',
    children=dbc.Container(
        [
            # ---------------------------------------------------
            # Header Row
            # ---------------------------------------------------
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.A(
                                dbc.Button(
                                    "← Customer Care Department",
                                    className='inv-btn-dark px-3 py-1',
                                    size='sm'
                                ),
                                href="/customer-care",
                                style={'textDecoration': 'none'}
                            ),
                            html.H2(
                                "Daily Customer List",
                                className="fw-bold mt-3 mb-1"
                            )
                        ],
                        width=8
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                f"Last Updated : {last_updated_text}",
                                className='text-end fw-bold mb-2',
                                style={'color': '#f8d7da'}
                            ),
                            html.Div(
                                [
                                    dbc.Button(
                                        "Export Data",
                                        id="export-customer-btn",
                                        className="inv-btn-dark px-3 py-1 me-2 shadow-sm",
                                        size="sm"
                                    ),
                                    dbc.Button(
                                        "Enter",
                                        id="customer-enter-btn",
                                        className="inv-btn-gold px-3 py-1 shadow-sm",
                                        size="sm"
                                    )
                                ],
                                className="text-end"
                            )
                        ],
                        width=4
                    )
                ],
                className='mb-4 mt-2 align-items-end'
            ),

            dcc.Download(
                id="download-customer-data"
            ),

            # ---------------------------------------------------
            # Filters Panel
            # ---------------------------------------------------
            dbc.Card(
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Date Range", className="fw-bold mb-1 small text-muted"),
                                    dcc.DatePickerRange(
                                        id='customer-date-filter',
                                        display_format='DD-MMM-YYYY',
                                        className="w-100"
                                    )
                                ],
                                width=4,
                                className="mb-2 mb-md-0"
                            ),
                            dbc.Col(
                                [
                                    html.Label("Location", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='customer-location-filter',
                                        options=location_options,
                                        multi=True,
                                        placeholder='Select Location'
                                    )
                                ],
                                width=4,
                                className="mb-2 mb-md-0"
                            ),
                            dbc.Col(
                                [
                                    html.Label("Search Customer", className="fw-bold mb-1 small text-muted"),
                                    dbc.Input(
                                        id='customer-search-filter',
                                        placeholder='Search Customer Code / Phone...',
                                        type='text',
                                        style={'height': '38px', 'borderRadius': '8px', 'backgroundColor': '#FFFFFF', 'color': '#1C1B19', 'border': '1px solid #E3DFD5'}
                                    )
                                ],
                                width=4,
                                className="mb-2 mb-md-0"
                            )
                        ]
                    )
                ),
                className="inv-premium-card mb-4"
            ),

        # ---------------------------------------------------
        # KPI Loading
        # ---------------------------------------------------

        dcc.Loading(

            children=[

                html.Div(
                    id='customer-kpi-container'
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
                    id='customer-table-container'
                )

            ],

            type='default'

        )

    ],
    fluid=True
    )
)


# ---------------------------------------------------
# KPI Card
# ---------------------------------------------------

def create_kpi_card(title, value, subtitle=None):
    card_content = [
        html.Div(
            title,
            style={
                'fontWeight': '600',
                'fontSize': '11px',
                'textAlign': 'center',
                'color': '#f8d7da',
                'textTransform': 'uppercase',
                'letterSpacing': '0.05em',
                'marginBottom': '4px'
            }
        ),
        html.Div(
            value,
            style={
                'fontSize': '20px',
                'fontWeight': '700',
                'textAlign': 'center',
                'color': '#FFFFFF',
                'lineHeight': '24px'
            }
        )
    ]
    if subtitle:
        card_content.append(
            html.Div(
                subtitle,
                style={
                    'fontSize': '11px',
                    'fontWeight': '500',
                    'textAlign': 'center',
                    'color': '#ffc107',
                    'marginTop': '4px'
                }
            )
        )
    return dbc.Card(
        dbc.CardBody(
            card_content,
            style={'padding': '12px 16px'}
        ),
        style={
            'borderRadius': '12px',
            'backgroundColor': 'rgba(255, 255, 255, 0.08)',
            'border': '1px solid rgba(255, 255, 255, 0.15)',
            'boxShadow': '0 4px 20px rgba(0, 0, 0, 0.15)',
            'height': '100%',
            'marginBottom': '4px'
        }
    )


# ---------------------------------------------------
# Main Callback
# ---------------------------------------------------

@callback(

    [

        Output(
            'customer-kpi-container',
            'children'
        ),

        Output(
            'customer-table-container',
            'children'
        )

    ],

    Input(
        'customer-enter-btn',
        'n_clicks'
    ),

    [

        State(
            'customer-date-filter',
            'start_date'
        ),

        State(
            'customer-date-filter',
            'end_date'
        ),

        State(
            'customer-location-filter',
            'value'
        ),

        State(
            'customer-search-filter',
            'value'
        )

    ]

)

def update_customer_dashboard(

    n_clicks,

    start_date,

    end_date,

    locations,

    search_query

):

    # ---------------------------------------------------
    # Prepare Data
    # ---------------------------------------------------

    df = prepare_customer_data(

        start_date=start_date,

        end_date=end_date,

        locations=locations,

        search_query=search_query

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
    # KPIs
    # ---------------------------------------------------

    kpis = get_customer_kpis(df)

    unique_custs = kpis['unique_customers']
    old_pct = (kpis['old_customers'] / unique_custs * 100) if unique_custs > 0 else 0
    new_pct = (kpis['new_customers'] / unique_custs * 100) if unique_custs > 0 else 0

    kpi_cards = dbc.Row(
        [
            dbc.Col(
                create_kpi_card(
                    "Customers",
                    f"{kpis['customers']:,}"
                ),
                style={'flex': '1', 'padding': '4px'}
            ),
            dbc.Col(
                create_kpi_card(
                    "Unique Customers",
                    f"{kpis['unique_customers']:,}"
                ),
                style={'flex': '1', 'padding': '4px'}
            ),
            dbc.Col(
                create_kpi_card(
                    "Old Customers",
                    f"{kpis['old_customers']:,}",
                    f"{old_pct:.1f}% of Unique"
                ),
                style={'flex': '1', 'padding': '4px'}
            ),
            dbc.Col(
                create_kpi_card(
                    "New Customers",
                    f"{kpis['new_customers']:,}",
                    f"{new_pct:.1f}% of Unique"
                ),
                style={'flex': '1', 'padding': '4px'}
            )
        ],
        className="mb-3 g-2"
    )


    # ---------------------------------------------------
    # Table
    # ---------------------------------------------------

    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[
            {
                'name': col,
                'id': col
            }
            for col in df.columns
        ],
        fixed_rows={
            'headers': True
        },
        style_table={
            'overflowX': 'auto',
            'overflowY': 'auto',
            'maxHeight': '600px',
            'width': '100%',
            'minWidth': '100%',
            'border': '1px solid #5a0b0b',
            'borderRadius': '8px'
        },
        style_cell={
            'textAlign': 'center',
            'padding': '6px 8px',
            'fontSize': '11px',
            'fontFamily': "'Outfit', 'Inter', sans-serif",
            'whiteSpace': 'normal',
            'height': '30px',
            'minWidth': '110px',
            'width': '130px',
            'maxWidth': '160px',
            'backgroundColor': '#FFFFFF',
            'color': '#1C1B19',
            'border': '1px solid #E3DFD5'
        },
        style_header={
            'fontWeight': 'bold',
            'backgroundColor': '#FAF9F6',
            'color': '#1C1B19',
            'border': '1px solid #D9D4C7',
            'position': 'sticky',
            'top': 0,
            'zIndex': 1
        },
        style_cell_conditional=[
            {
                'if': {
                    'column_id': 'Location'
                },
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'column_id': 'Customer Code'
                },
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'column_id': 'Customer Name'
                },
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'column_id': 'Phone Number'
                },
                'fontWeight': 'bold'
            }
        ],
        page_size=100
    )


    return (

        kpi_cards,

        table

    )


# ---------------------------------------------------
# Export Callback
# ---------------------------------------------------

@callback(

    Output(
        "download-customer-data",
        "data"
    ),

    Input(
        "export-customer-btn",
        "n_clicks"
    ),

    [

        State(
            'customer-date-filter',
            'start_date'
        ),

        State(
            'customer-date-filter',
            'end_date'
        ),

        State(
            'customer-location-filter',
            'value'
        ),

        State(
            'customer-search-filter',
            'value'
        )

    ],

    prevent_initial_call=True

)

def export_customer_data(

    n_clicks,

    start_date,

    end_date,

    locations,

    search_query

):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "Daily Customer Dashboard",
        action="Export Data",
        filters={"start_date": start_date, "end_date": end_date, "locations": locations, "search_query": search_query}
    )


    df = prepare_customer_data(

        start_date=start_date,

        end_date=end_date,

        locations=locations,

        search_query=search_query

    )


    output = io.BytesIO()


    with pd.ExcelWriter(

        output,

        engine='openpyxl'

    ) as writer:

        df.to_excel(

            writer,

            sheet_name='Daily Customer List',

            index=False

        )


    output.seek(0)


    return dcc.send_bytes(

        output.getvalue(),

        "daily_customer_list.xlsx"

    )

# ---------------------------------------------------
# Dynamic Location Dropdown Options RLS
# ---------------------------------------------------
from dash import callback, Output, Input

@callback(
    Output('customer-location-filter', 'options'),
    Input('customer-location-filter', 'id')
)
def populate_customer_location_filter_options(_):
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
