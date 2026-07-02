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
# Load & Clean Design Performance Data
# ---------------------------------------------------
def load_design_performance_data():
    design_perf_path = "data/processed/design_performance.xlsx"
    design_perf_parquet_path = "snapshot/design_performance.parquet"
    if os.path.exists(design_perf_parquet_path):
        try:
            df = pd.read_parquet(design_perf_parquet_path)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            return df
        except Exception as e:
            print(f"Error loading design_performance.parquet: {e}")
    elif os.path.exists(design_perf_path):
        try:
            df = pd.read_excel(design_perf_path)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            return df
        except Exception as e:
            print(f"Error loading design_performance.xlsx: {e}")
            
    # Return empty DataFrame with appropriate columns
    return pd.DataFrame(columns=[
        'Date', 'Counter', 'Design Code', 'Ornament Category', 'Ornament Subcategory',
        'weight', 'revenue', 'Tags Sold'
    ])

df_init = load_design_performance_data()

design_options = sorted(df_init['Design Code'].dropna().unique().tolist()) if not df_init.empty else []
counter_options = sorted(df_init['Counter'].dropna().unique().tolist()) if not df_init.empty else []
category_options = sorted(df_init['Ornament Category'].dropna().unique().tolist()) if not df_init.empty else []
subcategory_options = sorted(df_init['Ornament Subcategory'].dropna().unique().tolist()) if not df_init.empty else []

# ---------------------------------------------------
# Default Dates
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

def format_pct_cell(val):
    if pd.isna(val) or val == "" or val is None:
        return ""
    try:
        return f"{float(val):.2f}%"
    except Exception:
        return ""

# ---------------------------------------------------
# UI Table Style
# ---------------------------------------------------
TABLE_STYLE = {
    'page_action': 'native',
    'page_size': 15,
    'style_table': {
        'overflowX': 'auto',
        'overflowY': 'auto',
        'height': '480px',
        'width': '100%'
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
                'filter_query': '{Counter} contains "TOTAL"'
            },
            'fontWeight': 'bold',
            'backgroundColor': '#FAF2DF',
            'color': '#1C1B19'
        },
        {
            'if': {
                'column_id': 'Design Code'
            },
            'fontWeight': 'bold'
        }
    ]
}

# ---------------------------------------------------
# Total Row Helper
# ---------------------------------------------------
def add_total_row(df):
    if df.empty:
        return df
    total_row = {
        'Counter': 'TOTAL',
        'Design Code': '',
        'Ornament Category': '',
        'Ornament Subcategory': '',
        'weight': df['weight'].sum(),
        'Tags Sold': df['Tags Sold'].sum()
    }
    return pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)

# ---------------------------------------------------
# Dashboard Layout
# ---------------------------------------------------
TABLE_COLUMNS = [
    {'name': 'Counter', 'id': 'Counter'},
    {'name': 'Design Code', 'id': 'Design Code'},
    {'name': 'Category', 'id': 'Ornament Category'},
    {'name': 'Sub-category', 'id': 'Ornament Subcategory'},
    {'name': 'Weight Sold', 'id': 'weight'},
    {'name': 'Tags Sold', 'id': 'Tags Sold'},
    {'name': 'Contribution %', 'id': 'contribution_pct'}
]

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
                                    "← Inventory Department",
                                    className='inv-btn-dark px-3 py-1',
                                    size='sm'
                                ),
                                href="/inventory",
                                style={'textDecoration': 'none'}
                            ),
                            html.H2(
                                "Design Performance",
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
                                [
                                    dbc.Button(
                                        "Export Data",
                                        id='design-perf-export-btn',
                                        className='inv-btn-dark px-3 py-1 me-2',
                                        size='sm'
                                    ),
                                    dbc.Button(
                                        "Enter",
                                        id='design-perf-enter-btn',
                                        className='inv-btn-gold px-3 py-1',
                                        size='sm'
                                    )
                                ],
                                className='text-end'
                            ),
                            dcc.Download(
                                id='design-perf-download'
                            )
                        ],
                        width=6
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
                                            id='design-perf-date-filter',
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
                                        html.Label("Design Code", className="fw-bold mb-1 small text-muted"),
                                        dcc.Dropdown(
                                            id='design-perf-design-filter',
                                            options=[{'label': i, 'value': i} for i in design_options],
                                            multi=True,
                                            placeholder='Select Design'
                                        )
                                    ],
                                    width=2
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Counter", className="fw-bold mb-1 small text-muted"),
                                        dcc.Dropdown(
                                            id='design-perf-counter-filter',
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
                                            id='design-perf-category-filter',
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
                                            id='design-perf-subcategory-filter',
                                            options=[{'label': i, 'value': i} for i in subcategory_options],
                                            multi=True,
                                            placeholder='Select Subcategory'
                                        )
                                    ],
                                    width=3
                                )
                            ]
                        )
                    ]
                ),
                className='inv-premium-card mb-4'
            ),

            # Tables Panel (Dynamic Visibility)
            dcc.Loading(
                dbc.Row(
                    id='tables-row-container',
                    children=[
                        dbc.Col(
                            id='diamond-table-col',
                            width=6,
                            children=dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5("Diamond Design Performance Matrix", className='fw-bold mb-0 text-center py-1'),
                                        style={'borderBottom': '1px solid #E3DFD5', 'backgroundColor': '#FAF9F6'}
                                    ),
                                    dbc.CardBody(
                                        dash_table.DataTable(
                                            id='design-perf-diamond-table',
                                            columns=TABLE_COLUMNS,
                                            sort_action='custom',
                                            sort_by=[{'column_id': 'weight', 'direction': 'desc'}],
                                            **TABLE_STYLE
                                        ),
                                        style={'padding': '10px'}
                                    )
                                ],
                                className='inv-premium-card mb-4'
                            )
                        ),
                        dbc.Col(
                            id='gold-table-col',
                            width=6,
                            children=dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5("Gold Design Performance Matrix", className='fw-bold mb-0 text-center py-1'),
                                        style={'borderBottom': '1px solid #E3DFD5', 'backgroundColor': '#FAF9F6'}
                                    ),
                                    dbc.CardBody(
                                        dash_table.DataTable(
                                            id='design-perf-gold-table',
                                            columns=TABLE_COLUMNS,
                                            sort_action='custom',
                                            sort_by=[{'column_id': 'weight', 'direction': 'desc'}],
                                            **TABLE_STYLE
                                        ),
                                        style={'padding': '10px'}
                                    )
                                ],
                                className='inv-premium-card mb-4'
                            )
                        )
                    ],
                    className='g-3'
                ),
                type='default',
                color='#C5A059'
            )
        ],
        fluid=True
    )
)

# ---------------------------------------------------
# Callback 1: Filter & Render Tables
# ---------------------------------------------------
@callback(
    [
        Output('diamond-table-col', 'style'),
        Output('gold-table-col', 'style'),
        Output('diamond-table-col', 'width'),
        Output('gold-table-col', 'width'),
        Output('design-perf-diamond-table', 'data'),
        Output('design-perf-gold-table', 'data')
    ],
    [
        Input('design-perf-enter-btn', 'n_clicks'),
        Input('url', 'pathname')
    ],
    [
        State('design-perf-date-filter', 'start_date'),
        State('design-perf-date-filter', 'end_date'),
        State('design-perf-design-filter', 'value'),
        State('design-perf-counter-filter', 'value'),
        State('design-perf-category-filter', 'value'),
        State('design-perf-subcategory-filter', 'value')
    ]
)
def render_design_performance(n_clicks, pathname, start_date, end_date, designs, counters, categories, subcategories):
    start_dt = pd.to_datetime(start_date) if start_date else pd.to_datetime(default_start_date)
    end_dt = pd.to_datetime(end_date) if end_date else pd.to_datetime(default_end_date)

    df = load_design_performance_data()
    if df.empty:
        return {'display': 'none'}, {'display': 'none'}, 0, 0, [], []

    # Apply Filters
    mask = (df['Date'] >= start_dt) & (df['Date'] <= end_dt)
    df_filtered = df[mask].copy()

    if designs:
        df_filtered = df_filtered[df_filtered['Design Code'].isin(designs)]
    if counters:
        df_filtered = df_filtered[df_filtered['Counter'].isin(counters)]
    if categories:
        df_filtered = df_filtered[df_filtered['Ornament Category'].isin(categories)]
    if subcategories:
        df_filtered = df_filtered[df_filtered['Ornament Subcategory'].isin(subcategories)]

    # Determine Dynamic Table Visibility
    show_diamond = False
    show_gold = False

    if not counters:
        show_diamond = True
        show_gold = True
    else:
        # Check counter values
        if 'DIAMOND' in counters:
            show_diamond = True
        if any(c.startswith('G-') for c in counters):
            show_gold = True

    # 1. Diamond Table Data
    df_diamond = df_filtered[df_filtered['Counter'] == 'DIAMOND'].copy()
    t_diamond = df_diamond.groupby(['Counter', 'Design Code', 'Ornament Category', 'Ornament Subcategory'], as_index=False).agg({
        'weight': 'sum',
        'Tags Sold': 'sum'
    }).sort_values(by='weight', ascending=False)
    
    if not t_diamond.empty:
        t_diamond['subcat_total'] = t_diamond.groupby('Ornament Subcategory')['weight'].transform('sum')
        t_diamond['contribution_pct'] = np.where(
            t_diamond['subcat_total'] > 0,
            (t_diamond['weight'] / t_diamond['subcat_total']) * 100,
            0.0
        )
        t_diamond = t_diamond.drop(columns=['subcat_total'])
    else:
        t_diamond['contribution_pct'] = pd.Series(dtype='float64')
        
    t_diamond = add_total_row(t_diamond)
    
    t_disp_diamond = t_diamond.copy()
    t_disp_diamond['weight'] = t_disp_diamond['weight'].apply(format_weight_cell)
    t_disp_diamond['Tags Sold'] = t_disp_diamond['Tags Sold'].apply(lambda x: f"{int(x):,}")
    t_disp_diamond['contribution_pct'] = t_disp_diamond['contribution_pct'].apply(format_pct_cell)

    # 2. Gold Table Data
    df_gold = df_filtered[df_filtered['Counter'].astype(str).str.startswith('G-')].copy()
    t_gold = df_gold.groupby(['Counter', 'Design Code', 'Ornament Category', 'Ornament Subcategory'], as_index=False).agg({
        'weight': 'sum',
        'Tags Sold': 'sum'
    }).sort_values(by='weight', ascending=False)
    
    if not t_gold.empty:
        t_gold['subcat_total'] = t_gold.groupby('Ornament Subcategory')['weight'].transform('sum')
        t_gold['contribution_pct'] = np.where(
            t_gold['subcat_total'] > 0,
            (t_gold['weight'] / t_gold['subcat_total']) * 100,
            0.0
        )
        t_gold = t_gold.drop(columns=['subcat_total'])
    else:
        t_gold['contribution_pct'] = pd.Series(dtype='float64')
        
    t_gold = add_total_row(t_gold)
    
    t_disp_gold = t_gold.copy()
    t_disp_gold['weight'] = t_disp_gold['weight'].apply(format_weight_cell)
    t_disp_gold['Tags Sold'] = t_disp_gold['Tags Sold'].apply(lambda x: f"{int(x):,}")
    t_disp_gold['contribution_pct'] = t_disp_gold['contribution_pct'].apply(format_pct_cell)

    # Column layout states
    diamond_style = {'display': 'block'} if show_diamond else {'display': 'none'}
    gold_style = {'display': 'block'} if show_gold else {'display': 'none'}

    diamond_width = 12 if show_diamond and not show_gold else 6
    gold_width = 12 if show_gold and not show_diamond else 6

    return diamond_style, gold_style, diamond_width, gold_width, t_disp_diamond.to_dict('records'), t_disp_gold.to_dict('records')

# ---------------------------------------------------
# Callback 2: Export Data Workbook (Excel)
# ---------------------------------------------------
@callback(
    Output('design-perf-download', 'data'),
    Input('design-perf-export-btn', 'n_clicks'),
    [
        State('design-perf-date-filter', 'start_date'),
        State('design-perf-date-filter', 'end_date'),
        State('design-perf-design-filter', 'value'),
        State('design-perf-counter-filter', 'value'),
        State('design-perf-category-filter', 'value'),
        State('design-perf-subcategory-filter', 'value')
    ],
    prevent_initial_call=True
)
def export_design_perf_data(n_clicks, start_date, end_date, designs, counters, categories, subcategories):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "Design Performance Dashboard",
        action="Export Data",
        filters={"start_date": start_date, "end_date": end_date, "designs": designs, "counters": counters, "categories": categories, "subcategories": subcategories}
    )

    if not start_date or not end_date:
        return no_update
        
    df = load_design_performance_data()
    if df.empty:
        return no_update
        
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    mask = (df['Date'] >= start_dt) & (df['Date'] <= end_dt)
    df_filtered = df[mask].copy()
    
    if designs:
        df_filtered = df_filtered[df_filtered['Design Code'].isin(designs)]
    if counters:
        df_filtered = df_filtered[df_filtered['Counter'].isin(counters)]
    if categories:
        df_filtered = df_filtered[df_filtered['Ornament Category'].isin(categories)]
    if subcategories:
        df_filtered = df_filtered[df_filtered['Ornament Subcategory'].isin(subcategories)]
        
    if df_filtered.empty:
        return no_update

    # 1. Diamond Export Table
    df_diamond = df_filtered[df_filtered['Counter'] == 'DIAMOND'].copy()
    t_diamond = df_diamond.groupby(['Counter', 'Design Code', 'Ornament Category', 'Ornament Subcategory'], as_index=False).agg({
        'weight': 'sum',
        'Tags Sold': 'sum'
    }).sort_values(by='weight', ascending=False)
    
    if not t_diamond.empty:
        t_diamond['subcat_total'] = t_diamond.groupby('Ornament Subcategory')['weight'].transform('sum')
        t_diamond['Contribution %'] = np.where(
            t_diamond['subcat_total'] > 0,
            (t_diamond['weight'] / t_diamond['subcat_total']) * 100,
            0.0
        )
        t_diamond = t_diamond.drop(columns=['subcat_total'])
    else:
        t_diamond['Contribution %'] = pd.Series(dtype='float64')
        
    t_diamond = add_total_row(t_diamond)

    # 2. Gold Export Table
    df_gold = df_filtered[df_filtered['Counter'].astype(str).str.startswith('G-')].copy()
    t_gold = df_gold.groupby(['Counter', 'Design Code', 'Ornament Category', 'Ornament Subcategory'], as_index=False).agg({
        'weight': 'sum',
        'Tags Sold': 'sum'
    }).sort_values(by='weight', ascending=False)
    
    if not t_gold.empty:
        t_gold['subcat_total'] = t_gold.groupby('Ornament Subcategory')['weight'].transform('sum')
        t_gold['Contribution %'] = np.where(
            t_gold['subcat_total'] > 0,
            (t_gold['weight'] / t_gold['subcat_total']) * 100,
            0.0
        )
        t_gold = t_gold.drop(columns=['subcat_total'])
    else:
        t_gold['Contribution %'] = pd.Series(dtype='float64')
        
    t_gold = add_total_row(t_gold)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        t_diamond.to_excel(writer, sheet_name='Diamond Design Performance', index=False)
        t_gold.to_excel(writer, sheet_name='Gold Design Performance', index=False)
        
    output.seek(0)
    filename = f"design_performance_{start_dt.strftime('%Y%m%d')}_to_{end_dt.strftime('%Y%m%d')}.xlsx"
    return dcc.send_bytes(output.getvalue(), filename)

# ---------------------------------------------------
# Sorting Logic (Pinned TOTAL row)
# ---------------------------------------------------
def parse_formatted_value(val):
    if val is None or val == "":
        return -999999999.0
    val_str = str(val).strip()
    val_str = val_str.replace(",", "").replace("%", "")
    try:
        return float(val_str)
    except ValueError:
        return val_str.lower()

def handle_custom_sort(sort_by, data):
    if not data or not sort_by:
        return no_update
        
    df = pd.DataFrame(data)
    
    # Separate the TOTAL row
    total_mask = df['Counter'] == 'TOTAL'
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
    Output('design-perf-diamond-table', 'data'),
    Input('design-perf-diamond-table', 'sort_by'),
    State('design-perf-diamond-table', 'data'),
    prevent_initial_call=True
)
def sort_diamond_table(sort_by, data):
    return handle_custom_sort(sort_by, data)

@callback(
    Output('design-perf-gold-table', 'data'),
    Input('design-perf-gold-table', 'sort_by'),
    State('design-perf-gold-table', 'data'),
    prevent_initial_call=True
)
def sort_gold_table(sort_by, data):
    return handle_custom_sort(sort_by, data)
