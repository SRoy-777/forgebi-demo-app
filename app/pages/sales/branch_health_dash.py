# pages/branch_health_dash.py

from dash import (

    html,
    dcc,
    dash_table,

    callback,

    Input,
    Output,
    State

)

from dash.dash_table.Format import Format, Scheme

import pandas as pd

import dash_bootstrap_components as dbc

from backend.cache.data_cache import (

    branch_daily_aggregate_df,
    rm_zm_df

)

from backend.services.sales.branch_health_service import (

    generate_branch_health_dashboard_data

)

# ---------------------------------------------------
# Indian Formatting
# ---------------------------------------------------

def indian_format(

    value,
    decimals=0

):

    try:

        value = float(value)

    except:

        return value

    negative = value < 0

    value = abs(value)

    integer_part = int(value)

    decimal_part = round(

        value - integer_part,
        decimals

    )

    integer_str = str(integer_part)

    if len(integer_str) > 3:

        last_three = integer_str[-3:]

        remaining = integer_str[:-3]

        parts = []

        while len(remaining) > 2:

            parts.insert(

                0,
                remaining[-2:]

            )

            remaining = remaining[:-2]

        if remaining:

            parts.insert(0, remaining)

        integer_str = ",".join(parts) + "," + last_three

    if decimals > 0:

        decimal_str = f"{decimal_part:.{decimals}f}"[1:]

    else:

        decimal_str = ""

    formatted = integer_str + decimal_str

    if negative:

        formatted = "-" + formatted

    return formatted

# ---------------------------------------------------
# Populate Filters
# ---------------------------------------------------

location_options = sorted(

    branch_daily_aggregate_df['Location']

    .dropna()

    .unique()

)

rm_options = sorted(

    rm_zm_df['rm']

    .dropna()

    .unique()

)

zm_options = sorted(

    rm_zm_df['zm']

    .dropna()

    .unique()

)

# ---------------------------------------------------
# Default Dates
# ---------------------------------------------------

latest_invoice_date = pd.to_datetime(

    branch_daily_aggregate_df['Date']

).max()

default_start_date = latest_invoice_date.replace(

    day=1

)

# ---------------------------------------------------
# Layout
# ---------------------------------------------------

layout = html.Div(
    className='inv-premium-page-red',
    children=dbc.Container(
        [
            # ---------------------------------------------------
            # Header
            # ---------------------------------------------------
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.A(
                                dbc.Button(
                                    "← Sales Department",
                                    className='inv-btn-dark px-3 py-1',
                                    size='sm'
                                ),
                                href="/sales",
                                style={'textDecoration': 'none'}
                            ),
                            html.H2(
                                "Branch Health Analysis",
                                className="fw-bold mt-3 mb-1"
                            )
                        ],
                        width=8
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                f"Last Updated : {latest_invoice_date.strftime('%d-%b-%Y')}",
                                className='text-end fw-bold mb-2',
                                style={'color': '#f8d7da'}
                            ),
                            html.Div(
                                [
                                    dbc.Button(
                                        "Export Data",
                                        id='branch-health-export-btn',
                                        className="inv-btn-dark px-3 py-1 me-2 shadow-sm",
                                        size="sm"
                                    ),
                                    dbc.Button(
                                        "Enter",
                                        id='branch-health-enter-btn',
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
                id='branch-health-download'
            ),

            # ---------------------------------------------------
            # Filters
            # ---------------------------------------------------
            dbc.Card(
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Date Range", className="fw-bold mb-1 small text-muted"),
                                    dcc.DatePickerRange(
                                        id='branch-health-date-filter',
                                        start_date=default_start_date,
                                        end_date=latest_invoice_date,
                                        display_format='DD-MMM-YYYY',
                                        className="w-100"
                                    )
                                ],
                                width=3,
                                className="mb-2 mb-md-0"
                            ),
                            dbc.Col(
                                [
                                    html.Label("Location", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='branch-health-location-filter',
                                        options=[
                                            {
                                                'label': i,
                                                'value': i
                                            }
                                            for i in location_options
                                        ],
                                        multi=True,
                                        placeholder='Select Location'
                                    )
                                ],
                                width=3,
                                className="mb-2 mb-md-0"
                            ),
                            dbc.Col(
                                [
                                    html.Label("RM", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='branch-health-rm-filter',
                                        options=[
                                            {
                                                'label': i,
                                                'value': i
                                            }
                                            for i in rm_options
                                        ],
                                        multi=True,
                                        placeholder='Select RM'
                                    )
                                ],
                                width=3,
                                className="mb-2 mb-md-0"
                            ),
                            dbc.Col(
                                [
                                    html.Label("ZM", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='branch-health-zm-filter',
                                        options=[
                                            {
                                                'label': i,
                                                'value': i
                                            }
                                            for i in zm_options
                                        ],
                                        multi=True,
                                        placeholder='Select ZM'
                                    )
                                ],
                                width=3,
                                className="mb-2 mb-md-0"
                            )
                        ]
                    )
                ),
                className='inv-premium-card mb-4'
            ),

            # ---------------------------------------------------
            # KPI Section
            # ---------------------------------------------------
            html.Div(
                id='branch-health-kpi-container'
            ),

            # ---------------------------------------------------
            # Tables
            # ---------------------------------------------------
            dcc.Loading(
                html.Div(
                    id='branch-health-table-container'
                ),
                type='default'
            )
        ],
        fluid=True
    )
)

# ---------------------------------------------------
# KPI Card Helper
# ---------------------------------------------------

def create_kpi_card(

    title,
    value,

    background='#ffe082',

    is_percentage=False

):

    if is_percentage:

        formatted_value = f"{value:,.2f}%"

    elif title == 'UPT':

        formatted_value = f"{value:,.2f}"

    else:

        formatted_value = f"{value:,.0f}"

    if background == '#ffe082':
        bg_color = 'rgba(255, 224, 130, 0.12)'
        border_color = 'rgba(255, 224, 130, 0.25)'
        title_color = '#ffe082'
    elif background == '#ffb74d':
        bg_color = 'rgba(255, 183, 77, 0.12)'
        border_color = 'rgba(255, 183, 77, 0.25)'
        title_color = '#ffb74d'
    else:
        bg_color = 'rgba(255, 255, 255, 0.08)'
        border_color = 'rgba(255, 255, 255, 0.15)'
        title_color = '#f8d7da'

    return dbc.Card(

        dbc.CardBody(

            [

                html.Div(

                    title,

                    style={

                        'fontWeight': '600',
                        'fontSize': '10px',

                        'textAlign': 'center',
                        'color': title_color,
                        'textTransform': 'uppercase',
                        'letterSpacing': '0.05em',

                        'whiteSpace': 'nowrap',
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis'

                    }

                ),

                html.Div(

                    formatted_value,

                    style={

                        'fontSize': '14px',

                        'fontWeight': '700',

                        'textAlign': 'center',
                        'color': '#FFFFFF',

                        'marginTop': '2px'

                    }

                )

            ],

            style={

                'padding': '6px 4px'

            }

        ),

        className='branch-kpi-card',

        style={

            'borderRadius': '10px',
            'backgroundColor': bg_color,
            'border': f'1px solid {border_color}',
            'boxShadow': '0 4px 15px rgba(0, 0, 0, 0.15)',

            'height': '58px',

            'display': 'flex',

            'justifyContent': 'center',
            'marginBottom': '4px'

        }

    )

# ---------------------------------------------------
# KPI Section Builder
# ---------------------------------------------------

def build_kpi_section(

    title,
    kpis,

    background='#ffe082'

):

    cards = []

    percentage_kpis = [

        'Customer Conversion %',

        'Gold %',
        'Diamond %',
        'Silver %',
        'Gemstone %',
        'Mohor %'

    ]

    ordered_kpis = [

        'NSV',
        'ATV',
        'ASP',
        'UPT',
        'Customer Conversion %',

        'Gold %',
        'Diamond %',
        'Silver %',
        'Gemstone %',
        'Mohor %'

    ]

    for kpi_name in ordered_kpis:

        if kpi_name not in kpis:

            continue

        value = kpis[kpi_name]

        cards.append(

            html.Div(

                create_kpi_card(

                    title=kpi_name,

                    value=value,

                    background=background,

                    is_percentage=kpi_name in percentage_kpis

                ),

                style={'flex': '1 1 90px', 'minWidth': '90px', 'maxWidth': '140px', 'padding': '4px'}

            )

        )

    return html.Div(

        [

            html.H5(

                title,

                className='fw-bold mb-2 mt-3',

                style= {

                    'color': 'white'
                }

            ),

            html.Div(

                cards,

                style={
                    'display': 'flex',
                    'flexWrap': 'wrap',
                    'justifyContent': 'space-between',
                    'margin': '0 -4px'
                }

            )

        ]

    )

# ---------------------------------------------------
# Collection KPI Section
# ---------------------------------------------------

def build_collection_section(

    title,
    kpis,

    background='#ffb74d'

):

    ordered_kpis = [

        'Total Collection',
        'Cash',
        'Card',
        'Cheque',
        'Digital'

    ]

    cards = []

    for kpi_name in ordered_kpis:

        value = kpis.get(

            kpi_name,
            0

        )

        cards.append(

            html.Div(

                create_kpi_card(

                    title=kpi_name,

                    value=value,

                    background=background

                ),

                style={'flex': '1 1 120px', 'minWidth': '120px', 'maxWidth': '240px', 'padding': '4px'}

            )

        )

    return html.Div(

        [

            html.H5(

                title,

                className='fw-bold mb-2 mt-3',

                style= {

                    'color': 'white'
                }

            ),

            html.Div(

                cards,

                style={
                    'display': 'flex',
                    'flexWrap': 'wrap',
                    'justifyContent': 'space-between',
                    'margin': '0 -4px'
                }

            )

        ]

    )
# ---------------------------------------------------
# Table Builder
# ---------------------------------------------------

def build_table(

    df,
    table_title

):

    # ---------------------------------------------------
    # Indian Formatting
    # ---------------------------------------------------

    formatted_df = df.copy()

    weight_metrics = [

        'Gold Gms',
        'Diamond CTS',
        'Silver Gms'

    ]

    # ---------------------------------------------------
    # Force Numeric Conversion First
    # ---------------------------------------------------

    for col in formatted_df.columns:

        if col == 'Metric':

            continue

        formatted_df[col] = pd.to_numeric(

            formatted_df[col],

            errors='coerce'

        )

    # ---------------------------------------------------
    # Force Object Type
    # ---------------------------------------------------

    formatted_df = formatted_df.astype(object)


    # ---------------------------------------------------
    # Indian Formatting
    # ---------------------------------------------------

    for idx in formatted_df.index:

        metric_name = formatted_df.loc[idx, 'Metric']

        decimals = 3 if metric_name in weight_metrics else 0

        for col in formatted_df.columns:

            if col == 'Metric':

                continue

            value = formatted_df.loc[idx, col]

            if pd.notna(value):

                formatted_df.loc[idx, col] = str(

                    indian_format(

                        value,
                        decimals

                    )

                )

    # ---------------------------------------------------
    # Table UI
    # ---------------------------------------------------

    return dbc.Card(

        [

            dbc.CardHeader(

                html.Div(

                    table_title,

                    className='fw-bold mb-0',

                    style={

                        'fontSize': '1.1rem',

                        'color': '#1C1B19',

                        'fontFamily': "'Outfit', sans-serif"

                    }

                )

            ),

            dbc.CardBody(

                dash_table.DataTable(

                    data=formatted_df.to_dict('records'),

                    columns=[

                        {

                            'name': i,

                            'id': i,

                            'type': 'text'

                        }

                        for i in formatted_df.columns

                    ],

                    fixed_rows={'headers': True},

                    page_action='none',

                    style_table={

                        'overflowX': 'auto',

                        'overflowY': 'auto',

                        'maxHeight': '650px',

                        'width': '100%',

                        'margin': '0 auto',

                        'border': '1px solid #5a0b0b',

                        'borderRadius': '8px'

                    },

                    style_cell={

                        'textAlign': 'center',

                        'padding': '6px 8px',

                        'fontSize': '11px',

                        'fontFamily': "'Outfit', 'Inter', sans-serif",

                        'minWidth': '90px',

                        'width': '90px',

                        'maxWidth': '110px',

                        'whiteSpace': 'normal',

                        'height': 'auto',

                        'backgroundColor': '#FFFFFF',

                        'color': '#1C1B19',

                        'border': '1px solid #E3DFD5'

                    },

                    style_cell_conditional=[

                        {

                            'if': {

                                'column_id': 'Metric'

                            },

                            'textAlign': 'left',

                            'fontWeight': 'bold',

                            'minWidth': '160px',

                            'width': '160px',

                            'maxWidth': '180px'

                        }

                    ],

                    style_header={

                        'fontWeight': 'bold',

                        'backgroundColor': '#FAF9F6',

                        'color': '#1C1B19',

                        'fontSize': '11px',

                        'textAlign': 'center',

                        'border': '1px solid #D9D4C7',

                        'position': 'sticky',

                        'top': 0,

                        'zIndex': 1

                    },

                    style_data={

                        'backgroundColor': '#FFFFFF',

                        'color': '#1C1B19',

                        'border': '1px solid #E3DFD5'

                    },

                    style_data_conditional=[

                        # ---------------------------------------------------
                        # Positive Target
                        # ---------------------------------------------------

                        {

                            'if': {

                                'filter_query': '{Vs Target %} > 0',
                                'column_id': 'Vs Target %'

                            },

                            'backgroundColor': '#d4edda',
                            'color': 'black'

                        },

                        {

                            'if': {

                                'filter_query': '{Vs MTD Target %} > 0',
                                'column_id': 'Vs MTD Target %'

                            },

                            'backgroundColor': '#d4edda',
                            'color': 'black'

                        },

                        {

                            'if': {

                                'filter_query': '{Vs YTD Target %} > 0',
                                'column_id': 'Vs YTD Target %'

                            },

                            'backgroundColor': '#d4edda',
                            'color': 'black'

                        },

                        # ---------------------------------------------------
                        # Negative Target
                        # ---------------------------------------------------

                        {

                            'if': {

                                'filter_query': '{Vs Target %} < 0',
                                'column_id': 'Vs Target %'

                            },

                            'backgroundColor': '#f8d7da',
                            'color': 'black'

                        },

                        {

                            'if': {

                                'filter_query': '{Vs MTD Target %} < 0',
                                'column_id': 'Vs MTD Target %'

                            },

                            'backgroundColor': '#f8d7da',
                            'color': 'black'

                        },

                        {

                            'if': {

                                'filter_query': '{Vs YTD Target %} < 0',
                                'column_id': 'Vs YTD Target %'

                            },

                            'backgroundColor': '#f8d7da',
                            'color': 'black'

                        },

                        # ---------------------------------------------------
                        # Positive LY
                        # ---------------------------------------------------

                        {

                            'if': {

                                'filter_query': '{Vs LY %} > 0',
                                'column_id': 'Vs LY %'

                            },

                            'backgroundColor': '#d4edda',
                            'color': 'black'

                        },

                        {

                            'if': {

                                'filter_query': '{Vs LY TD %} > 0',
                                'column_id': 'Vs LY TD %'

                            },

                            'backgroundColor': '#d4edda',
                            'color': 'black'

                        },

                        # ---------------------------------------------------
                        # Negative LY
                        # ---------------------------------------------------

                        {

                            'if': {

                                'filter_query': '{Vs LY %} < 0',
                                'column_id': 'Vs LY %'

                            },

                            'backgroundColor': '#f8d7da',
                            'color': 'black'

                        },

                        {

                            'if': {

                                'filter_query': '{Vs LY TD %} < 0',
                                'column_id': 'Vs LY TD %'

                            },

                            'backgroundColor': '#f8d7da',
                            'color': 'black'

                        }

                    ]

                ),

                style={

                    'padding': '16px'

                }

            )

        ],

        className='inv-premium-card mb-4'

    )

# ---------------------------------------------------
# Main Callback
# ---------------------------------------------------

@callback(

    Output(

        'branch-health-kpi-container',

        'children'

    ),

    Output(

        'branch-health-table-container',

        'children'

    ),

    Input(

        'branch-health-enter-btn',

        'n_clicks'

    ),

    State(

        'branch-health-date-filter',

        'start_date'

    ),

    State(

        'branch-health-date-filter',

        'end_date'

    ),

    State(

        'branch-health-location-filter',

        'value'

    ),

    State(

        'branch-health-rm-filter',

        'value'

    ),

    State(

        'branch-health-zm-filter',

        'value'

    )

)

def render_branch_health_dashboard(

    n_clicks,

    start_date,
    end_date,

    locations,
    rms,
    zms

):

    if not start_date or not end_date:

        return html.Div(), html.Div()

    try:

        dashboard_data = generate_branch_health_dashboard_data(

            start_date=start_date,
            end_date=end_date,

            locations=locations,
            rms=rms,
            zms=zms

        )

    except Exception as e:

        return html.Div(str(e)), html.Div()

    kpi_sections = dashboard_data['kpi_sections']

    today_table = dashboard_data['today_table']

    mtd_table = dashboard_data['mtd_table']

    ytd_table = dashboard_data['ytd_table']

    # ---------------------------------------------------
    # KPI Layout
    # ---------------------------------------------------

    kpi_layout = html.Div(

        [

            # ---------------------------------------------------
            # TODAY
            # ---------------------------------------------------

            build_kpi_section(

                'TODAY KPI',

                kpi_sections['today_kpis'],

                background='#ffe082'

            ),

            build_collection_section(

                'TODAY COLLECTION',

                kpi_sections['today_kpis'],

                background='#ffb74d'

            ),

            # ---------------------------------------------------
            # MTD
            # ---------------------------------------------------

            build_kpi_section(

                'MTD KPI',

                kpi_sections['mtd_kpis'],

                background='#ffe082'

            ),

            build_collection_section(

                'MTD COLLECTION',

                kpi_sections['mtd_kpis'],

                background='#ffb74d'

            ),

            # ---------------------------------------------------
            # YTD
            # ---------------------------------------------------

            build_kpi_section(

                'YTD KPI',

                kpi_sections['ytd_kpis'],

                background='#ffe082'

            ),

            build_collection_section(

                'YTD COLLECTION',

                kpi_sections['ytd_kpis'],

                background='#ffb74d'

            )

        ]

    )

    # ---------------------------------------------------
    # Tables Layout
    # ---------------------------------------------------

    table_layout = html.Div(

        [

            build_table(

                today_table,

                'TODAY ANALYSIS'

            ),

            build_table(

                mtd_table,

                'MTD ANALYSIS'

            ),

            build_table(

                ytd_table,

                'YTD ANALYSIS'

            )

        ]

    )

    return kpi_layout, table_layout

# ---------------------------------------------------
# Export Callback
# ---------------------------------------------------

@callback(

    Output(

        'branch-health-download',

        'data'

    ),

    Input(

        'branch-health-export-btn',

        'n_clicks'

    ),

    State(

        'branch-health-date-filter',

        'start_date'

    ),

    State(

        'branch-health-date-filter',

        'end_date'

    ),

    State(

        'branch-health-location-filter',

        'value'

    ),

    State(

        'branch-health-rm-filter',

        'value'

    ),

    State(

        'branch-health-zm-filter',

        'value'

    ),

    prevent_initial_call=True

)

def export_branch_health_dashboard(

    n_clicks,

    start_date,
    end_date,

    locations,
    rms,
    zms

):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "Branch Health Dashboard",
        action="Export Data",
        filters={"start_date": start_date, "end_date": end_date, "locations": locations, "rms": rms, "zms": zms}
    )


    dashboard_data = generate_branch_health_dashboard_data(

        start_date=start_date,
        end_date=end_date,

        locations=locations,
        rms=rms,
        zms=zms

    )

    export_df = dashboard_data['export_df']

    return dcc.send_data_frame(

        export_df.to_csv,

        "branch_health_dashboard_export.csv",

        index=False

    )

# ---------------------------------------------------
# Dynamic Location Dropdown Options RLS
# ---------------------------------------------------
from dash import callback, Output, Input

@callback(
    Output('branch-health-location-filter', 'options'),
    Input('branch-health-location-filter', 'id')
)
def populate_branch_health_location_filter_options(_):
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
