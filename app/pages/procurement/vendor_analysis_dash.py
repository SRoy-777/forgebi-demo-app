from dash import (
    html,
    dcc,
    dash_table,
    callback,
    Input,
    Output,
    State,
    no_update
)
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from flask import session
import os
import io

# ---------------------------------------------------
# Load & Clean Vendor Data
# ---------------------------------------------------
def load_vendor_sales_data():
    vendor_sales_path = "data/processed/vendor_sales.xlsx"
    vendor_sales_parquet_path = "snapshot/vendor_sales.parquet"
    if os.path.exists(vendor_sales_path):
        try:
            df = pd.read_excel(vendor_sales_path)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            return df
        except Exception as e:
            print(f"Error loading vendor_sales.xlsx: {e}")
    elif os.path.exists(vendor_sales_parquet_path):
        try:
            df = pd.read_parquet(vendor_sales_parquet_path)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            return df
        except Exception as e:
            print(f"Error loading vendor_sales.parquet: {e}")
            
    # Return a fallback empty DataFrame
    return pd.DataFrame(columns=[
        'Date', 'Counter', 'Category', 'Subcategory', 'Vendor_code', 'Vendor_name',
        'Tags_sold', 'NSV', 'Gold_w', 'Diamond_cts', 'Silver_w',
        'Gemstone_nsv', 'Mohor_w', 'Mohor_nsv'
    ])

df_init = load_vendor_sales_data()

vendor_options = sorted(df_init['Vendor_name'].dropna().unique().tolist()) if not df_init.empty else []
counter_options = sorted(df_init['Counter'].dropna().unique().tolist()) if not df_init.empty else []
category_options = sorted(df_init['Category'].dropna().unique().tolist()) if not df_init.empty else []
subcategory_options = sorted(df_init['Subcategory'].dropna().unique().tolist()) if not df_init.empty else []

# ---------------------------------------------------
# Default Dates (Current MTD based on latest Date in file)
# ---------------------------------------------------
if not df_init.empty and df_init['Date'].notna().any():
    latest_invoice_date = df_init['Date'].max()
else:
    latest_invoice_date = pd.Timestamp.now()

default_end_date = latest_invoice_date.date()
default_start_date = latest_invoice_date.replace(day=1).date()

# ---------------------------------------------------
# Formatting Helpers
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

def format_currency_cell(val):
    if pd.isna(val) or val == "":
        return "0"
    return indian_format(val, 0)

def format_weight_cell(val):
    if pd.isna(val) or val == "":
        return "0.00"
    return f"{float(val):,.2f}"

# ---------------------------------------------------
# UI Styles
# ---------------------------------------------------
TABLE_STYLE_1 = {
    'page_action': 'native',
    'page_size': 15,
    'style_table': {
        'overflowX': 'auto',
        'overflowY': 'auto',
        'height': '380px',
        'width': '100%',
        'minWidth': '100%'
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
    'style_data_conditional': [
        {
            'if': {
                'filter_query': '{Vendor_name} contains "TOTAL"'
            },
            'fontWeight': 'bold',
            'backgroundColor': '#FAF2DF',
            'color': '#1C1B19'
        },
        {
            'if': {
                'column_id': 'Vendor_name'
            },
            'fontWeight': 'bold'
        },
        {
            'if': {
                'column_id': 'NSV'
            },
            'fontWeight': 'bold'
        }
    ]
}

TABLE_STYLE_2 = {
    'page_action': 'native',
    'page_size': 25,
    'style_table': {
        'overflowX': 'auto',
        'overflowY': 'auto',
        'height': '480px',
        'width': '100%',
        'minWidth': '100%'
    },
    'style_cell': {
        'textAlign': 'center',
        'padding': '6px 8px',
        'fontSize': '11px',
        'fontFamily': 'Outfit, Inter, sans-serif',
        'whiteSpace': 'normal',
        'height': '30px',
        'minWidth': '80px',
        'width': '95px',
        'maxWidth': '130px',
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
    'style_data_conditional': [
        {
            'if': {
                'filter_query': '{Counter} contains "TOTAL"'
            },
            'fontWeight': 'bold',
            'backgroundColor': '#FAF2DF',
            'color': '#1C1B19'
        },
        {
            'if': {
                'column_id': 'Counter'
            },
            'fontWeight': 'bold'
        },
        {
            'if': {
                'column_id': 'Vendor_name'
            },
            'fontWeight': 'bold'
        },
        {
            'if': {
                'column_id': 'NSV'
            },
            'fontWeight': 'bold'
        }
    ]
}

# ---------------------------------------------------
# Layout Elements Builder
# ---------------------------------------------------
def build_kpi_card(title, value, is_currency=False, unit=""):
    if is_currency:
        formatted_val = f"₹ {indian_format(value, 0)}"
    else:
        formatted_val = indian_format(value, 2 if unit else 0)
        if unit:
            formatted_val = f"{formatted_val} {unit}"
            
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    title, 
                    className="text-muted small fw-bold text-center text-uppercase",
                    style={'fontSize': '10px', 'letterSpacing': '0.5px'}
                ),
                html.Div(
                    formatted_val,
                    className="fw-bold text-center mt-1",
                    style={'fontSize': '16px', 'color': '#1C1B19', 'fontFamily': 'Outfit, sans-serif'}
                )
            ],
            style={'padding': '12px 8px'}
        ),
        className="inv-premium-card",
        style={
            'border': '1px solid #E3DFD5',
            'borderRadius': '10px',
            'boxShadow': '0 4px 15px rgba(28, 27, 25, 0.02)',
            'height': '68px',
            'backgroundColor': '#FFFFFF',
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center',
            'flex': '1 1 140px',
            'minWidth': '130px'
        }
    )

def add_total_row_table1(df):
    if df.empty:
        return df
    total_row = {
        'Vendor_name': 'TOTAL',
        'Tags_sold': df['Tags_sold'].sum(),
        'NSV': df['NSV'].sum(),
        'Gold_w': df['Gold_w'].sum(),
        'Diamond_cts': df['Diamond_cts'].sum(),
        'Silver_w': df['Silver_w'].sum(),
        'Mohor_w': df['Mohor_w'].sum(),
        'Mohor_nsv': df['Mohor_nsv'].sum(),
        'Gemstone_nsv': df['Gemstone_nsv'].sum()
    }
    return pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

def add_total_row_table2(df):
    if df.empty:
        return df
    total_row = {
        'Counter': 'TOTAL',
        'Category': '',
        'Subcategory': '',
        'Vendor_code': '',
        'Vendor_name': '',
        'Tags_sold': df['Tags_sold'].sum(),
        'NSV': df['NSV'].sum(),
        'Gold_w': df['Gold_w'].sum(),
        'Diamond_cts': df['Diamond_cts'].sum(),
        'Silver_w': df['Silver_w'].sum(),
        'Gemstone_nsv': df['Gemstone_nsv'].sum(),
        'Mohor_w': df['Mohor_w'].sum(),
        'Mohor_nsv': df['Mohor_nsv'].sum()
    }
    return pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

# ---------------------------------------------------
# Dashboard Layout
# ---------------------------------------------------
layout = html.Div(
    className='inv-premium-page',
    children=dbc.Container(
        [
            # ---------------------------------------------------
            # Header Block
            # ---------------------------------------------------
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.A(
                                dbc.Button(
                                    "← Procurement Department",
                                    className='inv-btn-dark px-3 py-1',
                                    size='sm'
                                ),
                                href="/procurement",
                                style={'textDecoration': 'none'}
                            ),
                            html.H2(
                                "Vendor Analysis Dashboard",
                                className='fw-bold mt-3 mb-1'
                            )
                        ],
                        width=6
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                f"Last Updated : {latest_invoice_date.strftime('%d-%b-%Y')}",
                                className='text-end fw-bold mb-2',
                                style={'color': '#7F7C75'}
                            ),
                            html.Div(
                                dbc.Button(
                                    "Export Data",
                                    id='vendor-analysis-export-btn',
                                    className='inv-btn-dark px-3 py-1',
                                    size='sm'
                                ),
                                className='text-end'
                            ),
                            dcc.Download(
                                id='vendor-analysis-download'
                            )
                        ],
                        width=6
                    )
                ],
                className='mb-4 mt-2 align-items-end'
            ),

            # ---------------------------------------------------
            # Filters Panel (Inventory Optimization Style)
            # ---------------------------------------------------
            dbc.Card(
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Date Range", className="fw-bold mb-1 small text-muted"),
                                        dcc.DatePickerRange(
                                            id='vendor-analysis-date-filter',
                                            start_date=default_start_date,
                                            end_date=default_end_date,
                                            display_format='DD-MMM-YYYY',
                                            className="w-100"
                                        )
                                    ],
                                    width=3
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Vendor Name", className="fw-bold mb-1 small text-muted"),
                                        dcc.Dropdown(
                                            id='vendor-analysis-vendor-filter',
                                            options=[{'label': i, 'value': i} for i in vendor_options],
                                            multi=True,
                                            placeholder='Select Vendor'
                                        )
                                    ],
                                    width=2
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Counter", className="fw-bold mb-1 small text-muted"),
                                        dcc.Dropdown(
                                            id='vendor-analysis-counter-filter',
                                            options=[{'label': i, 'value': i} for i in counter_options],
                                            multi=True,
                                            placeholder='Select Counter'
                                        )
                                    ],
                                    width=2
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Category", className="fw-bold mb-1 small text-muted"),
                                        dcc.Dropdown(
                                            id='vendor-analysis-category-filter',
                                            options=[{'label': i, 'value': i} for i in category_options],
                                            multi=True,
                                            placeholder='Select Category'
                                        )
                                    ],
                                    width=2
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Sub-category", className="fw-bold mb-1 small text-muted"),
                                        dcc.Dropdown(
                                            id='vendor-analysis-subcategory-filter',
                                            options=[{'label': i, 'value': i} for i in subcategory_options],
                                            multi=True,
                                            placeholder='Select Subcategory'
                                        )
                                    ],
                                    width=2
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Action", className="fw-bold mb-1 small text-transparent", style={'color': 'transparent'}),
                                        dbc.Button(
                                            "Enter",
                                            id='vendor-analysis-enter-btn',
                                            className='inv-btn-gold w-100',
                                            style={'height': '38px'}
                                        )
                                    ],
                                    width=1
                                )
                            ]
                        )
                    ]
                ),
                className='inv-premium-card mb-4'
            ),

            # ---------------------------------------------------
            # KPI Containers
            # ---------------------------------------------------
            dcc.Loading(
                html.Div(id='vendor-analysis-kpi-container'),
                type='default',
                color='#C5A059'
            ),

            # ---------------------------------------------------
            # Master Tables Container
            # ---------------------------------------------------
            dcc.Loading(
                [
                    html.Div(id='vendor-analysis-best-table-container'),
                    html.Div(id='vendor-analysis-subcategory-table-container')
                ],
                type='default',
                color='#C5A059'
            )
        ],
        fluid=True
    )
)

# ---------------------------------------------------
# Callback 1: Render Dashboard Layout & Calculation
# ---------------------------------------------------
@callback(
    [
        Output('vendor-analysis-kpi-container', 'children'),
        Output('vendor-analysis-best-table-container', 'children'),
        Output('vendor-analysis-subcategory-table-container', 'children')
    ],
    [
        Input('vendor-analysis-enter-btn', 'n_clicks'),
        Input('url', 'pathname')
    ],
    [
        State('vendor-analysis-date-filter', 'start_date'),
        State('vendor-analysis-date-filter', 'end_date'),
        State('vendor-analysis-vendor-filter', 'value'),
        State('vendor-analysis-counter-filter', 'value'),
        State('vendor-analysis-category-filter', 'value'),
        State('vendor-analysis-subcategory-filter', 'value')
    ]
)
def render_vendor_analysis_dashboard(n_clicks, pathname, start_date, end_date, vendors, counters, categories, subcategories):
    # Determine date range defaults
    start_dt = pd.to_datetime(start_date) if start_date else pd.to_datetime(default_start_date)
    end_dt = pd.to_datetime(end_date) if end_date else pd.to_datetime(default_end_date)

    # Load file
    df = load_vendor_sales_data()
    if df.empty:
        empty_msg = html.Div(
            "No sales data available. Make sure to run the raw-to-processed ETL pipeline.",
            className="text-center py-5 text-muted fw-bold"
        )
        return empty_msg, html.Div(), html.Div()

    # Apply Filters
    mask = (df['Date'] >= start_dt) & (df['Date'] <= end_dt)
    df_filtered = df[mask].copy()

    if vendors:
        df_filtered = df_filtered[df_filtered['Vendor_name'].isin(vendors)]
    if counters:
        df_filtered = df_filtered[df_filtered['Counter'].isin(counters)]
    if categories:
        df_filtered = df_filtered[df_filtered['Category'].isin(categories)]
    if subcategories:
        df_filtered = df_filtered[df_filtered['Subcategory'].isin(subcategories)]

    if df_filtered.empty:
        empty_msg = html.Div(
            "No vendor transactions found matching the selected filters.",
            className="text-center py-5 text-muted fw-bold"
        )
        return empty_msg, html.Div(), html.Div()

    # --- KPI Values ---
    nsv_sum = df_filtered['NSV'].sum()
    gold_sum = df_filtered['Gold_w'].sum()
    diamond_sum = df_filtered['Diamond_cts'].sum()
    silver_sum = df_filtered['Silver_w'].sum()
    mohor_w_sum = df_filtered['Mohor_w'].sum()
    mohor_nsv_sum = df_filtered['Mohor_nsv'].sum()
    gemstone_nsv_sum = df_filtered['Gemstone_nsv'].sum()

    kpi_layout = html.Div(
        className="d-flex flex-wrap gap-3 justify-content-between mb-4 w-100",
        children=[
            build_kpi_card("NSV", nsv_sum, is_currency=True),
            build_kpi_card("Gold Weight", gold_sum, unit="g"),
            build_kpi_card("Diamond Carat", diamond_sum, unit="ct"),
            build_kpi_card("Silver Weight", silver_sum, unit="g"),
            build_kpi_card("Mohor Weight", mohor_w_sum, unit="g"),
            build_kpi_card("Mohor NSV", mohor_nsv_sum, is_currency=True),
            build_kpi_card("Gemstone NSV", gemstone_nsv_sum, is_currency=True)
        ]
    )

    # --- Table 1: Best Vendors ---
    t1_df = df_filtered.groupby(['Vendor_name'], as_index=False).agg({
        'Tags_sold': 'sum',
        'NSV': 'sum',
        'Gold_w': 'sum',
        'Diamond_cts': 'sum',
        'Silver_w': 'sum',
        'Mohor_w': 'sum',
        'Mohor_nsv': 'sum',
        'Gemstone_nsv': 'sum'
    }).sort_values(by='NSV', ascending=False)

    t1_df = add_total_row_table1(t1_df)

    t1_disp = t1_df.copy()
    for col in ['NSV', 'Mohor_nsv', 'Gemstone_nsv']:
        t1_disp[col] = t1_disp[col].apply(format_currency_cell)
    for col in ['Gold_w', 'Diamond_cts', 'Silver_w', 'Mohor_w']:
        t1_disp[col] = t1_disp[col].apply(format_weight_cell)
    t1_disp['Tags_sold'] = t1_disp['Tags_sold'].apply(lambda x: f"{int(x):,}")

    t1_cols = [
        {'name': 'Vendor Name', 'id': 'Vendor_name'},
        {'name': 'Tags Sold', 'id': 'Tags_sold'},
        {'name': 'NSV', 'id': 'NSV'},
        {'name': 'Gold Weight (g)', 'id': 'Gold_w'},
        {'name': 'Diamond Carats (ct)', 'id': 'Diamond_cts'},
        {'name': 'Silver Weight (g)', 'id': 'Silver_w'},
        {'name': 'Mohor Weight (g)', 'id': 'Mohor_w'},
        {'name': 'Mohor NSV', 'id': 'Mohor_nsv'},
        {'name': 'Gemstone NSV', 'id': 'Gemstone_nsv'}
    ]

    t1_card = dbc.Card(
        [
            dbc.CardHeader(
                html.H5("Best Vendors Matrix", className='fw-bold mb-0 text-center py-1'),
                style={'borderBottom': '1px solid #E3DFD5', 'backgroundColor': '#FAF9F6'}
            ),
            dbc.CardBody(
                dash_table.DataTable(
                    id='vendor-analysis-best-table',
                    data=t1_disp.to_dict('records'),
                    columns=t1_cols,
                    sort_action='custom',
                    sort_by=[{'column_id': 'NSV', 'direction': 'desc'}],
                    **TABLE_STYLE_1
                ),
                style={'padding': '10px'}
            )
        ],
        className='inv-premium-card mb-4'
    )

    # --- Table 2: SubCategory Vendor Analysis ---
    t2_df = df_filtered.groupby(['Counter', 'Category', 'Subcategory', 'Vendor_code', 'Vendor_name'], as_index=False).agg({
        'Tags_sold': 'sum',
        'NSV': 'sum',
        'Gold_w': 'sum',
        'Diamond_cts': 'sum',
        'Silver_w': 'sum',
        'Gemstone_nsv': 'sum',
        'Mohor_w': 'sum',
        'Mohor_nsv': 'sum'
    }).sort_values(by='NSV', ascending=False)

    t2_df = add_total_row_table2(t2_df)

    t2_disp = t2_df.copy()
    for col in ['NSV', 'Gemstone_nsv', 'Mohor_nsv']:
        t2_disp[col] = t2_disp[col].apply(format_currency_cell)
    for col in ['Gold_w', 'Diamond_cts', 'Silver_w', 'Mohor_w']:
        t2_disp[col] = t2_disp[col].apply(format_weight_cell)
    t2_disp['Tags_sold'] = t2_disp['Tags_sold'].apply(lambda x: f"{int(x):,}")

    t2_cols = [
        {'name': 'Counter', 'id': 'Counter'},
        {'name': 'Category', 'id': 'Category'},
        {'name': 'Subcategory', 'id': 'Subcategory'},
        {'name': 'Vendor Code', 'id': 'Vendor_code'},
        {'name': 'Vendor Name', 'id': 'Vendor_name'},
        {'name': 'Tags Sold', 'id': 'Tags_sold'},
        {'name': 'NSV', 'id': 'NSV'},
        {'name': 'Gold Weight (g)', 'id': 'Gold_w'},
        {'name': 'Diamond Carats (ct)', 'id': 'Diamond_cts'},
        {'name': 'Silver Weight (g)', 'id': 'Silver_w'},
        {'name': 'Gemstone NSV', 'id': 'Gemstone_nsv'},
        {'name': 'Mohor Weight (g)', 'id': 'Mohor_w'},
        {'name': 'Mohor NSV', 'id': 'Mohor_nsv'}
    ]

    t2_card = dbc.Card(
        [
            dbc.CardHeader(
                html.H5("SubCategory Vendor Analysis Matrix", className='fw-bold mb-0 text-center py-1'),
                style={'borderBottom': '1px solid #E3DFD5', 'backgroundColor': '#FAF9F6'}
            ),
            dbc.CardBody(
                dash_table.DataTable(
                    id='vendor-analysis-subcategory-table',
                    data=t2_disp.to_dict('records'),
                    columns=t2_cols,
                    sort_action='custom',
                    sort_by=[{'column_id': 'NSV', 'direction': 'desc'}],
                    **TABLE_STYLE_2
                ),
                style={'padding': '10px'}
            )
        ],
        className='inv-premium-card mb-4'
    )

    return kpi_layout, t1_card, t2_card

# ---------------------------------------------------
# Callback 2: Export Data Workbook (Excel)
# ---------------------------------------------------
@callback(
    Output('vendor-analysis-download', 'data'),
    Input('vendor-analysis-export-btn', 'n_clicks'),
    [
        State('vendor-analysis-date-filter', 'start_date'),
        State('vendor-analysis-date-filter', 'end_date'),
        State('vendor-analysis-vendor-filter', 'value'),
        State('vendor-analysis-counter-filter', 'value'),
        State('vendor-analysis-category-filter', 'value'),
        State('vendor-analysis-subcategory-filter', 'value')
    ],
    prevent_initial_call=True
)
def export_vendor_analysis_data(n_clicks, start_date, end_date, vendors, counters, categories, subcategories):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "Vendor Analysis Dashboard",
        action="Export Data",
        filters={"start_date": start_date, "end_date": end_date, "vendors": vendors, "counters": counters, "categories": categories, "subcategories": subcategories}
    )

    if not start_date or not end_date:
        return no_update
        
    df = load_vendor_sales_data()
    if df.empty:
        return no_update
        
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    mask = (df['Date'] >= start_dt) & (df['Date'] <= end_dt)
    df_filtered = df[mask].copy()
    if vendors:
        df_filtered = df_filtered[df_filtered['Vendor_name'].isin(vendors)]
    if counters:
        df_filtered = df_filtered[df_filtered['Counter'].isin(counters)]
    if categories:
        df_filtered = df_filtered[df_filtered['Category'].isin(categories)]
    if subcategories:
        df_filtered = df_filtered[df_filtered['Subcategory'].isin(subcategories)]
        
    if df_filtered.empty:
        return no_update

    # Generate tables
    t1_df = df_filtered.groupby(['Vendor_name'], as_index=False).agg({
        'Tags_sold': 'sum',
        'NSV': 'sum',
        'Gold_w': 'sum',
        'Diamond_cts': 'sum',
        'Silver_w': 'sum',
        'Mohor_w': 'sum',
        'Mohor_nsv': 'sum',
        'Gemstone_nsv': 'sum'
    }).sort_values(by='NSV', ascending=False)
    t1_df = add_total_row_table1(t1_df)
    
    t2_df = df_filtered.groupby(['Counter', 'Category', 'Subcategory', 'Vendor_code', 'Vendor_name'], as_index=False).agg({
        'Tags_sold': 'sum',
        'NSV': 'sum',
        'Gold_w': 'sum',
        'Diamond_cts': 'sum',
        'Silver_w': 'sum',
        'Gemstone_nsv': 'sum',
        'Mohor_w': 'sum',
        'Mohor_nsv': 'sum'
    }).sort_values(by='NSV', ascending=False)
    t2_df = add_total_row_table2(t2_df)
    
    # Write to Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        t1_df.to_excel(writer, sheet_name='Best Vendors', index=False)
        t2_df.to_excel(writer, sheet_name='SubCategory Vendor Analysis', index=False)
        
    output.seek(0)
    filename = f"vendor_analysis_{start_dt.strftime('%Y%m%d')}_to_{end_dt.strftime('%Y%m%d')}.xlsx"
    return dcc.send_bytes(output.getvalue(), filename)

# ---------------------------------------------------
# Reusable Sorting Logic (Pinned TOTAL row)
# ---------------------------------------------------
def parse_formatted_value(val):
    if val is None or val == "":
        return -999999999.0
    val_str = str(val).strip()
    val_str = val_str.replace(",", "").replace(" g", "").replace(" ct", "").replace("%", "")
    try:
        return float(val_str)
    except ValueError:
        return val_str.lower()

def handle_custom_sort(sort_by, data, key_col):
    if not data or not sort_by:
        return no_update
        
    df = pd.DataFrame(data)
    
    # Separate the TOTAL row
    total_mask = df[key_col] == 'TOTAL'
    total_df = df[total_mask]
    data_df = df[~total_mask]
    
    # Sort
    temp_cols = []
    asc_list = []
    for sort_col in sort_by:
        col_id = sort_col['column_id']
        ascending = sort_col['direction'] == 'asc'
        temp_col = f"_sort_{col_id}"
        data_df[temp_col] = data_df[col_id].apply(parse_formatted_value)
        temp_cols.append(temp_col)
        asc_list.append(ascending)
        
    data_df = data_df.sort_values(by=temp_cols, ascending=asc_list, kind='stable')
    data_df = data_df.drop(columns=temp_cols)
    
    # Append TOTAL row back at the bottom
    sorted_df = pd.concat([data_df, total_df], ignore_index=True)
    return sorted_df.to_dict('records')

@callback(
    Output('vendor-analysis-best-table', 'data'),
    Input('vendor-analysis-best-table', 'sort_by'),
    State('vendor-analysis-best-table', 'data'),
    prevent_initial_call=True
)
def sort_table1(sort_by, data):
    return handle_custom_sort(sort_by, data, key_col='Vendor_name')

@callback(
    Output('vendor-analysis-subcategory-table', 'data'),
    Input('vendor-analysis-subcategory-table', 'sort_by'),
    State('vendor-analysis-subcategory-table', 'data'),
    prevent_initial_call=True
)
def sort_table2(sort_by, data):
    return handle_custom_sort(sort_by, data, key_col='Counter')
