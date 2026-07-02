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
from dash.dash_table.Format import Format, Group

from backend.cache.data_cache import (

    branch_daily_aggregate_df,
    rm_zm_df

)

from backend.services.sales.period_comparison import (

    generate_period_comparison_dashboard_data

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

latest_date = pd.to_datetime(

    branch_daily_aggregate_df['Date']

).max()

recent_start_date = latest_date.replace(day=1)

older_start_date = (

    recent_start_date
    - pd.DateOffset(years=1)

)

older_end_date = (

    latest_date
    - pd.DateOffset(years=1)

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
                                "Period Comparison Dashboard",
                                className="fw-bold mt-3 mb-1"
                            )
                        ],
                        width=8
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                f"Last Updated : {latest_date.strftime('%d-%b-%Y')}",
                                className='text-end fw-bold mb-2',
                                style={'color': '#f8d7da'}
                            ),
                            html.Div(
                                [
                                    dbc.Button(
                                        "Export Data",
                                        id='period-comparison-export-btn',
                                        className="inv-btn-dark px-3 py-1 me-2 shadow-sm",
                                        size="sm"
                                    ),
                                    dbc.Button(
                                        "Enter",
                                        id='period-comparison-enter-btn',
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
                id='period-comparison-download'
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
                                    html.Label("Recent Period", className="fw-bold mb-1 small text-muted"),
                                    dcc.DatePickerRange(
                                        id='recent-period-filter',
                                        start_date=recent_start_date,
                                        end_date=latest_date,
                                        display_format='DD-MMM-YYYY',
                                        className="w-100"
                                    )
                                ],
                                width=3,
                                className="mb-2 mb-md-0"
                            ),
                            dbc.Col(
                                [
                                    html.Label("Older Period", className="fw-bold mb-1 small text-muted"),
                                    dcc.DatePickerRange(
                                        id='older-period-filter',
                                        start_date=older_start_date,
                                        end_date=older_end_date,
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
                                        id='period-comparison-location-filter',
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
                                width=2,
                                className="mb-2 mb-md-0"
                            ),
                            dbc.Col(
                                [
                                    html.Label("RM", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='period-comparison-rm-filter',
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
                                width=2,
                                className="mb-2 mb-md-0"
                            ),
                            dbc.Col(
                                [
                                    html.Label("ZM", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='period-comparison-zm-filter',
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
                                width=2,
                                className="mb-2 mb-md-0"
                            )
                        ]
                    )
                ),
                className='inv-premium-card mb-4'
            ),

            # ---------------------------------------------------
            # Table Container
            # ---------------------------------------------------
            dcc.Loading(
                html.Div(
                    id='period-comparison-table-container'
                ),
                type='default'
            )
        ],
        fluid=True
    )
)

# ---------------------------------------------------
# Table Builder
# ---------------------------------------------------

def build_table(

    df,
    table_title

):
    
    display_df = df.copy()

    display_df = display_df.astype(object)

    for col in display_df.columns:

        if col in [

            '_abs_diff_numeric',

            '_norm_diff_numeric'

        ]:

            continue

        if col == 'Metric':

            continue

        for idx in display_df.index:

            value = display_df.loc[idx, col]

            metric = display_df.loc[idx, 'Metric']

            if metric in [

                'Gold_w',
                'Silver_w',
                'Diamond_Cts',
                'UPT'

            ]:

                display_df.loc[idx, col] = indian_format(

                    value,

                    decimals=3

                )

            elif metric == 'Customer conversion%':

                display_df.loc[idx, col] = indian_format(

                    value,

                    decimals=2

                )

            else:

                display_df.loc[idx, col] = indian_format(

                    value,

                    decimals=0

                )

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

                    data=display_df.to_dict('records'),

                    columns=[

                        {

                            'name': col,
                            'id': col

                        }

                        for col in df.columns

                        if col not in [

                            '_abs_diff_numeric',

                            '_norm_diff_numeric'

                        ]

                    ],

                    page_action='none',

                    style_table={

                        'overflowX': 'auto',
                        'overflowY': 'auto',

                        'maxHeight': '650px',

                        'width': '100%',

                        'border': '1px solid #5a0b0b',

                        'borderRadius': '8px'

                    },

                    style_cell={

                        'textAlign': 'center',

                        'padding': '6px 8px',

                        'fontSize': '13px',

                        'fontFamily': "'Outfit', 'Inter', sans-serif",

                        'whiteSpace': 'normal',

                        'height': 'auto',

                        'minWidth': '110px',

                        'width': '110px',

                        'maxWidth': '110px',

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

                            'minWidth': '180px',

                            'width': '180px',

                            'maxWidth': '180px'

                        },

                        {

                            'if': {

                                'column_id': 'Normalized Difference'

                            },

                            'fontWeight': 'bold'

                        }

                    ],

                    style_header={

                        'fontWeight': 'bold',

                        'backgroundColor': '#FAF9F6',

                        'color': '#1C1B19',

                        'fontSize': '13px',

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

                    style_data_conditional=(

                        [

                            {

                                'if': {

                                    'filter_query': '{_abs_diff_numeric} > 0',
                                    'column_id': 'Absolute Difference'

                                },

                                'backgroundColor': '#d4edda',
                                'color': '#1C1B19'

                            },

                            {

                                'if': {

                                    'filter_query': '{_abs_diff_numeric} < 0',
                                    'column_id': 'Absolute Difference'

                                },

                                'backgroundColor': '#f8d7da',
                                'color': '#1C1B19'

                            },

                            {

                                'if': {

                                    'filter_query': '{_norm_diff_numeric} > 0',
                                    'column_id': 'Normalized Difference'

                                },

                                'backgroundColor': '#d4edda',
                                'color': '#1C1B19'

                            },

                            {

                                'if': {

                                    'filter_query': '{_norm_diff_numeric} < 0',
                                    'column_id': 'Normalized Difference'

                                },

                                'backgroundColor': '#f8d7da',
                                'color': '#1C1B19'

                            }

                        ]

                        if 'Absolute Difference' in df.columns

                        else []

                    )

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

        'period-comparison-table-container',

        'children'

    ),

    Input(

        'period-comparison-enter-btn',

        'n_clicks'

    ),

    State(

        'recent-period-filter',

        'start_date'

    ),

    State(

        'recent-period-filter',

        'end_date'

    ),

    State(

        'older-period-filter',

        'start_date'

    ),

    State(

        'older-period-filter',

        'end_date'

    ),

    State(

        'period-comparison-location-filter',

        'value'

    ),

    State(

        'period-comparison-rm-filter',

        'value'

    ),

    State(

        'period-comparison-zm-filter',

        'value'

    )

)

def render_period_comparison_dashboard(

    n_clicks,

    recent_start_date,
    recent_end_date,

    older_start_date,
    older_end_date,

    locations,
    rms,
    zms

):

    try:

        dashboard_data = generate_period_comparison_dashboard_data(

            recent_start_date=recent_start_date,
            recent_end_date=recent_end_date,

            older_start_date=older_start_date,
            older_end_date=older_end_date,

            locations=locations,
            rms=rms,
            zms=zms

        )

    except Exception as e:

        return html.Div(str(e))

    comparison_table = dashboard_data['comparison_table']

    recent_table = dashboard_data['recent_table']

    older_table = dashboard_data['older_table']

    return html.Div(

        [

            # ---------------------------------------------------
            # Comparison Table
            # ---------------------------------------------------

            dbc.Row(

                [

                    dbc.Col(

                        build_table(

                            comparison_table,

                            'COMPARISON ANALYSIS'

                        ),

                        width=6

                    )

                ],

                justify='center'

            ),

            # ---------------------------------------------------
            # Recent & Older Tables
            # ---------------------------------------------------

            dbc.Row(

                [

                    dbc.Col(

                        build_table(

                            recent_table,

                            'RECENT PERIOD'

                        ),

                        width=6

                    ),

                    dbc.Col(

                        build_table(

                            older_table,

                            'OLDER PERIOD'

                        ),

                        width=6

                    )

                ]

            )

        ]

    )

# ---------------------------------------------------
# Export Callback
# ---------------------------------------------------

@callback(

    Output(

        'period-comparison-download',

        'data'

    ),

    Input(

        'period-comparison-export-btn',

        'n_clicks'

    ),

    State(

        'recent-period-filter',

        'start_date'

    ),

    State(

        'recent-period-filter',

        'end_date'

    ),

    State(

        'older-period-filter',

        'start_date'

    ),

    State(

        'older-period-filter',

        'end_date'

    ),

    State(

        'period-comparison-location-filter',

        'value'

    ),

    State(

        'period-comparison-rm-filter',

        'value'

    ),

    State(

        'period-comparison-zm-filter',

        'value'

    ),

    prevent_initial_call=True

)

def export_period_comparison_dashboard(

    n_clicks,

    recent_start_date,
    recent_end_date,

    older_start_date,
    older_end_date,

    locations,
    rms,
    zms

):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "Period Comparison Dashboard",
        action="Export Data",
        filters={"recent_start_date": recent_start_date, "recent_end_date": recent_end_date, "older_start_date": older_start_date, "older_end_date": older_end_date, "locations": locations, "rms": rms, "zms": zms}
    )


    dashboard_data = generate_period_comparison_dashboard_data(

        recent_start_date=recent_start_date,
        recent_end_date=recent_end_date,

        older_start_date=older_start_date,
        older_end_date=older_end_date,

        locations=locations,
        rms=rms,
        zms=zms

    )

    export_df = dashboard_data['export_df']

    return dcc.send_data_frame(

        export_df.to_csv,

        "period_comparison_export.csv",

        index=False

    )

# ---------------------------------------------------
# Dynamic Location Dropdown Options RLS
# ---------------------------------------------------
from dash import callback, Output, Input

@callback(
    Output('period-comparison-location-filter', 'options'),
    Input('period-comparison-location-filter', 'id')
)
def populate_period_comparison_location_filter_options(_):
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
