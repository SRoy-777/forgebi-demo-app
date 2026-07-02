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
import dash_bootstrap_components as dbc
from flask import session

from backend.services.rls import get_allowed_locations
from backend.cache.data_cache import rm_zm_df
from backend.services.accounts.profitability_analysis_service import (
    get_available_months,
    get_profitability_report,
    get_filtered_data,
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

    formatted = integer_str + decimal_str
    if negative:
        formatted = '-' + formatted

    return formatted


def format_cell_value(col_id_or_name, val):
    if pd.isna(val) or val == '' or val is None:
        return ''
    
    col_lower = str(col_id_or_name).lower()
    
    # Check for percentage metrics first
    if 'ratio' in col_lower or 'gp_ratio' in col_lower or 'sales_ratio' in col_lower:
        return f"{indian_format(val, 2)}%"
    
    # Check for count / employee / sales / gp / area metrics: always format to 2 decimal places
    if any(m in col_lower for m in ['sales', 'profit', 'gp', 'employee', 'area', 'sq_ft', 'sq ft']):
        return str(indian_format(val, 2))
        
    return str(val)


# ---------------------------------------------------
# Options for filters
# ---------------------------------------------------
location_options = sorted(
    rm_zm_df['location'].dropna().unique().tolist()
)

# Fetch sorted months
all_available_months = get_available_months()
default_month_selection = [all_available_months[-1]] if all_available_months else []


# ---------------------------------------------------
# Layout Design
# ---------------------------------------------------
layout = html.Div(
    className='inv-premium-page-blue',
    children=dbc.Container([
        # Hidden Stores for State management
        dcc.Store(id="pa-mode-toggle", data="Consolidate"),

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
                    'Profitability Analysis',
                    className='fw-bold mt-3 mb-1',
                    style={'fontFamily': 'Outfit', 'color': '#0F172A'}
                ),
            ], width=8),

            dbc.Col([
                html.Div([
                    dbc.Button(
                        'Download Source File',
                        id='pa-download-source-btn',
                        className='inv-btn-blue-dark px-3 py-1 mb-2 shadow-sm',
                        size='sm',
                    ),
                ], className='text-end'),

                html.Div(
                    f"Last Updated Month: {all_available_months[-1] if all_available_months else 'N/A'}",
                    className='text-end fw-bold mb-2',
                    style={'color': '#1E3A8A', 'fontFamily': 'Outfit'},
                ),

                html.Div([
                    dbc.Button(
                        'Export CSV',
                        id='pa-export-btn',
                        className='inv-btn-blue-dark px-3 py-1 me-2 shadow-sm',
                        size='sm',
                    ),
                    dbc.Button(
                        'Enter',
                        id='pa-enter-btn',
                        className='inv-btn-blue px-4 py-1 shadow-sm',
                        size='sm',
                    ),
                ], className='text-end'),

                dcc.Download(id='pa-download'),
                dcc.Download(id='pa-download-source'),
            ], width=4),
        ], className='mb-4 mt-2 align-items-end'),

        # Segmented Button Mode Toggle Group
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.ButtonGroup([
                        dbc.Button(
                            "Consolidate Period",
                            id="pa-btn-consolidate",
                            color="primary",
                            className="px-4 py-2 fw-bold"
                        ),
                        dbc.Button(
                            "Compare Months Side-by-Side",
                            id="pa-btn-compare",
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
                            id='pa-month-filter',
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
                            id='pa-location-filter',
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
                            id='pa-columns-filter',
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

        # Results Grid Container
        dcc.Loading(
            html.Div(id='pa-table-container'),
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
    formatted_df = formatted_df.astype(object) # Prevent pandas FutureWarning by casting to object type before assigning string formatted values
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
            'fontWeight': 'bold', # Bold style applied to both Code and Location
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

    # Highlighting rows with Code == "Office" at the very end
    style_data_conditional = [
        {
            'if': {
                'filter_query': '{code} eq "Office"',
            },
            'backgroundColor': '#F8FAFC',
            'fontStyle': 'italic',
            'color': '#475569'
        }
    ]

    return dbc.Card([
        dbc.CardHeader(
            html.H5(
                "Profitability Report Overview",
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
                    'backgroundColor': '#1E293B', # Dark slate navy header
                    'color': '#F8FAFC', # Off-white text
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
        Output('pa-mode-toggle', 'data'),
        Output('pa-btn-consolidate', 'color'),
        Output('pa-btn-compare', 'color'),
    ],
    [
        Input('pa-btn-consolidate', 'n_clicks'),
        Input('pa-btn-compare', 'n_clicks'),
    ],
    [
        State('pa-mode-toggle', 'data')
    ]
)
def toggle_report_mode(consolidate_clicks, compare_clicks, current_mode):
    ctx = callback_context
    if not ctx.triggered:
        return current_mode, "primary" if current_mode == "Consolidate" else "outline-primary", "primary" if current_mode == "Compare" else "outline-primary"

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == 'pa-btn-consolidate':
        return "Consolidate", "primary", "outline-primary"
    elif triggered_id == 'pa-btn-compare':
        return "Compare", "outline-primary", "primary"

    return current_mode, "primary" if current_mode == "Consolidate" else "outline-primary", "primary" if current_mode == "Compare" else "outline-primary"


# ---------------------------------------------------
# Primary Enter Search Callback
# ---------------------------------------------------
@callback(
    Output('pa-table-container', 'children'),
    Input('pa-enter-btn', 'n_clicks'),
    State('pa-mode-toggle', 'data'),
    State('pa-month-filter', 'value'),
    State('pa-columns-filter', 'value'),
    State('pa-location-filter', 'value'),
)
def render_profitability_table(
    n_clicks,
    mode,
    selected_months,
    selected_metrics,
    locations
):
    if not selected_months:
        return html.Div(
            "Please select at least one Year Month period in filters and click Enter.",
            className="text-center py-5 text-danger fw-bold"
        )
    if not selected_metrics:
        return html.Div(
            "Please select at least one Column Metric and click Enter.",
            className="text-center py-5 text-danger fw-bold"
        )

    try:
        df, columns_config = get_profitability_report(
            selected_months=selected_months,
            mode=mode,
            selected_metrics=selected_metrics,
            locations=locations,
            rms=None,
            zms=None
        )
    except Exception as e:
        import traceback
        return html.Div([
            html.H5("Error calculating metrics:", className="text-danger fw-bold"),
            html.Pre(traceback.format_exc(), style={'fontSize': '12px', 'color': '#7F1D1D'})
        ], className="p-3 border border-danger rounded bg-red-50")

    if df.empty:
        return html.Div(
            "No data matching your selection and RLS permissions was found.",
            className="text-center py-5 text-muted fw-bold"
        )

    return build_report_datatable(df, columns_config)


# ---------------------------------------------------
# Export CSV Callback
# ---------------------------------------------------
@callback(
    Output('pa-download', 'data'),
    Input('pa-export-btn', 'n_clicks'),
    State('pa-mode-toggle', 'data'),
    State('pa-month-filter', 'value'),
    State('pa-columns-filter', 'value'),
    State('pa-location-filter', 'value'),
    prevent_initial_call=True,
)
def export_profitability_report(
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
        "Profitability Analysis Dashboard",
        action="Export Data",
        filters={"mode": mode, "selected_months": selected_months, "selected_metrics": selected_metrics, "locations": locations}
    )

    if not selected_months or not selected_metrics:
        return None

    try:
        df, columns_config = get_profitability_report(
            selected_months=selected_months,
            mode=mode,
            selected_metrics=selected_metrics,
            locations=locations,
            rms=None,
            zms=None
        )
    except Exception:
        return None

    if df.empty:
        return None

    # Apply nice labels to columns in dynamic dataframe before saving
    col_mapping = {col['id']: col['name'] for col in columns_config}
    export_df = df.copy()
    
    # Sort out code and location column names for export
    export_df = export_df.rename(columns={'code': 'Code', 'location_name': 'Location'})
    
    # Map metrics columns
    export_df = export_df.rename(columns=col_mapping)

    return dcc.send_data_frame(
        export_df.to_csv,
        'profitability_analysis_export.csv',
        index=False,
    )


# ---------------------------------------------------
# Download Source File Callback
# ---------------------------------------------------
@callback(
    Output('pa-download-source', 'data'),
    Input('pa-download-source-btn', 'n_clicks'),
    State('pa-month-filter', 'value'),
    prevent_initial_call=True,
)
def download_source_file(n_clicks, selected_months):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "Profitability Analysis Dashboard",
        action="Download Source File",
        filters={"selected_months": selected_months}
    )

    if not selected_months:
        return None

    df = get_filtered_data(selected_months=selected_months)
    if df.empty:
        return None

    # Remove temporary columns if present to make output cleaner
    cols_to_drop = ['location_name', 'code']
    cleaned_df = df.copy()
    for col in cols_to_drop:
        if col in cleaned_df.columns:
            cleaned_df = cleaned_df.drop(columns=[col])

    return dcc.send_data_frame(
        cleaned_df.to_csv,
        'consolidated_pl_source_export.csv',
        index=False
    )


# ---------------------------------------------------
# Location Filter dynamic options according to RLS
# ---------------------------------------------------
@callback(
    Output('pa-location-filter', 'options'),
    Input('pa-location-filter', 'id')
)
def populate_pa_location_filter_options(_):
    allowed_locations = session.get('locations', [])
    if not allowed_locations:
        return []
    if 'ALL' in allowed_locations:
        locs = sorted(rm_zm_df['location'].dropna().unique().tolist())
    else:
        locs = sorted(allowed_locations)
    return [{'label': i, 'value': i} for i in locs]
