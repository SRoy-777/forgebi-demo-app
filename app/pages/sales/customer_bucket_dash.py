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
    rm_zm_df,
    customer_list_df
)
from backend.services.rls import get_allowed_locations

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
# Default Date Settings (MTD)
# ---------------------------------------------------
latest_invoice_dt = pd.to_datetime(merged_sales_df['Invoice Date'].max())
default_end_date = latest_invoice_dt.date()
default_start_date = latest_invoice_dt.replace(day=1).date()
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

bucket_list = [
    "0 - 30k",
    "30k - 50k",
    "50k - 80k",
    "80k - 1L",
    "1L - 1.5L",
    "1.5L - 2L",
    "2L - 3L",
    "3L - 5L",
    "5L & Above"
]

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
        {'if': {'column_id': 'Location Code'}, 'fontWeight': 'bold', 'backgroundColor': '#FAF9F6'},
        {'if': {'column_id': 'Location Name'}, 'fontWeight': 'bold', 'backgroundColor': '#FAF9F6'},
        {'if': {'column_id': 'Customer Code'}, 'fontWeight': 'bold', 'backgroundColor': '#FAF9F6'},
        {'if': {'column_id': 'Customer Name'}, 'fontWeight': 'bold', 'backgroundColor': '#FAF9F6'},
        {'if': {'column_id': 'Customer Phone'}, 'fontWeight': 'bold', 'backgroundColor': '#FAF9F6'},
    ]
}

# ---------------------------------------------------
# Service Logic
# ---------------------------------------------------
def get_customer_bucket_data(
    start_date,
    end_date,
    locations=None,
    rms=None,
    zms=None,
    buckets=None,
    search_query=None
):
    try:
        allowed_locations = get_allowed_locations()
    except Exception:
        allowed_locations = ['ALL']

    df = merged_sales_df.copy()

    # Filter by Date
    if start_date:
        df = df[df['Invoice Date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['Invoice Date'] <= pd.to_datetime(end_date)]

    # Filter by RLS
    if 'ALL' not in allowed_locations:
        df = df[df['Location Name'].isin(allowed_locations)]

    # Filter RM / ZM
    if zms or rms:
        rm_zm = rm_zm_df.copy()
        if 'ALL' not in allowed_locations:
            rm_zm = rm_zm[rm_zm['location'].isin(allowed_locations)]
        if zms:
            zm_locs = rm_zm[rm_zm['zm'].isin(zms)]['location'].unique()
            df = df[df['Location Name'].isin(zm_locs)]
        if rms:
            rm_locs = rm_zm[rm_zm['rm'].isin(rms)]['location'].unique()
            df = df[df['Location Name'].isin(rm_locs)]

    # Filter Location
    if locations:
        df = df[df['Location Name'].isin(locations)]

    # Blocked locations
    exclude_locations = [
        'KATIHAR', 'HEAD OFFICE', 'E COMMERCE', 'SILIGURI OFFICE', 'CORPORATE OFFICE'
    ]
    df = df[~df['Location Name'].astype(str).str.strip().str.upper().isin(exclude_locations)]

    # Clean Customer Code
    df['Customer Code'] = df['Customer Code'].fillna("").astype(str).str.strip().str.upper()
    df = df[df['Customer Code'] != ""]

    if df.empty:
        return pd.DataFrame(columns=[
            'Location Code', 'Location Name', 'Customer Code', 'Customer Name', 'Customer Phone',
            'nsv_generated', 'times_purchased', 'Last Purchase Date', 'last_purchase_value',
            'Last Purchased Item', 'Sales Person Name', 'Bucket'
        ])

    df = df.sort_values(by=['Invoice Date', 'Document No.'])

    latest_tx = df.groupby('Customer Code').last().reset_index()
    sums = df.groupby('Customer Code')['Bom Line Amount'].sum().reset_index().rename(
        columns={'Bom Line Amount': 'nsv_generated'}
    )
    dates = df[['Customer Code', 'Invoice Date']].copy()
    dates['Invoice Date Only'] = dates['Invoice Date'].dt.date
    dates_unique = dates.groupby('Customer Code')['Invoice Date Only'].nunique().reset_index().rename(
        columns={'Invoice Date Only': 'times_purchased'}
    )

    cust_df = latest_tx.merge(sums, on='Customer Code').merge(dates_unique, on='Customer Code')

    # Map Phone
    cust_list = customer_list_df.copy()
    cust_list['customer_no.'] = cust_list['customer_no.'].astype(str).str.strip().str.upper()
    cust_list['phone_no.'] = cust_list['phone_no.'].astype(str).str.strip().str.replace('.0', '', regex=False)
    code_to_phone = cust_list[['customer_no.', 'phone_no.']].drop_duplicates(subset=['customer_no.'])

    cust_df = cust_df.merge(code_to_phone, left_on='Customer Code', right_on='customer_no.', how='left')
    cust_df['Customer Phone'] = cust_df['phone_no.'].fillna("").astype(str).str.strip().replace(['nan', 'None'], '')
    cust_df.drop(columns=['customer_no.', 'phone_no.'], inplace=True, errors='ignore')

    cust_df['Last Purchase Date'] = pd.to_datetime(cust_df['Invoice Date'])
    cust_df['last_purchase_value'] = pd.to_numeric(cust_df['Bom Line Amount'], errors='coerce').fillna(0.0).round(2)
    cust_df['nsv_generated'] = pd.to_numeric(cust_df['nsv_generated'], errors='coerce').fillna(0.0).round(2)
    cust_df['Customer Name'] = cust_df['Customer Name'].fillna("").astype(str).replace(['nan', 'None'], '')
    cust_df['Sales Person Name'] = cust_df['Sales Person Name'].fillna("").astype(str).replace(['nan', 'None'], '')
    cust_df['Item Name'] = cust_df['Item Name'].fillna("").astype(str).replace(['nan', 'None'], '')

    # Assign Bucket
    def get_bucket(val):
        if val <= 30000:
            return "0 - 30k"
        elif val <= 50000:
            return "30k - 50k"
        elif val <= 80000:
            return "50k - 80k"
        elif val <= 100000:
            return "80k - 1L"
        elif val <= 150000:
            return "1L - 1.5L"
        elif val <= 200000:
            return "1.5L - 2L"
        elif val <= 300000:
            return "2L - 3L"
        elif val <= 500000:
            return "3L - 5L"
        else:
            return "5L & Above"

    cust_df['Bucket'] = cust_df['nsv_generated'].apply(get_bucket)

    # Search query
    if search_query:
        q = str(search_query).strip().upper()
        cust_df = cust_df[
            cust_df['Customer Code'].astype(str).str.upper().str.contains(q, na=False) |
            cust_df['Customer Phone'].astype(str).str.upper().str.contains(q, na=False)
        ]

    # Bucket Filter
    if buckets:
        cust_df = cust_df[cust_df['Bucket'].isin(buckets)]

    final_cols = [
        'Location Code', 'Location Name', 'Customer Code', 'Customer Name', 'Customer Phone',
        'nsv_generated', 'times_purchased', 'Last Purchase Date', 'last_purchase_value',
        'Item Name', 'Sales Person Name', 'Bucket'
    ]

    for col in final_cols:
        if col not in cust_df.columns:
            cust_df[col] = ""

    res = cust_df[final_cols].rename(columns={'Item Name': 'Last Purchased Item'}).copy()
    res = res.sort_values(by='nsv_generated', ascending=False)
    return res

# ---------------------------------------------------
# KPI Card UI Maker
# ---------------------------------------------------
def create_kpi_card(title, value, subtitle=None):
    formatted_value = indian_format(value, 0)
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
            formatted_value,
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
                        "← Sales Department",
                        className='inv-btn-dark px-3 py-1',
                        size='sm'
                    ),
                    href="/sales",
                    style={'textDecoration': 'none'}
                ),
                html.H2("Customer Bucket Analysis", className='fw-bold mt-3 mb-1')
            ], width=8),
            dbc.Col([
                html.Div(f"Last Updated : {last_updated_str}", className='text-end fw-bold mb-2', style={'color': '#f8d7da'}),
                html.Div([
                    dbc.Button("Export Data", id='bucket-export-btn', className='inv-btn-dark px-3 py-1 me-2 shadow-sm', size='sm'),
                    dbc.Button("Enter", id='bucket-enter-btn', className='inv-btn-gold px-3 py-1 shadow-sm', size='sm')
                ], className='text-end')
            ], width=4)
        ], className='mb-4 mt-2 align-items-end'),
        
        dcc.Download(id='bucket-download'),
        
        # ---------------------------------------------------
        # Filter Panel
        # ---------------------------------------------------
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Date Range", className="fw-bold mb-1 small text-muted"),
                        html.Br(),
                        dcc.DatePickerRange(
                            id='bucket-date-filter',
                            start_date=default_start_date,
                            end_date=default_end_date,
                            display_format='DD-MMM-YYYY',
                            className="w-100"
                        )
                    ], width=3),
                    dbc.Col([
                        html.Label("Location", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='bucket-location-filter',
                            options=[{'label': l, 'value': l} for l in location_list],
                            multi=True,
                            placeholder='Select Location'
                        )
                    ], width=2),
                    dbc.Col([
                        html.Label("RM", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='bucket-rm-filter',
                            options=[{'label': r, 'value': r} for r in rm_list],
                            multi=True,
                            placeholder='Select RM'
                        )
                    ], width=1),
                    dbc.Col([
                        html.Label("ZM", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='bucket-zm-filter',
                            options=[{'label': z, 'value': z} for z in zm_list],
                            multi=True,
                            placeholder='Select ZM'
                        )
                    ], width=1),
                    dbc.Col([
                        html.Label("Bucket", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='bucket-filter',
                            options=[{'label': b, 'value': b} for b in bucket_list],
                            multi=True,
                            placeholder='Select Bucket'
                        )
                    ], width=2),
                    dbc.Col([
                        html.Label("Search Customer", className="fw-bold mb-1 small text-muted"),
                        dbc.Input(
                            id='bucket-search-filter',
                            placeholder='Search Code/Phone',
                            type='text',
                            style={'height': '38px', 'borderRadius': '8px', 'backgroundColor': '#FFFFFF', 'color': '#1C1B19', 'border': '1px solid #E3DFD5'}
                        )
                    ], width=3)
                ])
            ])
        ], className='inv-premium-card mb-4'),
        
        # ---------------------------------------------------
        # KPI Container
        # ---------------------------------------------------
        dcc.Loading(
            html.Div(id='bucket-kpi-container'),
            type='default'
        ),
        
        # ---------------------------------------------------
        # Table Container
        # ---------------------------------------------------
        dcc.Loading(
            html.Div(id='bucket-table-container'),
            type='default'
        )
    ], fluid=True)
)

# ---------------------------------------------------
# Callback 1: Render Dashboard & Dynamic KPIs
# ---------------------------------------------------
@callback(
    [
        Output('bucket-kpi-container', 'children'),
        Output('bucket-table-container', 'children')
    ],
    [
        Input('bucket-enter-btn', 'n_clicks'),
        Input('url', 'pathname')
    ],
    [
        State('bucket-date-filter', 'start_date'),
        State('bucket-date-filter', 'end_date'),
        State('bucket-location-filter', 'value'),
        State('bucket-rm-filter', 'value'),
        State('bucket-zm-filter', 'value'),
        State('bucket-filter', 'value'),
        State('bucket-search-filter', 'value')
    ]
)
def render_dashboard(n_clicks, pathname, start_date, end_date, locations, rms, zms, buckets, search_query):
    # Prepare data
    df = get_customer_bucket_data(
        start_date=start_date,
        end_date=end_date,
        locations=locations,
        rms=rms,
        zms=zms,
        buckets=buckets,
        search_query=search_query
    )

    if df.empty:
        empty_msg = html.Div(
            "No customers matching filters found.",
            style={'color': 'white', 'textAlign': 'center', 'padding': '50px', 'fontWeight': 'bold'}
        )
        empty_kpi = dbc.Row([
            dbc.Col(
                create_kpi_card("Unique Customers", 0),
                style={'flex': '1', 'minWidth': '150px', 'padding': '4px'}
            )
        ], className="mb-3 g-2")
        return empty_kpi, empty_msg

    # Determine unique customer count
    total_unique_count = df['Customer Code'].nunique()
    
    # Calculate counts per bucket
    bucket_counts = df['Bucket'].value_counts().to_dict()

    visible_buckets = buckets if (buckets and len(buckets) > 0) else bucket_list

    kpi_cols = [
        dbc.Col(
            create_kpi_card("Unique Customers", total_unique_count),
            style={'flex': '1', 'minWidth': '150px', 'padding': '4px'}
        )
    ]
    
    for b in visible_buckets:
        b_count = bucket_counts.get(b, 0)
        b_pct = (b_count / total_unique_count * 100) if total_unique_count > 0 else 0
        kpi_cols.append(
            dbc.Col(
                create_kpi_card(b, b_count, f"{b_pct:.1f}% of Unique"),
                style={'flex': '1', 'minWidth': '150px', 'padding': '4px'}
            )
        )

    kpi_row = dbc.Row(kpi_cols, className="mb-3 g-2", style={'display': 'flex', 'flexWrap': 'wrap'})

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
        {'name': ['Customer', 'Phone No'], 'id': 'Customer Phone'},
        {'name': ['Sales Metrics', 'NSV Generated'], 'id': 'nsv_generated'},
        {'name': ['Sales Metrics', 'Times Purchased'], 'id': 'times_purchased'},
        {'name': ['Last Purchase Info', 'Date'], 'id': 'Last Purchase Date'},
        {'name': ['Last Purchase Info', 'Value'], 'id': 'last_purchase_value'},
        {'name': ['Last Purchase Info', 'Item Name'], 'id': 'Last Purchased Item'},
        {'name': ['Sales Rep', 'Sales Rep'], 'id': 'Sales Person Name'}
    ]

    table_card = dbc.Card([
        dbc.CardHeader(
            html.H5("Customer Bucket Matrix", className='fw-bold mb-0', style={'color': '#1C1B19'})
        ),
        dbc.CardBody([
            dash_table.DataTable(
                id='bucket-table',
                data=disp_df.to_dict('records'),
                columns=columns,
                merge_duplicate_headers=True,
                sort_action='native',
                **TABLE_STYLE
            )
        ])
    ], className='inv-premium-card mb-4')

    return kpi_row, table_card

# ---------------------------------------------------
# Callback 2: Export Data Workbook (Excel)
# ---------------------------------------------------
@callback(
    Output('bucket-download', 'data'),
    Input('bucket-export-btn', 'n_clicks'),
    [
        State('bucket-date-filter', 'start_date'),
        State('bucket-date-filter', 'end_date'),
        State('bucket-location-filter', 'value'),
        State('bucket-rm-filter', 'value'),
        State('bucket-zm-filter', 'value'),
        State('bucket-filter', 'value'),
        State('bucket-search-filter', 'value')
    ],
    prevent_initial_call=True
)
def export_data(n_clicks, start_date, end_date, locations, rms, zms, buckets, search_query):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "Customer Bucket Analysis Dashboard",
        action="Export Data",
        filters={"start_date": start_date, "end_date": end_date, "locations": locations, "rms": rms, "zms": zms, "buckets": buckets, "search_query": search_query}
    )

    df = get_customer_bucket_data(
        start_date=start_date,
        end_date=end_date,
        locations=locations,
        rms=rms,
        zms=zms,
        buckets=buckets,
        search_query=search_query
    )
    
    if df.empty:
        return no_update
        
    clean_master = df.copy()
    clean_master['Last Purchase Date'] = pd.to_datetime(clean_master['Last Purchase Date']).dt.strftime('%Y-%m-%d')
    
    clean_master.rename(columns={
        'Location Code': 'Location Code',
        'Location Name': 'Location Name',
        'Customer Code': 'Customer Code',
        'Customer Name': 'Customer Name',
        'Customer Phone': 'Phone No',
        'nsv_generated': 'NSV Generated',
        'times_purchased': 'Times Purchased',
        'Last Purchase Date': 'Last Purchase Date',
        'last_purchase_value': 'Last Purchase Value',
        'Last Purchased Item': 'Last Purchased Item',
        'Sales Person Name': 'Sales Rep',
        'Bucket': 'Bucket'
    }, inplace=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        clean_master.to_excel(writer, sheet_name='Customer Buckets', index=False)
        
    output.seek(0)
    filename = f"customer_buckets_{start_date or 'MTD'}_to_{end_date or 'latest'}.xlsx"
    return dcc.send_bytes(output.getvalue(), filename)

# ---------------------------------------------------
# Dynamic Location Dropdown Options RLS
# ---------------------------------------------------
@callback(
    Output('bucket-location-filter', 'options'),
    Input('bucket-location-filter', 'id')
)
def populate_bucket_location_filter_options(_):
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
