import sys
import os
import io

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '../..'
        )
    )
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dash import html, dcc, dash_table, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# ---------------------------------------------------
# Performance Queries
# ---------------------------------------------------
from backend.services.sales.performance import (
    # Gauges
    get_nsv_gauge,
    get_gold_gauge,
    get_diamond_gauge,
    get_silver_gauge,
    get_gemstone_gauge,
    get_mohor_gauge,
    # Tables
    get_nsv_performance,
    get_gold_performance,
    get_diamond_performance,
    get_silver_performance,
    get_gemstone_performance,
    get_mohor_performance,
    get_making_charge_performance,
    get_scheme_performance
)

# ---------------------------------------------------
# parquet Connection
# ---------------------------------------------------
from backend.cache.data_cache import (
    merged_sales_df,
    rm_zm_df
)

# ---------------------------------------------------
# Dynamic Dropdown Data
# ---------------------------------------------------
rm_df = pd.DataFrame({
    'rm': sorted(
        rm_zm_df['rm']
        .dropna()
        .unique()
    )
})

last_updated_value = pd.to_datetime(
    merged_sales_df['Invoice Date'].max()
).strftime('%d-%b-%Y')

zm_df = pd.DataFrame({
    'zm': sorted(
        rm_zm_df['zm']
        .dropna()
        .unique()
    )
})

location_df_dropdown = pd.DataFrame({
    'location': sorted(
        rm_zm_df['location']
        .dropna()
        .unique()
    )
})

# ---------------------------------------------------
# Formatting Functions
# ---------------------------------------------------
def format_inr(number):
    if number is None:
        return "₹ 0.00"
    number = float(number)
    x = f"{number:.2f}"
    before_decimal, after_decimal = x.split(".")
    if len(before_decimal) > 3:
        last_three = before_decimal[-3:]
        remaining = before_decimal[:-3]
        parts = []
        while len(remaining) > 2:
            parts.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            parts.insert(0, remaining)
        formatted = ",".join(parts) + "," + last_three
    else:
        formatted = before_decimal
    return f"₹ {formatted}.{after_decimal}"

def format_weight(number):
    if number is None:
        return "0.00"
    return f"{float(number):,.2f}"

def indian_format(number, decimals=0):
    if pd.isna(number) or number == '':
        return ""
    number = float(number)
    if decimals == 0:
        x = str(int(round(number, 0)))
        after_decimal = None
    else:
        x = f"{number:.{decimals}f}"
        before_decimal, after_decimal = x.split(".")
    if decimals == 0:
        before_decimal = x
    if len(before_decimal) > 3:
        last_three = before_decimal[-3:]
        remaining = before_decimal[:-3]
        parts = []
        while len(remaining) > 2:
            parts.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            parts.insert(0, remaining)
        formatted = ",".join(parts) + "," + last_three
    else:
        formatted = before_decimal
    if decimals == 0:
        return formatted
    return f"{formatted}.{after_decimal}"

def monetary_format(number, value_format):
    if pd.isna(number) or number == '':
        return ""
    number = float(number)
    if value_format == 'lakhs':
        return indian_format(
            number / 100000,
            3
        )
    return indian_format(
        number,
        0
    )

# ---------------------------------------------------
# Gauge Function
# ---------------------------------------------------
def create_gauge(title, achieved, target):
    percent = 0
    if target and target != 0:
        percent = (achieved / target) * 100
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=percent,
            number={
                'suffix': '%',
                'font': {
                    'size': 14,
                    'family': 'Outfit, sans-serif'
                }
            },
            title={
                'text': f"<b>{title}</b>",
                'font': {
                    'size': 10,
                    'family': 'Outfit, sans-serif',
                    'color': '#1C1B19'
                }
            },
            gauge={
                'shape': 'angular',
                'axis': {
                    'range': [0, 100],
                    'tickwidth': 1,
                    'tickfont': {
                        'size': 6
                    }
                },
                'bar': {
                    'color': '#C5A059',
                    'thickness': 0.45
                },
                'bgcolor': 'white',
                'steps': [
                    {
                        'range': [0, 60],
                        'color': '#ffcccc'
                    },
                    {
                        'range': [60, 85],
                        'color': '#fff0b3'
                    },
                    {
                        'range': [85, 100],
                        'color': '#d6f5d6'
                    }
                ]
            }
        )
    )
    fig.update_layout(
        height=100,
        margin=dict(
            l=10,
            r=10,
            t=50,
            b=10
        ),
        font=dict(
            size=10,
            family='Outfit, sans-serif'
        ),
        paper_bgcolor='white'
    )
    return fig

# ---------------------------------------------------
# Reusable Table Style
# ---------------------------------------------------
TABLE_STYLE = {
    'page_action': 'none',
    'fill_width': False,
    'fixed_rows': {'headers': True},
    'fixed_columns': {'headers': True, 'data': 1},
    'style_table': {
        'overflowX': 'auto',
        'overflowY': 'auto',
        'height': '380px',
        'width': '100%',
        'minWidth': '100%',
        'border': '1px solid #E3DFD5',
        'borderRadius': '8px'
    },
    'style_cell': {
        'textAlign': 'center',
        'padding': '6px 8px',
        'fontSize': '11px',
        'fontFamily': 'Outfit, Inter, sans-serif',
        'whiteSpace': 'normal',
        'height': '30px',
        'minWidth': '80px',
        'width': '110px',
        'maxWidth': '140px',
        'backgroundColor': '#FFFFFF',
        'color': '#1C1B19',
        'border': '1px solid #E3DFD5'
    },
    'style_header': {
        'fontWeight': 'bold',
        'backgroundColor': '#FAF9F6',
        'color': '#1C1B19',
        'border': '1px solid #D9D4C7',
        'position': 'sticky',
        'top': 0,
        'zIndex': 1
    },
    'style_cell_conditional': [
        {
            'if': {'column_id': 'Location'},
            'width': '140px',
            'minWidth': '120px',
            'maxWidth': '160px',
            'textAlign': 'left'
        },
        {
            'if': {'column_id': 'Code'},
            'width': '70px',
            'minWidth': '60px',
            'maxWidth': '80px'
        }
    ],
    'style_data_conditional': [
        {
            'if': {'column_id': 'Code'},
            'fontWeight': 'bold',
            'backgroundColor': '#FAF9F6'
        },
        {
            'if': {'column_id': 'Location'},
            'fontWeight': 'bold',
            'backgroundColor': '#FAF9F6'
        },
        {
            'if': {'filter_query': '{Location} = "TOTAL"'},
            'fontWeight': 'bold',
            'backgroundColor': '#FAF2DF',
            'color': '#1C1B19'
        }
    ],
}

# ---------------------------------------------------
# Total Row Helper
# ---------------------------------------------------
def add_total_row(df, sum_columns, avg_columns=[], label_column='location', days_passed=None, remaining_days=None):
    if df.empty:
        return df
    total_row = {}
    for col in df.columns:
        if col == label_column:
            total_row[col] = 'TOTAL'
        elif col in sum_columns:
            total_row[col] = df[col].sum()
        elif col in avg_columns:
            total_row[col] = 0
        else:
            total_row[col] = ''

    if days_passed is not None and remaining_days is not None:
        days_passed = max(days_passed, 1)
        remaining_days = max(remaining_days, 1)
        # 1. NSV
        if 'target_nsv' in sum_columns and 'mtd_nsv' in sum_columns:
            total_row['run_rate'] = round(total_row['mtd_nsv'] / days_passed, 0)
            total_row['required_run_rate'] = round((total_row['target_nsv'] - total_row['mtd_nsv']) / remaining_days, 0)
        # 2. Gold
        elif 'target_gold' in sum_columns and 'mtd_gold' in sum_columns:
            total_row['run_rate'] = round(total_row['mtd_gold'] / days_passed, 2)
            total_row['required_run_rate'] = round((total_row['target_gold'] - total_row['mtd_gold']) / remaining_days, 2)
        # 3. Silver
        elif 'target_silver' in sum_columns and 'mtd_silver' in sum_columns:
            total_row['run_rate'] = round(total_row['mtd_silver'] / days_passed, 2)
            total_row['required_run_rate'] = round((total_row['target_silver'] - total_row['mtd_silver']) / remaining_days, 2)
        # 4. Diamond
        elif 'target_diamond' in sum_columns and 'mtd_diamond' in sum_columns:
            total_row['run_rate'] = round(total_row['mtd_diamond'] / days_passed, 2)
            total_row['required_run_rate'] = round((total_row['target_diamond'] - total_row['mtd_diamond']) / remaining_days, 2)
        # 5. Gemstone
        elif 'target_gemstone' in sum_columns and 'mtd_gemstone' in sum_columns:
            total_row['run_rate'] = round(total_row['mtd_gemstone'] / days_passed, 0)
            total_row['required_run_rate'] = round((total_row['target_gemstone'] - total_row['mtd_gemstone']) / remaining_days, 0)
        # 6. Mohor
        elif 'target_mohor_nsv' in sum_columns and 'mtd_mohor_w' in sum_columns:
            total_row['run_rate'] = round(total_row['mtd_mohor_w'] / days_passed, 2)
            total_row['required_run_rate'] = round((total_row['target_mohor_nsv'] - total_row['mtd_mohor_nsv']) / remaining_days, 0)

    df.loc[len(df)] = total_row
    return df

# ---------------------------------------------------
# Default Dates
# ---------------------------------------------------
last_invoice_date = pd.to_datetime(
    merged_sales_df['Invoice Date'].max()
)
default_end_date = last_invoice_date.date()
default_start_date = last_invoice_date.replace(
    day=1
).date()

# ---------------------------------------------------
# Dashboard Layout
# ---------------------------------------------------
layout = html.Div(
    className='inv-premium-page',
    children=dbc.Container(
        [
            # Header Row
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
                                "Performance Dashboard",
                                className='fw-bold mt-3 mb-1'
                            )
                        ],
                        width=8
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                f"Last Updated : {last_updated_value}",
                                className='text-end fw-bold mb-2',
                                style={'color': '#7F7C75'}
                            ),
                            html.Div(
                                [
                                    dbc.Button(
                                        "Export Data",
                                        id="export-performance-btn",
                                        className="inv-btn-dark px-3 py-1 me-2",
                                        size="sm"
                                    ),
                                    dbc.Button(
                                        "Enter",
                                        id="performance-enter-btn",
                                        className="inv-btn-gold px-3 py-1",
                                        size="sm"
                                    )
                                ],
                                className="text-end"
                            ),
                            dcc.Download(
                                id="download-performance-data"
                            )
                        ],
                        width=4
                    )
                ],
                className='mb-4 mt-2 align-items-end'
            ),

            # Filters Panel
            dbc.Card(
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Date Range", className="fw-bold mb-1 small text-muted"),
                                        dcc.DatePickerRange(
                                            id='date-filter',
                                            start_date=default_start_date,
                                            end_date=default_end_date,
                                            display_format='YYYY-MM-DD',
                                            className="w-100"
                                        )
                                    ],
                                    width=3
                                ),
                                dbc.Col(
                                    [
                                        html.Label("RM", className="fw-bold mb-1 small text-muted"),
                                        dcc.Dropdown(
                                            id='rm-filter',
                                            options=[{'label': i, 'value': i} for i in rm_df['rm']],
                                            placeholder='Select RM',
                                            multi=False
                                        )
                                    ],
                                    width=2
                                ),
                                dbc.Col(
                                    [
                                        html.Label("ZM", className="fw-bold mb-1 small text-muted"),
                                        dcc.Dropdown(
                                            id='zm-filter',
                                            options=[{'label': i, 'value': i} for i in zm_df['zm']],
                                            placeholder='Select ZM',
                                            multi=False
                                        )
                                    ],
                                    width=2
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Location", className="fw-bold mb-1 small text-muted"),
                                        dcc.Dropdown(
                                            id='location-filter',
                                            options=[{'label': i, 'value': i} for i in location_df_dropdown['location']],
                                            placeholder='Select Location',
                                            multi=False
                                        )
                                    ],
                                    width=3
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Value Format", className="fw-bold mb-1 small text-muted"),
                                        dbc.RadioItems(
                                            id='value-format-toggle',
                                            options=[
                                                {'label': ' Normal', 'value': 'normal'},
                                                {'label': ' Lakhs', 'value': 'lakhs'}
                                            ],
                                            value='normal',
                                            inline=True,
                                            style={'fontSize': '13px', 'marginTop': '8px'}
                                        )
                                    ],
                                    width=2
                                )
                            ]
                        )
                    ]
                ),
                className='inv-premium-card mb-4'
            ),

            # Gauges Panel
            dbc.Card(
                dbc.CardBody(
                    dcc.Loading(
                        dbc.Row(
                            [
                                # NSV Gauge
                                dbc.Col(
                                    [
                                        dcc.Graph(id='nsv-gauge', style={'height': '120px'}),
                                        html.Div(id='nsv-gauge-text', className='text-center fw-bold small mt-n2 mb-2', style={'color': '#1C1B19'})
                                    ],
                                    width=2
                                ),
                                # Gold Gauge
                                dbc.Col(
                                    [
                                        dcc.Graph(id='gold-gauge', style={'height': '120px'}),
                                        html.Div(id='gold-gauge-text', className='text-center fw-bold small mt-n2 mb-2', style={'color': '#1C1B19'})
                                    ],
                                    width=2
                                ),
                                # Diamond Gauge
                                dbc.Col(
                                    [
                                        dcc.Graph(id='diamond-gauge', style={'height': '120px'}),
                                        html.Div(id='diamond-gauge-text', className='text-center fw-bold small mt-n2 mb-2', style={'color': '#1C1B19'})
                                    ],
                                    width=2
                                ),
                                # Silver Gauge
                                dbc.Col(
                                    [
                                        dcc.Graph(id='silver-gauge', style={'height': '120px'}),
                                        html.Div(id='silver-gauge-text', className='text-center fw-bold small mt-n2 mb-2', style={'color': '#1C1B19'})
                                    ],
                                    width=2
                                ),
                                # Gemstone Gauge
                                dbc.Col(
                                    [
                                        dcc.Graph(id='gemstone-gauge', style={'height': '120px'}),
                                        html.Div(id='gemstone-gauge-text', className='text-center fw-bold small mt-n2 mb-2', style={'color': '#1C1B19'})
                                    ],
                                    width=2
                                ),
                                # Mohor Gauge
                                dbc.Col(
                                    [
                                        dcc.Graph(id='mohor-gauge', style={'height': '120px'}),
                                        html.Div(id='mohor-gauge-text', className='text-center fw-bold small mt-n2 mb-2', style={'color': '#1C1B19'})
                                    ],
                                    width=2
                                )
                            ],
                            className='gx-2'
                        ),
                        type='default',
                        color='#C5A059'
                    ),
                    style={'padding': '15px'}
                ),
                className='inv-premium-card mb-4'
            ),

            # Tables Panel (2-column grid format)
            dcc.Loading(
                [
                    dbc.Row(
                        [
                            # 1. NSV Table
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(html.H5("1. NSV Performance Matrix", className='fw-bold mb-0 text-center py-1'), style={'borderBottom': '1px solid #E3DFD5', 'backgroundColor': '#FAF9F6'}),
                                        dbc.CardBody(dash_table.DataTable(id='nsv-table', **TABLE_STYLE), style={'padding': '10px'})
                                    ],
                                    className='inv-premium-card mb-4'
                                ),
                                xs=12, md=6
                            ),
                            # 2. Gold Table
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(html.H5("2. Gold Performance Matrix", className='fw-bold mb-0 text-center py-1'), style={'borderBottom': '1px solid #E3DFD5', 'backgroundColor': '#FAF9F6'}),
                                        dbc.CardBody(dash_table.DataTable(id='gold-table', **TABLE_STYLE), style={'padding': '10px'})
                                    ],
                                    className='inv-premium-card mb-4'
                                ),
                                xs=12, md=6
                            )
                        ],
                        className='g-3'
                    ),
                    dbc.Row(
                        [
                            # 3. Diamond Table
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(html.H5("3. Diamond Performance Matrix", className='fw-bold mb-0 text-center py-1'), style={'borderBottom': '1px solid #E3DFD5', 'backgroundColor': '#FAF9F6'}),
                                        dbc.CardBody(dash_table.DataTable(id='diamond-table', **TABLE_STYLE), style={'padding': '10px'})
                                    ],
                                    className='inv-premium-card mb-4'
                                ),
                                xs=12, md=6
                            ),
                            # 4. Silver Table
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(html.H5("4. Silver Performance Matrix", className='fw-bold mb-0 text-center py-1'), style={'borderBottom': '1px solid #E3DFD5', 'backgroundColor': '#FAF9F6'}),
                                        dbc.CardBody(dash_table.DataTable(id='silver-table', **TABLE_STYLE), style={'padding': '10px'})
                                    ],
                                    className='inv-premium-card mb-4'
                                ),
                                xs=12, md=6
                            )
                        ],
                        className='g-3'
                    ),
                    dbc.Row(
                        [
                            # 5. Gemstone Table
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(html.H5("5. Gemstone Performance Matrix", className='fw-bold mb-0 text-center py-1'), style={'borderBottom': '1px solid #E3DFD5', 'backgroundColor': '#FAF9F6'}),
                                        dbc.CardBody(dash_table.DataTable(id='gemstone-table', **TABLE_STYLE), style={'padding': '10px'})
                                    ],
                                    className='inv-premium-card mb-4'
                                ),
                                xs=12, md=6
                            ),
                            # 6. Mohor Table
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(html.H5("6. Mohor Performance Matrix", className='fw-bold mb-0 text-center py-1'), style={'borderBottom': '1px solid #E3DFD5', 'backgroundColor': '#FAF9F6'}),
                                        dbc.CardBody(dash_table.DataTable(id='mohor-table', **TABLE_STYLE), style={'padding': '10px'})
                                    ],
                                    className='inv-premium-card mb-4'
                                ),
                                xs=12, md=6
                            )
                        ],
                        className='g-3'
                    ),
                    dbc.Row(
                        [
                            # 7. MC Table
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(html.H5("7. Making Charge Performance Matrix", className='fw-bold mb-0 text-center py-1'), style={'borderBottom': '1px solid #E3DFD5', 'backgroundColor': '#FAF9F6'}),
                                        dbc.CardBody(dash_table.DataTable(id='mc-table', **TABLE_STYLE), style={'padding': '10px'})
                                    ],
                                    className='inv-premium-card mb-4'
                                ),
                                xs=12, md=6
                            ),
                            # 8. Scheme Table
                            dbc.Col(
                                dbc.Card(
                                    [
                                        dbc.CardHeader(html.H5("8. Scheme Performance Matrix", className='fw-bold mb-0 text-center py-1'), style={'borderBottom': '1px solid #E3DFD5', 'backgroundColor': '#FAF9F6'}),
                                        dbc.CardBody(dash_table.DataTable(id='scheme-table', **TABLE_STYLE), style={'padding': '10px'})
                                    ],
                                    className='inv-premium-card mb-4'
                                ),
                                xs=12, md=6
                            )
                        ],
                        className='g-3'
                    )
                ],
                type='default',
                color='#C5A059'
            )
        ],
        fluid=True
    )
)

# ---------------------------------------------------
# Callback
# ---------------------------------------------------
@callback(
    Output('nsv-gauge', 'figure'),
    Output('gold-gauge', 'figure'),
    Output('diamond-gauge', 'figure'),
    Output('silver-gauge', 'figure'),
    Output('gemstone-gauge', 'figure'),
    Output('mohor-gauge', 'figure'),

    Output('nsv-gauge-text', 'children'),
    Output('gold-gauge-text', 'children'),
    Output('diamond-gauge-text', 'children'),
    Output('silver-gauge-text', 'children'),
    Output('gemstone-gauge-text', 'children'),
    Output('mohor-gauge-text', 'children'),

    Output('nsv-table', 'data'),
    Output('nsv-table', 'columns'),

    Output('gold-table', 'data'),
    Output('gold-table', 'columns'),

    Output('diamond-table', 'data'),
    Output('diamond-table', 'columns'),

    Output('silver-table', 'data'),
    Output('silver-table', 'columns'),

    Output('gemstone-table', 'data'),
    Output('gemstone-table', 'columns'),

    Output('mohor-table', 'data'),
    Output('mohor-table', 'columns'),

    Output('mc-table', 'data'),
    Output('mc-table', 'columns'),

    Output('scheme-table', 'data'),
    Output('scheme-table', 'columns'),

    Input('performance-enter-btn', 'n_clicks'),
    Input('url', 'pathname'),

    State('date-filter', 'start_date'),
    State('date-filter', 'end_date'),
    State('rm-filter', 'value'),
    State('zm-filter', 'value'),
    State('location-filter', 'value'),
    State('value-format-toggle', 'value'),
)
def update_dashboard(
    n_clicks,
    pathname,
    start_date,
    end_date,
    rm,
    zm,
    location,
    value_format
):
    # Determine date range defaults
    start_dt = pd.to_datetime(start_date) if start_date else pd.to_datetime(default_start_date)
    end_dt = pd.to_datetime(end_date) if end_date else pd.to_datetime(default_end_date)

    # ---------------------------------------------------
    # Gauges
    # ---------------------------------------------------
    nsv_g = get_nsv_gauge(start_dt, end_dt, rm, zm, location)
    gold_g = get_gold_gauge(start_dt, end_dt, rm, zm, location)
    diamond_g = get_diamond_gauge(start_dt, end_dt, rm, zm, location)
    silver_g = get_silver_gauge(start_dt, end_dt, rm, zm, location)
    gemstone_g = get_gemstone_gauge(start_dt, end_dt, rm, zm, location)
    mohor_g = get_mohor_gauge(start_dt, end_dt, rm, zm, location)

    # ---------------------------------------------------
    # Tables
    # ---------------------------------------------------
    # Calculate days passed and remaining days in month for total row run rates
    days_passed = end_dt.day
    import calendar
    total_days = calendar.monthrange(end_dt.year, end_dt.month)[1]
    remaining_days = max(total_days - end_dt.day, 1)

    nsv_table = get_nsv_performance(start_dt, end_dt, rm, zm, location)
    if nsv_table is None:
        return no_update

    nsv_table = add_total_row(
        nsv_table,
        sum_columns=['target_nsv', 'today_nsv', 'mtd_nsv'],
        avg_columns=['run_rate', 'required_run_rate'],
        days_passed=days_passed,
        remaining_days=remaining_days
    )

    gold_table = get_gold_performance(start_dt, end_dt, rm, zm, location)
    if gold_table is None:
        return no_update

    gold_table = add_total_row(
        gold_table,
        sum_columns=['target_gold', 'today_gold', 'mtd_gold'],
        avg_columns=['run_rate', 'required_run_rate'],
        days_passed=days_passed,
        remaining_days=remaining_days
    )

    diamond_table = get_diamond_performance(start_dt, end_dt, rm, zm, location)
    if diamond_table is None:
        return no_update
    
    diamond_table = add_total_row(
        diamond_table,
        sum_columns=['target_diamond', 'today_diamond', 'mtd_diamond', 'today_diamond_nsv', 'mtd_diamond_nsv'],
        avg_columns=['run_rate', 'required_run_rate'],
        days_passed=days_passed,
        remaining_days=remaining_days
    )

    silver_table = get_silver_performance(start_dt, end_dt, rm, zm, location)
    if silver_table is None:
        return no_update
    
    silver_table = add_total_row(
        silver_table,
        sum_columns=['target_silver', 'today_silver', 'mtd_silver'],
        avg_columns=['run_rate', 'required_run_rate'],
        days_passed=days_passed,
        remaining_days=remaining_days
    )

    gemstone_table = get_gemstone_performance(start_dt, end_dt, rm, zm, location)
    if gemstone_table is None:
        return no_update
    
    gemstone_table = add_total_row(
        gemstone_table,
        sum_columns=['target_gemstone', 'today_gemstone', 'mtd_gemstone'],
        avg_columns=['run_rate', 'required_run_rate'],
        days_passed=days_passed,
        remaining_days=remaining_days
    )

    mohor_table = get_mohor_performance(start_dt, end_dt, rm, zm, location)
    if mohor_table is None:
        return no_update

    mohor_table = add_total_row(
        mohor_table,
        sum_columns=['today_mohor_w', 'mtd_mohor_w', 'target_mohor_nsv', 'today_mohor_nsv', 'mtd_mohor_nsv'],
        avg_columns=['run_rate', 'required_run_rate'],
        days_passed=days_passed,
        remaining_days=remaining_days
    )

    mc_table = get_making_charge_performance(start_dt, end_dt, rm, zm, location)
    if mc_table is None:
        return no_update

    mc_table = add_total_row(
        mc_table,
        sum_columns=['diamond_mc', 'gold_mc', 'silver_mc', 'platinum_mc']
    )

    scheme_table = get_scheme_performance(start_dt, end_dt, rm, zm, location)
    if scheme_table is None:
        return no_update
    
    scheme_table = add_total_row(
        scheme_table,
        sum_columns=['today_scheme_count', 'today_scheme_collection', 'mtd_scheme_count', 'mtd_scheme_collection']
    )
   
    # ----------------------------------------------------
    # % Calculation
    # ----------------------------------------------------
    nsv_table['achievement_pct'] = (
        (
            nsv_table['mtd_nsv']
            /
            nsv_table['target_nsv'].replace(0, pd.NA)
        ) * 100
    ).fillna(0).round(2)

    cols = list(nsv_table.columns)
    cols.insert(5, cols.pop(cols.index('achievement_pct')))
    nsv_table = nsv_table[cols]

    gold_table['achievement_pct'] = (
        (
            gold_table['mtd_gold']
            /
            gold_table['target_gold'].replace(0, pd.NA)
        ) * 100
    ).fillna(0).round(2)

    cols = list(gold_table.columns)
    cols.insert(5, cols.pop(cols.index('achievement_pct')))
    gold_table = gold_table[cols]

    silver_table['achievement_pct'] = (
        (
            silver_table['mtd_silver']
            /
            silver_table['target_silver'].replace(0, pd.NA)
        ) * 100
    ).fillna(0).round(2)

    cols = list(silver_table.columns)
    cols.insert(5, cols.pop(cols.index('achievement_pct')))
    silver_table = silver_table[cols]

    diamond_table['achievement_pct'] = (
        (
            diamond_table['mtd_diamond']
            /
            diamond_table['target_diamond'].replace(0, pd.NA)
        ) * 100
    ).fillna(0).round(2)

    cols = list(diamond_table.columns)
    cols.insert(5, cols.pop(cols.index('achievement_pct')))
    diamond_table = diamond_table[cols]

    gemstone_table['achievement_pct'] = (
        (
            gemstone_table['mtd_gemstone']
            /
            gemstone_table['target_gemstone'].replace(0, pd.NA)
        ) * 100
    ).fillna(0).round(2)

    cols = list(gemstone_table.columns)
    cols.insert(5, cols.pop(cols.index('achievement_pct')))
    gemstone_table = gemstone_table[cols]

    mohor_table['achievement_pct'] = (
        (
            mohor_table['mtd_mohor_nsv']
            /
            mohor_table['target_mohor_nsv'].replace(0, pd.NA)
        ) * 100
    ).fillna(0).round(2)

    cols = list(mohor_table.columns)
    cols.insert(5, cols.pop(cols.index('achievement_pct')))
    mohor_table = mohor_table[cols]

    # ----------------------------------------------------
    # % Formatting
    # ----------------------------------------------------
    nsv_table['achievement_pct'] = nsv_table['achievement_pct'].apply(lambda x: f"{x:.2f}%")
    gold_table['achievement_pct'] = gold_table['achievement_pct'].apply(lambda x: f"{x:.2f}%")
    silver_table['achievement_pct'] = silver_table['achievement_pct'].apply(lambda x: f"{x:.2f}%")
    diamond_table['achievement_pct'] = diamond_table['achievement_pct'].apply(lambda x: f"{x:.2f}%")
    gemstone_table['achievement_pct'] = gemstone_table['achievement_pct'].apply(lambda x: f"{x:.2f}%")
    mohor_table['achievement_pct'] = mohor_table['achievement_pct'].apply(lambda x: f"{x:.2f}%")

    # ---------------------------------------------------
    # Indian Number Formatting
    # ---------------------------------------------------
    nsv_numeric_cols = ['target_nsv', 'today_nsv', 'run_rate', 'mtd_nsv', 'required_run_rate']
    for col in nsv_numeric_cols:
        nsv_table[col] = nsv_table[col].apply(lambda x: monetary_format(x, value_format))

    gold_numeric_cols = ['target_gold', 'today_gold', 'run_rate', 'mtd_gold', 'required_run_rate']
    for col in gold_numeric_cols:
        gold_table[col] = gold_table[col].apply(lambda x: indian_format(x, 2))
    
    silver_numeric_cols = ['target_silver', 'today_silver', 'run_rate', 'mtd_silver', 'required_run_rate']
    for col in silver_numeric_cols:
        silver_table[col] = silver_table[col].apply(lambda x: indian_format(x, 2))

    diamond_numeric_cols = ['target_diamond', 'today_diamond', 'run_rate', 'mtd_diamond', 'required_run_rate', 'today_diamond_nsv', 'mtd_diamond_nsv']
    for col in diamond_numeric_cols:
        if 'nsv' in col:
            diamond_table[col] = diamond_table[col].apply(lambda x: monetary_format(x, value_format))
        else:
            diamond_table[col] = diamond_table[col].apply(lambda x: indian_format(x, 2))

    gemstone_numeric_cols = ['target_gemstone', 'today_gemstone', 'run_rate', 'mtd_gemstone', 'required_run_rate']
    for col in gemstone_numeric_cols:
        gemstone_table[col] = gemstone_table[col].apply(lambda x: monetary_format(x, value_format))

    mohor_2_cols = ['today_mohor_w', 'mtd_mohor_w', 'run_rate']
    mohor_0_cols = ['target_mohor_nsv', 'today_mohor_nsv', 'mtd_mohor_nsv', 'required_run_rate']
    for col in mohor_2_cols:
        mohor_table[col] = mohor_table[col].apply(lambda x: indian_format(x, 2))
    for col in mohor_0_cols:
        mohor_table[col] = mohor_table[col].apply(lambda x: monetary_format(x, value_format))

    mc_numeric_cols = ['diamond_mc', 'gold_mc', 'silver_mc', 'platinum_mc']
    for col in mc_numeric_cols:
        mc_table[col] = mc_table[col].apply(lambda x: monetary_format(x, value_format))

    scheme_0_cols = ['today_scheme_collection', 'mtd_scheme_collection']
    scheme_count_cols = ['today_scheme_count', 'mtd_scheme_count']
    for col in scheme_0_cols:
        scheme_table[col] = scheme_table[col].apply(lambda x: monetary_format(x, value_format))
    for col in scheme_count_cols:
        scheme_table[col] = scheme_table[col].apply(lambda x: indian_format(x, 0))

    # ---------------------------------------------------
    # Rename Columns
    # ---------------------------------------------------
    nsv_table.rename(
        columns={
            'code': 'Code',
            'location': 'Location',
            'target_nsv': 'Target',
            'today_nsv': 'Today',
            'run_rate': 'Run Rate',
            'mtd_nsv': 'MTD',
            'achievement_pct': 'Ach %',
            'required_run_rate': 'Req RR'
        },
        inplace=True
    )

    gold_table.rename(
        columns={
            'code': 'Code',
            'location': 'Location',
            'target_gold': 'Target',
            'today_gold': 'Today',
            'run_rate': 'Run Rate',
            'mtd_gold': 'MTD',
            'achievement_pct': 'Ach %',
            'required_run_rate': 'Req RR'
        },
        inplace=True
    )

    silver_table.rename(
        columns={
            'code': 'Code',
            'location': 'Location',
            'target_silver': 'Target',
            'today_silver': 'Today',
            'run_rate': 'Run Rate',
            'mtd_silver': 'MTD',
            'achievement_pct': 'Ach %',
            'required_run_rate': 'Req RR'
        },
        inplace=True
    )

    diamond_table.rename(
        columns={
            'code': 'Code',
            'location': 'Location',
            'target_diamond': 'Target',
            'today_diamond': 'Today',
            'run_rate': 'Run Rate',
            'mtd_diamond': 'MTD',
            'achievement_pct': 'Ach %',
            'required_run_rate': 'Req RR',
            'today_diamond_nsv': 'Today NSV',
            'mtd_diamond_nsv': 'MTD NSV'
        },
        inplace=True
    )

    gemstone_table.rename(
        columns={
            'code': 'Code',
            'location': 'Location',
            'target_gemstone': 'Target',
            'today_gemstone': 'Today',
            'run_rate': 'Run Rate',
            'mtd_gemstone': 'MTD',
            'achievement_pct': 'Ach %',
            'required_run_rate': 'Req RR'
        },
        inplace=True
    )

    mohor_table.rename(
        columns={
            'code': 'Code',
            'location': 'Location',
            'today_mohor_w': 'Today Wt',
            'mtd_mohor_w': 'MTD Wt',
            'target_mohor_nsv': 'Target',
            'today_mohor_nsv': 'Today NSV',
            'mtd_mohor_nsv': 'MTD NSV',
            'achievement_pct': 'Ach %',
            'run_rate': 'Run Rate',
            'required_run_rate': 'Req RR'
        },
        inplace=True
    )

    mc_table.rename(
        columns={
            'code': 'Code',
            'location': 'Location',
            'diamond_mc': 'Diamond MC',
            'gold_mc': 'Gold MC',
            'silver_mc': 'Silver MC',
            'platinum_mc': 'Platinum MC'
        },
        inplace=True
    )

    scheme_table.rename(
        columns={
            'code': 'Code',
            'location': 'Location',
            'today_scheme_count': 'Today',
            'today_scheme_collection': 'Today_nsv',
            'mtd_scheme_count': 'MTD',
            'mtd_scheme_collection': 'MTD_nsv'
        },
        inplace=True
    )

    # Reorder columns: place Location before Code
    def reorder_location_code_first(df):
        cols = list(df.columns)
        if 'Location' in cols and 'Code' in cols:
            cols.remove('Location')
            cols.remove('Code')
            new_cols = ['Location', 'Code'] + cols
            return df[new_cols]
        return df

    nsv_table = reorder_location_code_first(nsv_table)
    gold_table = reorder_location_code_first(gold_table)
    silver_table = reorder_location_code_first(silver_table)
    diamond_table = reorder_location_code_first(diamond_table)
    gemstone_table = reorder_location_code_first(gemstone_table)
    mohor_table = reorder_location_code_first(mohor_table)
    mc_table = reorder_location_code_first(mc_table)
    scheme_table = reorder_location_code_first(scheme_table)

    return (
        create_gauge(
            'Revenue',
            nsv_g.iloc[0]['achieved_nsv'],
            nsv_g.iloc[0]['target_nsv']
        ),
        create_gauge(
            'Gold Weight',
            gold_g.iloc[0]['achieved_gold'],
            gold_g.iloc[0]['target_gold']
        ),
        create_gauge(
            'Diamond CTS',
            diamond_g.iloc[0]['achieved_diamond'],
            diamond_g.iloc[0]['target_diamond']
        ),
        create_gauge(
            'Silver Weight',
            silver_g.iloc[0]['achieved_silver'],
            silver_g.iloc[0]['target_silver']
        ),
        create_gauge(
            'Gemstone NSV',
            gemstone_g.iloc[0]['achieved_gemstone'],
            gemstone_g.iloc[0]['target_gemstone']
        ),
        create_gauge(
            'Mohor NSV',
            mohor_g.iloc[0]['achieved_mohor'],
            mohor_g.iloc[0]['target_mohor']
        ),

        format_inr(nsv_g.iloc[0]['achieved_nsv']),
        f"{gold_g.iloc[0]['achieved_gold']:,.2f} g",
        f"{diamond_g.iloc[0]['achieved_diamond']:,.2f} cts",
        f"{silver_g.iloc[0]['achieved_silver']:,.2f} g",
        format_inr(gemstone_g.iloc[0]['achieved_gemstone']),
        format_inr(mohor_g.iloc[0]['achieved_mohor']),

        nsv_table.to_dict('records'),
        [{'name': i, 'id': i} for i in nsv_table.columns],

        gold_table.to_dict('records'),
        [{'name': i, 'id': i} for i in gold_table.columns],

        diamond_table.to_dict('records'),
        [{'name': i, 'id': i} for i in diamond_table.columns],

        silver_table.to_dict('records'),
        [{'name': i, 'id': i} for i in silver_table.columns],

        gemstone_table.to_dict('records'),
        [{'name': i, 'id': i} for i in gemstone_table.columns],

        mohor_table.to_dict('records'),
        [{'name': i, 'id': i} for i in mohor_table.columns],

        mc_table.to_dict('records'),
        [{'name': i, 'id': i} for i in mc_table.columns],

        scheme_table.to_dict('records'),
        [{'name': i, 'id': i} for i in scheme_table.columns]
    )

# ---------------------------------------------------
# Export Callback
# ---------------------------------------------------
@callback(
    Output("download-performance-data", "data"),
    Input("export-performance-btn", "n_clicks"),
    State("date-filter", "start_date"),
    State("date-filter", "end_date"),
    State("rm-filter", "value"),
    State("zm-filter", "value"),
    State("location-filter", "value"),
    prevent_initial_call=True
)
def export_performance_data(
    n_clicks,
    start_date,
    end_date,
    rm,
    zm,
    location
):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "Daily Performance Dashboard",
        action="Export Data",
        filters={"start_date": start_date, "end_date": end_date, "rm": rm, "zm": zm, "location": location}
    )

    start_dt = pd.to_datetime(start_date) if start_date else pd.to_datetime(default_start_date)
    end_dt = pd.to_datetime(end_date) if end_date else pd.to_datetime(default_end_date)

    output = io.BytesIO()
    with pd.ExcelWriter(
        output,
        engine='openpyxl'
    ) as writer:
        current_row = 0
        tables = [
            ("NSV", get_nsv_performance(start_dt, end_dt, rm, zm, location)),
            ("Gold", get_gold_performance(start_dt, end_dt, rm, zm, location)),
            ("Diamond", get_diamond_performance(start_dt, end_dt, rm, zm, location)),
            ("Silver", get_silver_performance(start_dt, end_dt, rm, zm, location)),
            ("Gemstone", get_gemstone_performance(start_dt, end_dt, rm, zm, location)),
            ("Mohor", get_mohor_performance(start_dt, end_dt, rm, zm, location)),
            ("MC", get_making_charge_performance(start_dt, end_dt, rm, zm, location)),
            ("Scheme", get_scheme_performance(start_dt, end_dt, rm, zm, location))
        ]

        for table_name, df in tables:
            if df is None:
                continue
            pd.DataFrame({
                table_name: []
            }).to_excel(
                writer,
                sheet_name='Performance Dashboard',
                startrow=current_row,
                index=False
            )

            df.to_excel(
                writer,
                sheet_name='Performance Dashboard',
                startrow=current_row + 1,
                index=False
            )
            current_row += len(df) + 4

    output.seek(0)
    return dcc.send_bytes(
        output.getvalue(),
        "performance_dashboard_export.xlsx"
    )

# ---------------------------------------------------
# Dynamic Location Dropdown Options RLS
# ---------------------------------------------------
from dash import callback, Output, Input

@callback(
    Output('location-filter', 'options'),
    Input('location-filter', 'id')
)
def populate_location_filter_options(_):
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
