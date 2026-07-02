import sys
import os
import io
from datetime import datetime, date
import pandas as pd
import numpy as np

import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table, callback, Input, Output, State, no_update

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.cache.data_cache import (
    merged_sales_df,
    rm_zm_df
)
from backend.services.customer_care.dormant_customer import get_dormant_customer_data

# ---------------------------------------------------
# Indian Number Formatting
# ---------------------------------------------------
def indian_format(value, decimals=0):
    try:
        value = float(value)
    except Exception:
        return value

    negative = value < 0
    value = abs(value)
    integer_part = int(value)
    decimal_part = round(value - integer_part, decimals)

    integer_str = str(integer_part)
    if len(integer_str) > 3:
        last_three = integer_str[-3:]
        remaining = integer_str[:-3]
        parts = []
        while len(remaining) > 2:
            parts.insert(0, remaining[-2:])
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
# Default Date & Days Settings
# ---------------------------------------------------
latest_invoice_dt = pd.to_datetime(merged_sales_df['Invoice Date'].max())
default_evaluation_date = latest_invoice_dt.date()
default_days = 365
last_updated_str = latest_invoice_dt.strftime('%d-%b-%Y')

# ---------------------------------------------------
# Dynamic Filter Dropdowns Setup
# ---------------------------------------------------
def get_dropdown_options():
    locs = sorted(merged_sales_df['Location Name'].dropna().unique().tolist())
    rms = sorted(rm_zm_df['rm'].dropna().unique().tolist())
    zms = sorted(rm_zm_df['zm'].dropna().unique().tolist())
    return locs, rms, zms

location_list, rm_list, zm_list = get_dropdown_options()

# ---------------------------------------------------
# DataTable Styling
# ---------------------------------------------------
TABLE_STYLE = {
    'page_size': 100,
    'fill_width': True,
    'fixed_rows': {'headers': True},
    'style_table': {
        'overflowX': 'auto',
        'overflowY': 'auto',
        'maxHeight': '600px',
        'width': '100%',
        'minWidth': '100%',
        'border': '1px solid #5a0b0b',
        'borderRadius': '8px'
    },
    'style_cell': {
        'fontSize': '11px',
        'fontFamily': "'Outfit', 'Inter', sans-serif",
        'padding': '6px 8px',
        'textAlign': 'center',
        'whiteSpace': 'normal',
        'height': '30px',
        'minWidth': '110px',
        'width': '130px',
        'maxWidth': '160px',
        'backgroundColor': '#FFFFFF',
        'color': '#1C1B19',
        'border': '1px solid #E3DFD5'
    },
    'style_header': {
        'backgroundColor': '#FAF9F6',
        'color': '#1C1B19',
        'fontWeight': 'bold',
        'fontSize': '11px',
        'textAlign': 'center',
        'border': '1px solid #D9D4C7',
        'position': 'sticky',
        'top': 0,
        'zIndex': 1,
        'height': '40px',
        'minHeight': '40px',
        'maxHeight': '40px',
        'lineHeight': '14px'
    },
    'style_data': {
        'backgroundColor': '#FFFFFF',
        'color': '#1C1B19'
    },
    'style_data_conditional': [
        # Bold and grey out for key client details
        {'if': {'column_id': 'Location Code'}, 'fontWeight': 'bold', 'backgroundColor': '#FAF9F6'},
        {'if': {'column_id': 'Location Name'}, 'fontWeight': 'bold', 'backgroundColor': '#FAF9F6'},
        {'if': {'column_id': 'Customer Code'}, 'fontWeight': 'bold', 'backgroundColor': '#FAF9F6'},
        {'if': {'column_id': 'Customer Name'}, 'fontWeight': 'bold', 'backgroundColor': '#FAF9F6'},
        {'if': {'column_id': 'Customer Phone'}, 'fontWeight': 'bold', 'backgroundColor': '#FAF9F6'},
    ]
}

# ---------------------------------------------------
# Layout
# ---------------------------------------------------
layout = html.Div(
    className='inv-premium-page-red',
    children=dbc.Container([
        # ---------------------------------------------------
        # Header
        # ---------------------------------------------------
        dbc.Row([
            dbc.Col([
                html.A(
                    dbc.Button(
                        "← Customer Care Department",
                        className='inv-btn-dark px-3 py-1',
                        size='sm'
                    ),
                    href="/customer-care",
                    style={'textDecoration': 'none'}
                ),
                html.H2("Dormant Customer List", className='fw-bold mt-3 mb-1')
            ], width=8),
            dbc.Col([
                html.Div(f"Last Updated : {last_updated_str}", className='text-end fw-bold mb-2', style={'color': '#f8d7da'}),
                html.Div([
                    dbc.Button("Export Data", id='dormant-export-btn', className='inv-btn-dark px-3 py-1 me-2 shadow-sm', size='sm'),
                    dbc.Button("Enter", id='dormant-enter-btn', className='inv-btn-gold px-3 py-1 shadow-sm', size='sm')
                ], className='text-end')
            ], width=4)
        ], className='mb-4 mt-2 align-items-end'),
        
        dcc.Download(id='dormant-download'),
        
        # ---------------------------------------------------
        # Filter Panel
        # ---------------------------------------------------
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Evaluation Date", className="fw-bold mb-1 small text-muted"),
                        html.Br(),
                        dcc.DatePickerSingle(
                            id='dormant-evaluation-date',
                            display_format='DD-MMM-YYYY',
                            date=default_evaluation_date,
                            style={'width': '100%'}
                        )
                    ], width=2),
                    dbc.Col([
                        html.Label("Inactivity Days", className="fw-bold mb-1 small text-muted"),
                        dbc.Input(
                            id='dormant-days',
                            type='number',
                            value=default_days,
                            min=0,
                            placeholder='Days',
                            style={'height': '38px', 'borderRadius': '8px', 'backgroundColor': '#FFFFFF', 'color': '#1C1B19', 'border': '1px solid #E3DFD5'}
                        )
                    ], width=1),
                    dbc.Col([
                        html.Label("NSV more than", className="fw-bold mb-1 small text-muted"),
                        dbc.Input(
                            id='dormant-nsv-more',
                            type='number',
                            placeholder='NSV >=',
                            style={'height': '38px', 'borderRadius': '8px', 'backgroundColor': '#FFFFFF', 'color': '#1C1B19', 'border': '1px solid #E3DFD5'}
                        )
                    ], width=1),
                    dbc.Col([
                        html.Label("P. Count", className="fw-bold mb-1 small text-muted"),
                        dbc.Input(
                            id='dormant-p-count',
                            type='number',
                            placeholder='P. Count >=',
                            style={'height': '38px', 'borderRadius': '8px', 'backgroundColor': '#FFFFFF', 'color': '#1C1B19', 'border': '1px solid #E3DFD5'}
                        )
                    ], width=1),
                    dbc.Col([
                        html.Label("Location", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='dormant-location-filter',
                            options=[{'label': l, 'value': l} for l in location_list],
                            multi=True,
                            placeholder='Select Location'
                        )
                    ], width=2),
                    dbc.Col([
                        html.Label("RM", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='dormant-rm-filter',
                            options=[{'label': r, 'value': r} for r in rm_list],
                            multi=True,
                            placeholder='Select RM'
                        )
                    ], width=1),
                    dbc.Col([
                        html.Label("ZM", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='dormant-zm-filter',
                            options=[{'label': z, 'value': z} for z in zm_list],
                            multi=True,
                            placeholder='Select ZM'
                        )
                    ], width=1),
                    dbc.Col([
                        html.Label("Search Customer", className="fw-bold mb-1 small text-muted"),
                        dbc.Input(
                            id='dormant-search-filter',
                            placeholder='Search Code/Phone',
                            type='text',
                            style={'height': '38px', 'borderRadius': '8px', 'backgroundColor': '#FFFFFF', 'color': '#1C1B19', 'border': '1px solid #E3DFD5'}
                        )
                    ], width=3)
                ])
            ])
        ], className='inv-premium-card mb-4'),
        
        # ---------------------------------------------------
        # KPI Card
        # ---------------------------------------------------
        dcc.Loading(
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("Unique Customers", style={
                                'fontWeight': '600',
                                'fontSize': '11px',
                                'textAlign': 'center',
                                'color': '#f8d7da',
                                'textTransform': 'uppercase',
                                'letterSpacing': '0.05em',
                                'marginBottom': '4px'
                            }),
                            html.Div(id='dormant-kpi-unique-customers', style={
                                'fontSize': '20px',
                                'fontWeight': '700',
                                'textAlign': 'center',
                                'color': '#FFFFFF',
                                'lineHeight': '24px'
                            })
                        ], style={'padding': '12px 16px'})
                    ], style={
                        'borderRadius': '12px',
                        'backgroundColor': 'rgba(255, 255, 255, 0.08)',
                        'border': '1px solid rgba(255, 255, 255, 0.15)',
                        'boxShadow': '0 4px 20px rgba(0, 0, 0, 0.15)',
                        'height': '100%',
                        'marginBottom': '4px',
                        'maxWidth': '200px',
                        'margin': '0 auto'
                    })
                ], width=12, className='mb-3')
            ]),
            type='default'
        ),
        
        # ---------------------------------------------------
        # Data Table Container
        # ---------------------------------------------------
        dcc.Loading(
            html.Div(id='dormant-table-container'),
            type='default'
        )
    ], fluid=True)
)

# ---------------------------------------------------
# Callback 1: Render Dashboard (Enter Button or Route Change)
# ---------------------------------------------------
@callback(
    [
        Output('dormant-kpi-unique-customers', 'children'),
        Output('dormant-table-container', 'children')
    ],
    [
        Input('dormant-enter-btn', 'n_clicks'),
        Input('url', 'pathname')
    ],
    [
        State('dormant-evaluation-date', 'date'),
        State('dormant-days', 'value'),
        State('dormant-location-filter', 'value'),
        State('dormant-rm-filter', 'value'),
        State('dormant-zm-filter', 'value'),
        State('dormant-search-filter', 'value'),
        State('dormant-nsv-more', 'value'),
        State('dormant-p-count', 'value')
    ]
)
def render_dashboard(n_clicks, pathname, eval_date, days_filter, locations, rms, zms, search_query, nsv_more, p_count):
    # Retrieve calculations data
    df = get_dormant_customer_data(
        evaluation_date=eval_date,
        days_filter=days_filter,
        locations=locations,
        rms=rms,
        zms=zms,
        search_query=search_query,
        nsv_more=nsv_more,
        p_count=p_count
    )
    
    # Handle empty dataset
    if df.empty:
        empty_msg = html.Div(
            "No customers matching filters found.",
            style={'color': 'white', 'textAlign': 'center', 'padding': '50px', 'fontWeight': 'bold'}
        )
        return "0", empty_msg

    # Determine unique customer count
    unique_customers_count = df['Customer Code'].nunique()
    
    # Format DataTable data for display
    disp_df = df.copy()
    disp_df = disp_df.sort_values(by='nsv_generated', ascending=False)
    
    disp_df['nsv_generated'] = disp_df['nsv_generated'].apply(lambda x: indian_format(x, 0))
    disp_df['last_purchase_value'] = disp_df['last_purchase_value'].apply(lambda x: indian_format(x, 0))
    disp_df['times_purchased'] = disp_df['times_purchased'].apply(lambda x: indian_format(x, 0))
    disp_df['Last Purchase Date'] = pd.to_datetime(disp_df['Last Purchase Date']).dt.strftime('%d-%b-%Y')
    
    columns = [
        {'name': ['Location', 'Code'], 'id': 'Location Code'},
        {'name': ['Location', 'Name'], 'id': 'Location Name'},
        {'name': ['Customer', 'Code'], 'id': 'Customer Code'},
        {'name': ['Customer', 'Name'], 'id': 'Customer Name'},
        {'name': ['Customer', 'Phone'], 'id': 'Customer Phone'},
        {'name': ['Sales Metrics', 'NSV Generated'], 'id': 'nsv_generated'},
        {'name': ['Sales Metrics', 'Times Purchased'], 'id': 'times_purchased'},
        {'name': ['Last Purchase Info', 'Date'], 'id': 'Last Purchase Date'},
        {'name': ['Last Purchase Info', 'Value'], 'id': 'last_purchase_value'},
        {'name': ['Last Purchase Info', 'Item Name'], 'id': 'Last Purchased Item'},
        {'name': ['Sales Rep', 'Sales Person Name'], 'id': 'Sales Person Name'}
    ]

    table_card = dbc.Card([
        dbc.CardHeader(
            html.H5("Dormant Customer Matrix", className='fw-bold mb-0', style={'color': '#1C1B19'})
        ),
        dbc.CardBody([
            dash_table.DataTable(
                id='dormant-table',
                data=disp_df.to_dict('records'),
                columns=columns,
                merge_duplicate_headers=True,
                sort_action='native',
                **TABLE_STYLE
            )
        ])
    ], className='inv-premium-card mb-4')

    return indian_format(unique_customers_count, 0), table_card

# ---------------------------------------------------
# Callback 2: Export Data Workbook (Excel)
# ---------------------------------------------------
@callback(
    Output('dormant-download', 'data'),
    Input('dormant-export-btn', 'n_clicks'),
    [
        State('dormant-evaluation-date', 'date'),
        State('dormant-days', 'value'),
        State('dormant-location-filter', 'value'),
        State('dormant-rm-filter', 'value'),
        State('dormant-zm-filter', 'value'),
        State('dormant-search-filter', 'value'),
        State('dormant-nsv-more', 'value'),
        State('dormant-p-count', 'value')
    ],
    prevent_initial_call=True
)
def export_data(n_clicks, eval_date, days_filter, locations, rms, zms, search_query, nsv_more, p_count):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "Dormant Customer List",
        action="Export Data",
        filters={"eval_date": eval_date, "days_filter": days_filter, "locations": locations, "rms": rms, "zms": zms, "search_query": search_query, "nsv_more": nsv_more, "p_count": p_count}
    )

    df = get_dormant_customer_data(
        evaluation_date=eval_date,
        days_filter=days_filter,
        locations=locations,
        rms=rms,
        zms=zms,
        search_query=search_query,
        nsv_more=nsv_more,
        p_count=p_count
    )
    
    if df.empty:
        return no_update
        
    # Formatting dates for Excel
    clean_master = df.copy()
    clean_master['Last Purchase Date'] = pd.to_datetime(clean_master['Last Purchase Date']).dt.strftime('%Y-%m-%d')
    
    # Clean export headers
    clean_master.rename(columns={
        'Location Code': 'Location Code',
        'Location Name': 'Location Name',
        'Customer Code': 'Customer Code',
        'Customer Name': 'Customer Name',
        'Customer Phone': 'Customer Phone',
        'nsv_generated': 'NSV Generated',
        'times_purchased': 'Times Purchased',
        'Last Purchase Date': 'Last Purchase Date',
        'last_purchase_value': 'Last Purchase Value',
        'Last Purchased Item': 'Last Purchased Item',
        'Sales Person Name': 'Sales Person Name',
        'days_inactive': 'Days Inactive'
    }, inplace=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        clean_master.to_excel(writer, sheet_name='Dormant Customers', index=False)
        
    output.seek(0)
    filename = f"dormant_customers_{eval_date or 'latest'}_{days_filter or '0'}_days.xlsx"
    return dcc.send_bytes(output.getvalue(), filename)


# ---------------------------------------------------
# Dynamic Location Dropdown Options RLS
# ---------------------------------------------------
from dash import callback, Output, Input

@callback(
    Output('dormant-location-filter', 'options'),
    Input('dormant-location-filter', 'id')
)
def populate_dormant_location_filter_options(_):
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
