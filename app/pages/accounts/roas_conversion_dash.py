from dash import (
    html,
    dcc,
    dash_table,
    callback,
    Input,
    Output,
    State,
    callback_context,
    no_update
)
import pandas as pd
import os
from datetime import datetime
import dash_bootstrap_components as dbc
from flask import session

from backend.services.rls import get_allowed_locations
from backend.cache.data_cache import rm_zm_df, merged_sales_df
from backend.services.accounts.roas_conversion_service import (
    get_available_months,
    get_roas_conversion_report,
    get_roas_conversion_kpis,
    METRICS_MAP
)

# ---------------------------------------------------
# Indian Formatting Helper
# ---------------------------------------------------
def indian_format(value, decimals=2):
    try:
        value = float(value)
    except Exception:
        return value

    if pd.isna(value):
        return ''

    negative = value < 0
    value = abs(value)

    # Format to fixed decimals first
    fixed_str = f"{value:.{decimals}f}"
    if '.' in fixed_str:
        integer_str, decimal_str = fixed_str.split('.')
        decimal_str = '.' + decimal_str
    else:
        integer_str = fixed_str
        decimal_str = ''

    if len(integer_str) > 3:
        last_three = integer_str[-3:]
        remaining = integer_str[:-3]
        parts = []
        while len(remaining) > 2:
            parts.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            parts.insert(0, remaining)
        integer_str = ','.join(parts) + ',' + last_three
    else:
        integer_str = integer_str

    formatted = integer_str + decimal_str
    if negative:
        formatted = '-' + formatted

    return formatted


def format_cell_value(col_id_or_name, val):
    if pd.isna(val) or val == '' or val is None:
        return ''
    
    col_lower = str(col_id_or_name).lower()
    
    # Check for percentage metrics
    if 'acos' in col_lower or 'ad cost of sales' in col_lower:
        return f"{indian_format(val, 2)}%"
    
    # Check for footfall (integer)
    if 'footfall' in col_lower:
        return str(indian_format(val, 0))
    
    # Check for other numeric metrics
    if any(m in col_lower for m in ['ad_expense', 'ad expense', 'value', 'revenue', 'nsv', 'cpf', 'rpv', 'cost per footfall', 'revenue per visits']):
        return str(indian_format(val, 2))
        
    return str(val)


# ---------------------------------------------------
# Fetch sorted months
# ---------------------------------------------------
all_available_months = get_available_months()
default_month_selection = [all_available_months[-1]] if all_available_months else []

# Options for filters
location_options = sorted(
    rm_zm_df['location'].dropna().unique().tolist()
)

# ---------------------------------------------------
# Layout Design
# ---------------------------------------------------
layout = html.Div(
    className='inv-premium-page-blue',
    children=dbc.Container([
        # Hidden Stores for State management
        dcc.Store(id="roas-mode-toggle", data="Consolidate"),

        # Top Header Row
        dbc.Row([
            dbc.Col([
                html.A(
                    dbc.Button(
                        "← Accounts Home",
                        className='inv-btn-blue-dark px-3 py-1',
                        size='sm'
                    ),
                    href="/accounts",
                    style={'textDecoration': 'none'}
                ),
                html.H2(
                    'ROAS & Conversion Analytics',
                    className='fw-bold mt-3 mb-1',
                    style={'fontFamily': 'Outfit', 'color': '#0F172A'}
                ),
            ], width=7),

            dbc.Col([
                html.Div([
                    html.Span(
                        f"Last Updated G/L Entry: {all_available_months[-1] if all_available_months else 'N/A'}",
                        className='fw-bold small me-3',
                        style={'color': '#1E3A8A', 'fontFamily': 'Outfit'}
                    ),
                    html.Span(
                        f"Last Updated Sales: {merged_sales_df['Invoice Date'].max().strftime('%d-%b-%Y') if not merged_sales_df.empty else 'N/A'}",
                        className='fw-bold small',
                        style={'color': '#1E3A8A', 'fontFamily': 'Outfit'}
                    )
                ], className='text-end mb-3'),

                html.Div([
                    dbc.Button(
                        'Export CSV',
                        id='roas-export-btn',
                        className='inv-btn-blue-dark px-3 py-1 me-2 shadow-sm',
                        size='sm',
                    ),
                    dbc.Button(
                        'Enter',
                        id='roas-enter-btn',
                        className='inv-btn-blue px-4 py-1 shadow-sm',
                        size='sm',
                    ),
                ], className='text-end'),

                dcc.Download(id='roas-download'),
            ], width=5),
        ], className='mb-4 mt-2 align-items-end'),

        # Segmented Button Mode Toggle Group
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.ButtonGroup([
                        dbc.Button(
                            "Consolidate Period",
                            id="roas-btn-consolidate",
                            color="primary",
                            className="px-4 py-2 fw-bold"
                        ),
                        dbc.Button(
                            "Compare Months Side-by-Side",
                            id="roas-btn-compare",
                            color="outline-primary",
                            className="px-4 py-2 fw-bold"
                        ),
                    ], className="pa-toggle-group")
                ], className="text-center mb-4")
            ], width=12)
        ]),

        # Filter Options Card
        dbc.Card(
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Year Month", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='roas-month-filter',
                            options=[
                                {'label': i, 'value': i}
                                for i in all_available_months
                            ],
                            value=default_month_selection,
                            multi=True,
                            placeholder='Select Year Month',
                        ),
                    ], xs=12, md=4),

                    dbc.Col([
                        html.Label("Location", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='roas-location-filter',
                            options=[
                                {'label': i, 'value': i}
                                for i in location_options
                            ],
                            multi=True,
                            placeholder='Select Location',
                        ),
                    ], xs=12, md=4),

                    dbc.Col([
                        html.Label("Columns Selector", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='roas-columns-filter',
                            options=[
                                {'label': k, 'value': k}
                                for k in METRICS_MAP.keys()
                            ],
                            value=list(METRICS_MAP.keys()),
                            multi=True,
                            placeholder='Select Columns',
                        ),
                    ], xs=12, md=4),
                ], className='g-3'),
            ]),
            className='inv-blue-card mb-4',
        ),

        # KPI Cards Row
        dbc.Row([
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.Div("CPF (Cost Per Footfall)", className="text-muted small fw-bold mb-1 text-center"),
                        html.H3(id="roas-kpi-cpf", className="fw-bold text-center text-primary mb-0")
                    ]),
                    className="shadow-sm border-0 bg-white"
                )
            ], xs=12, md=4, className="mb-3"),

            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.Div("ACoS (Ad Cost of Sales)", className="text-muted small fw-bold mb-1 text-center"),
                        html.H3(id="roas-kpi-acos", className="fw-bold text-center text-success mb-0")
                    ]),
                    className="shadow-sm border-0 bg-white"
                )
            ], xs=12, md=4, className="mb-3"),

            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.Div("RPV (Revenue Per Visits)", className="text-muted small fw-bold mb-1 text-center"),
                        html.H3(id="roas-kpi-rpv", className="fw-bold text-center text-info mb-0")
                    ]),
                    className="shadow-sm border-0 bg-white"
                )
            ], xs=12, md=4, className="mb-3"),
        ], className="mb-3"),

        # Results Grid Container
        dcc.Loading(
            html.Div(id='roas-table-container'),
            type='circle',
        ),
    ], fluid=True, style={'padding': '0px'})
)


# ---------------------------------------------------
# Table Builder Helper
# ---------------------------------------------------
def build_report_datatable(df, columns_config):
    # Formats cell data according to metric types
    formatted_df = df.copy()
    formatted_df = formatted_df.astype(object)
    for idx in formatted_df.index:
        for col in formatted_df.columns:
            if col in ['code', 'location_name']:
                continue
            
            value = formatted_df.loc[idx, col]
            formatted_df.loc[idx, col] = format_cell_value(col, value)

    # Setup cell styling alignments - BOTH Code and Location are bold
    left_align_cols = ['code', 'location_name']
    cell_conditional = [
        {
            'if': {'column_id': col},
            'textAlign': 'center' if col == 'code' else 'left',
            'fontWeight': 'bold',
            'minWidth': '110px' if col == 'code' else '220px',
            'width': '110px' if col == 'code' else '220px',
            'maxWidth': '140px' if col == 'code' else '260px',
        }
        for col in left_align_cols
    ]

    # Dynamic columns definitions
    table_columns = []
    for col in columns_config:
        col_id = col['id']
        col_name = col['name']
        table_columns.append({
            'name': col_name,
            'id': col_id,
            'type': 'text'
        })

    # Highlighting the TOTAL row
    style_data_conditional = [
        {
            'if': {
                'filter_query': '{location_name} eq "TOTAL"',
            },
            'fontWeight': 'bold',
            'backgroundColor': '#FAF2DF',
            'color': '#1C1B19'
        }
    ]

    return dbc.Card([
        dbc.CardHeader(
            html.H5(
                "ROAS & Conversion Report Overview",
                className='fw-bold mb-0',
                style={'textAlign': 'left', 'color': '#0F172A', 'fontFamily': 'Outfit'},
            ),
            style={'backgroundColor': '#F8FAFC', 'borderBottom': '1px solid #E2E8F0'},
        ),
        dbc.CardBody(
            dash_table.DataTable(
                data=formatted_df.to_dict('records'),
                columns=table_columns,
                fixed_rows={'headers': True},
                page_action='none',
                style_as_list_view=True,
                style_table={
                    'overflowX': 'auto',
                    'overflowY': 'auto',
                    'maxHeight': '650px',
                    'width': '100%',
                    'margin': '0 auto',
                },
                style_cell={
                    'textAlign': 'right',
                    'padding': '10px 14px',
                    'fontSize': '13px',
                    'fontFamily': "'Outfit', 'Inter', sans-serif",
                    'minWidth': '140px',
                    'width': '160px',
                    'maxWidth': '220px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'backgroundColor': '#FFFFFF',
                    'color': '#334155',
                    'borderBottom': '1px solid #F1F5F9',
                },
                style_cell_conditional=cell_conditional,
                style_data_conditional=style_data_conditional,
                style_header={
                    'fontWeight': 'bold',
                    'backgroundColor': '#1E293B',
                    'color': '#F8FAFC',
                    'fontSize': '13px',
                    'textAlign': 'center',
                    'fontFamily': "'Outfit', sans-serif",
                    'border': '1px solid #CBD5E1',
                    'padding': '12px 14px',
                },
            ),
            style={'padding': '6px'},
        ),
    ], className='inv-blue-card mb-4')


# ---------------------------------------------------
# Toggle Button Group Handler
# ---------------------------------------------------
@callback(
    [
        Output('roas-mode-toggle', 'data'),
        Output('roas-btn-consolidate', 'color'),
        Output('roas-btn-compare', 'color'),
    ],
    [
        Input('roas-btn-consolidate', 'n_clicks'),
        Input('roas-btn-compare', 'n_clicks'),
    ],
    [
        State('roas-mode-toggle', 'data')
    ]
)
def toggle_report_mode(consolidate_clicks, compare_clicks, current_mode):
    ctx = callback_context
    if not ctx.triggered:
        return current_mode, "primary" if current_mode == "Consolidate" else "outline-primary", "primary" if current_mode == "Compare" else "outline-primary"

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == 'roas-btn-consolidate':
        return "Consolidate", "primary", "outline-primary"
    elif triggered_id == 'roas-btn-compare':
        return "Compare", "outline-primary", "primary"

    return current_mode, "primary" if current_mode == "Consolidate" else "outline-primary", "primary" if current_mode == "Compare" else "outline-primary"


# ---------------------------------------------------
# Primary Enter Search Callback (Table & KPIs)
# ---------------------------------------------------
@callback(
    [
        Output('roas-table-container', 'children'),
        Output('roas-kpi-cpf', 'children'),
        Output('roas-kpi-acos', 'children'),
        Output('roas-kpi-rpv', 'children')
    ],
    Input('roas-enter-btn', 'n_clicks'),
    State('roas-mode-toggle', 'data'),
    State('roas-month-filter', 'value'),
    State('roas-columns-filter', 'value'),
    State('roas-location-filter', 'value'),
)
def render_roas_table(
    n_clicks,
    mode,
    selected_months,
    selected_metrics,
    locations
):
    if not selected_months:
        return (
            html.Div("Please select at least one Year Month and click Enter.", className="text-center py-5 text-danger fw-bold"),
            "N/A", "N/A", "N/A"
        )
    if not selected_metrics:
        return (
            html.Div("Please select at least one Column Metric and click Enter.", className="text-center py-5 text-danger fw-bold"),
            "N/A", "N/A", "N/A"
        )

    # 1. Update KPIs
    kpis = get_roas_conversion_kpis(selected_months, locations)
    formatted_cpf = indian_format(kpis['cpf'], 2)
    formatted_acos = f"{indian_format(kpis['acos'], 2)}%"
    formatted_rpv = indian_format(kpis['rpv'], 2)

    # 2. Update Table
    try:
        df, columns_config = get_roas_conversion_report(
            selected_months=selected_months,
            mode=mode,
            selected_metrics=selected_metrics,
            locations=locations
        )
    except Exception as e:
        import traceback
        return (
            html.Div([
                html.H5("Error calculating metrics:", className="text-danger fw-bold"),
                html.Pre(traceback.format_exc(), style={'fontSize': '12px', 'color': '#7F1D1D'})
            ], className="p-3 border border-danger rounded bg-red-50"),
            formatted_cpf, formatted_acos, formatted_rpv
        )

    if df.empty:
        return (
            html.Div("No data matching your selection and RLS permissions was found.", className="text-center py-5 text-muted fw-bold"),
            formatted_cpf, formatted_acos, formatted_rpv
        )

    table_element = build_report_datatable(df, columns_config)
    return table_element, formatted_cpf, formatted_acos, formatted_rpv


# ---------------------------------------------------
# Export CSV Callback
# ---------------------------------------------------
@callback(
    Output('roas-download', 'data'),
    Input('roas-export-btn', 'n_clicks'),
    State('roas-mode-toggle', 'data'),
    State('roas-month-filter', 'value'),
    State('roas-columns-filter', 'value'),
    State('roas-location-filter', 'value'),
    prevent_initial_call=True,
)
def export_roas_report(
    n_clicks,
    mode,
    selected_months,
    selected_metrics,
    locations
):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "ROAS & Conversion Analytics Dashboard",
        action="Export Data",
        filters={"mode": mode, "selected_months": selected_months, "selected_metrics": selected_metrics, "locations": locations}
    )

    if not selected_months or not selected_metrics:
        return None

    try:
        df, columns_config = get_roas_conversion_report(
            selected_months=selected_months,
            mode=mode,
            selected_metrics=selected_metrics,
            locations=locations
        )
    except Exception:
        return None

    if df.empty:
        return None

    col_mapping = {col['id']: col['name'] for col in columns_config}
    export_df = df.copy()
    export_df = export_df.rename(columns={'code': 'Code', 'location_name': 'Location'})
    export_df = export_df.rename(columns=col_mapping)

    return dcc.send_data_frame(
        export_df.to_csv,
        'roas_conversion_analytics_export.csv',
        index=False,
    )


# ---------------------------------------------------
# Location Filter dynamic options according to RLS
# ---------------------------------------------------
@callback(
    Output('roas-location-filter', 'options'),
    Input('roas-location-filter', 'id')
)
def populate_roas_location_filter_options(_):
    allowed_locations = session.get('locations', [])
    if not allowed_locations:
        return []
    if 'ALL' in allowed_locations:
        locs = sorted(rm_zm_df['location'].dropna().unique().tolist())
    else:
        locs = sorted(allowed_locations)
    return [{'label': i, 'value': i} for i in locs]
