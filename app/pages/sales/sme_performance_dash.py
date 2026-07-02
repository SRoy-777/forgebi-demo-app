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
import io
import pandas as pd
from datetime import datetime
import dash_bootstrap_components as dbc
from flask import session

from backend.services.rls import get_allowed_locations
from backend.cache.data_cache import (
    merged_sales_df,
    rm_zm_df,
    targets_df
)
from backend.services.sales.comparison import (
    prepare_comparison_data,
    get_nsv_comparison,
    get_gold_comparison,
    get_diamond_comparison,
    get_silver_comparison,
    get_gemstone_comparison,
    get_mohor_comparison,
    get_mc_comparison,
    get_invoice_comparison,
    get_tag_comparison,
    get_scheme_comparison
)

# ---------------------------------------------------
# Filter Options
# ---------------------------------------------------
rm_options = [
    {'label': rm, 'value': rm}
    for rm in sorted(rm_zm_df['rm'].dropna().unique())
]

zm_options = [
    {'label': zm, 'value': zm}
    for zm in sorted(rm_zm_df['zm'].dropna().unique())
]

# ---------------------------------------------------
# Last Updated & Default Dates
# ---------------------------------------------------
last_updated = merged_sales_df['Invoice Date'].max()
if pd.isna(last_updated):
    last_updated = datetime.now()

last_updated_text = last_updated.strftime("%d-%b-%Y")
last_invoice_date = pd.to_datetime(last_updated)
default_end_date = last_invoice_date.date()
default_start_date = last_invoice_date.replace(day=1).date()

# ---------------------------------------------------
# Indian Number Format Helper
# ---------------------------------------------------
def indian_format(number, decimals=0):
    if pd.isna(number):
        return "0"
    number = round(number, decimals)
    sign = "-" if number < 0 else ""
    number = abs(number)
    int_part = int(number)
    formatted_number = f"{number:.{decimals}f}"
    
    if "." in formatted_number:
        decimal_part = formatted_number.split(".")[1]
    else:
        decimal_part = ""

    s = str(int_part)
    if len(s) > 3:
        last3 = s[-3:]
        rest = s[:-3]
        rest = ",".join(
            [
                rest[max(i - 2, 0):i]
                for i in range(len(rest), 0, -2)
            ][::-1]
        )
        formatted = rest + "," + last3
    else:
        formatted = s

    if decimals > 0:
        return f"{sign}{formatted}.{decimal_part}"
    return f"{sign}{formatted}"

# ---------------------------------------------------
# Reusable Table Style (Blue Theme matching roas_conversion_dash)
# ---------------------------------------------------
def create_sme_comparison_table(df, table_title):
    weight_tables = [
        'Gold',
        'Diamond',
        'Silver'
    ]

    format_cols = [
        'LYM',
        'LY_MTD',
        'TY_MTD',
        'V_LYM',
        'V_Diff',
        'V_LY_MTD',
        'V_TY_MTD',
        'Target'
    ]

    count_cols = [
        'No_LYM',
        'No_LY_MTD',
        'No_TY_MTD',
        'No_Diff'
    ]

    # Format values
    formatted_df = df.copy()
    for col in formatted_df.columns:
        if col in format_cols or col.endswith('(achieved)'):
            if table_title in weight_tables:
                formatted_df[col] = formatted_df[col].apply(lambda x: indian_format(x, 2))
            else:
                formatted_df[col] = formatted_df[col].apply(lambda x: indian_format(x, 0))
        elif col in count_cols:
            formatted_df[col] = formatted_df[col].apply(lambda x: indian_format(x, 0))

    if 'Pct_Diff' in formatted_df.columns:
        formatted_df['Pct_Diff'] = formatted_df['Pct_Diff'].apply(lambda x: f"{x:.2f}%")

    if 'ach %' in formatted_df.columns:
        formatted_df['ach %'] = formatted_df['ach %'].apply(lambda x: f"{x:.2f}%")

    return dbc.Card(
        [
            dbc.CardHeader(
                html.H5(
                    table_title,
                    className='fw-bold mb-0',
                    style={'textAlign': 'left', 'color': '#0F172A', 'fontFamily': 'Outfit'},
                ),
                style={'backgroundColor': '#F8FAFC', 'borderBottom': '1px solid #E2E8F0'},
            ),
            dbc.CardBody(
                [
                    dash_table.DataTable(
                        data=formatted_df.to_dict('records'),
                        columns=[
                            {
                                'name': col,
                                'id': col
                            }
                            for col in formatted_df.columns
                            if col not in [
                                'raw_v_diff',
                                'raw_pct_diff',
                                'raw_ach_pct'
                            ]
                        ],
                        fixed_rows={'headers': True},
                        fixed_columns={'headers': True, 'data': 1},
                        page_action='none',
                        style_as_list_view=True,
                        style_table={
                            'overflowX': 'auto',
                            'overflowY': 'auto',
                            'maxHeight': '500px',
                            'width': '100%',
                        },
                        style_cell={
                            'textAlign': 'center',
                            'padding': '10px 14px',
                            'fontSize': '12px',
                            'fontFamily': "'Outfit', 'Inter', sans-serif",
                            'minWidth': '120px',
                            'width': '150px',
                            'maxWidth': '200px',
                            'whiteSpace': 'normal',
                            'height': 'auto',
                            'backgroundColor': '#FFFFFF',
                            'color': '#334155',
                            'borderBottom': '1px solid #F1F5F9',
                        },
                        style_header={
                            'fontWeight': 'bold',
                            'backgroundColor': '#1E293B',
                            'color': '#F8FAFC',
                            'fontSize': '12px',
                            'textAlign': 'center',
                            'fontFamily': "'Outfit', sans-serif",
                            'border': '1px solid #CBD5E1',
                            'padding': '12px 14px',
                        },
                        style_data_conditional=[
                            {
                                'if': {'column_id': 'Manager'},
                                'fontWeight': 'bold',
                                'backgroundColor': '#F8FAFC'
                            },
                            {
                                'if': {
                                    'filter_query': '{raw_pct_diff} > 0',
                                    'column_id': 'Pct_Diff'
                                },
                                'backgroundColor': '#d1e7dd',
                                'color': '#0f5132',
                                'fontWeight': 'bold'
                            },
                            {
                                'if': {
                                    'filter_query': '{raw_pct_diff} < 0',
                                    'column_id': 'Pct_Diff'
                                },
                                'backgroundColor': '#f8d7da',
                                'color': '#842029',
                                'fontWeight': 'bold'
                            },
                            {
                                'if': {
                                    'filter_query': '{raw_ach_pct} >= 100',
                                    'column_id': 'ach %'
                                },
                                'backgroundColor': '#d1e7dd',
                                'color': '#0f5132',
                                'fontWeight': 'bold'
                            },
                            {
                                'if': {
                                    'filter_query': '{raw_ach_pct} < 100',
                                    'column_id': 'ach %'
                                },
                                'backgroundColor': '#f8d7da',
                                'color': '#842029',
                                'fontWeight': 'bold'
                            },
                            {
                                'if': {
                                    'filter_query': '{Manager} eq "TOTAL"'
                                },
                                'fontWeight': 'bold',
                                'backgroundColor': '#FAF2DF',
                                'color': '#1C1B19'
                            }
                        ],
                    )
                ],
                style={'padding': '6px', 'backgroundColor': 'white'}
            )
        ],
        className="inv-blue-card mb-4"
    )

# ---------------------------------------------------
# Ratio Metrics (ATV, ASP, UPT) Table Generator
# ---------------------------------------------------
def create_ratio_metrics_table(nsv_table, invoice_table, tag_table):
    rows = []
    
    for manager in nsv_table['Manager'].unique():
        nsv_row = nsv_table[nsv_table['Manager'] == manager].iloc[0]
        inv_row = invoice_table[invoice_table['Manager'] == manager].iloc[0]
        tag_row = tag_table[tag_table['Manager'] == manager].iloc[0]
        
        nsv_val = float(nsv_row['TY_MTD'])
        inv_val = float(inv_row['TY_MTD'])
        tag_val = float(tag_row['TY_MTD'])
        
        atv = nsv_val / inv_val if inv_val > 0 else 0.0
        asp = nsv_val / tag_val if tag_val > 0 else 0.0
        upt = tag_val / inv_val if inv_val > 0 else 0.0
        
        rows.append({
            'Manager': manager,
            'ATV': atv,
            'ASP': asp,
            'UPT': upt
        })
        
    df = pd.DataFrame(rows)
    formatted_df = df.copy()
    formatted_df['ATV'] = formatted_df['ATV'].apply(lambda x: indian_format(x, 2))
    formatted_df['ASP'] = formatted_df['ASP'].apply(lambda x: indian_format(x, 2))
    formatted_df['UPT'] = formatted_df['UPT'].apply(lambda x: indian_format(x, 2))
    
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H5(
                    "Average Transaction Metrics (ATV | ASP | UPT) - Current Period",
                    className='fw-bold mb-0',
                    style={'textAlign': 'left', 'color': '#0F172A', 'fontFamily': 'Outfit'},
                ),
                style={'backgroundColor': '#F8FAFC', 'borderBottom': '1px solid #E2E8F0'},
            ),
            dbc.CardBody(
                [
                    dash_table.DataTable(
                        data=formatted_df.to_dict('records'),
                        columns=[
                            {'name': col, 'id': col}
                            for col in formatted_df.columns
                        ],
                        fixed_rows={'headers': True},
                        fixed_columns={'headers': True, 'data': 1},
                        page_action='none',
                        style_as_list_view=True,
                        style_table={
                            'overflowX': 'auto',
                            'overflowY': 'auto',
                            'maxHeight': '500px',
                            'width': '100%',
                        },
                        style_cell={
                            'textAlign': 'center',
                            'padding': '10px 14px',
                            'fontSize': '12px',
                            'fontFamily': "'Outfit', 'Inter', sans-serif",
                            'minWidth': '120px',
                            'width': '150px',
                            'maxWidth': '200px',
                            'whiteSpace': 'normal',
                            'height': 'auto',
                            'backgroundColor': '#FFFFFF',
                            'color': '#334155',
                            'borderBottom': '1px solid #F1F5F9',
                        },
                        style_header={
                            'fontWeight': 'bold',
                            'backgroundColor': '#1E293B',
                            'color': '#F8FAFC',
                            'fontSize': '12px',
                            'textAlign': 'center',
                            'fontFamily': "'Outfit', sans-serif",
                            'border': '1px solid #CBD5E1',
                            'padding': '12px 14px',
                        },
                        style_data_conditional=[
                            {
                                'if': {'column_id': 'Manager'},
                                'fontWeight': 'bold',
                                'backgroundColor': '#F8FAFC'
                            },
                            {
                                'if': {
                                    'filter_query': '{Manager} eq "TOTAL"'
                                },
                                'fontWeight': 'bold',
                                'backgroundColor': '#FAF2DF',
                                'color': '#1C1B19'
                            }
                        ],
                    )
                ],
                style={'padding': '6px', 'backgroundColor': 'white'}
            )
        ],
        className="inv-blue-card mb-4"
    )

# ---------------------------------------------------
# KPI Card (Blue Theme accents)
# ---------------------------------------------------
def create_kpi_card(title, value_diff, pct_diff):
    raw_value = value_diff
    
    if raw_value < 0:
        bg_color = '#f8d7da'     # rose pink
        border_color = '#f5c2c7'
        text_color = '#842029'    # dark red
        pct_color = '#842029'
        arrow = "▼"
    else:
        bg_color = '#d1e7dd'     # mint green
        border_color = '#badbcc'
        text_color = '#0f5132'    # dark forest green
        pct_color = '#0f5132'
        arrow = "▲"

    # Formatting values
    if title in ['Gold_g', 'Diamond_cts', 'Silver_g']:
        formatted_value = indian_format(value_diff, 2)
    else:
        formatted_value = indian_format(value_diff, 0)
        
    display_title = title.replace('_g', ' (g)').replace('_cts', ' (cts)').upper()

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    display_title,
                    style={
                        'fontWeight': '600',
                        'fontSize': '11px',
                        'color': '#6b7280',
                        'textTransform': 'uppercase',
                        'letterSpacing': '0.05em',
                        'marginBottom': '4px',
                        'textAlign': 'center'
                    }
                ),
                html.Div(
                    [
                        html.Span(arrow + " ", style={'fontSize': '12px', 'marginRight': '2px'}),
                        html.Span(f"{pct_diff:.2f}%")
                    ],
                    style={
                        'fontSize': '20px',
                        'fontWeight': '700',
                        'color': pct_color,
                        'textAlign': 'center',
                        'lineHeight': '24px'
                    }
                ),
                html.Div(
                    f"Diff: {formatted_value}",
                    style={
                        'fontSize': '12px',
                        'fontWeight': '500',
                        'textAlign': 'center',
                        'color': text_color,
                        'marginTop': '4px'
                    }
                )
            ]
        ),
        style={
            'borderRadius': '10px',
            'border': f'1px solid {border_color}',
            'backgroundColor': bg_color,
            'boxShadow': '0 2px 8px rgba(15, 23, 42, 0.05)',
            'height': '100%'
        }
    )

# ---------------------------------------------------
# Layout Design
# ---------------------------------------------------
layout = html.Div(
    className='inv-premium-page-blue',
    children=dbc.Container(
        [
            # Top Header Row
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.A(
                                dbc.Button(
                                    "← Sales Department",
                                    id="sme-back-btn",
                                    className='inv-btn-blue-dark px-3 py-1',
                                    size='sm'
                                ),
                                href="/sales",
                                style={'textDecoration': 'none'}
                            ),
                            html.H2(
                                "SME Performance Dashboard",
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
                                style={'color': '#475569', 'fontFamily': 'Outfit'}
                            ),
                            html.Div(
                                [
                                    dbc.Button(
                                        "Export Data",
                                        id="sme-export-btn",
                                        className="inv-btn-blue-dark px-3 py-1 shadow-sm me-2",
                                        size="sm"
                                    ),
                                    dbc.Button(
                                        "Enter",
                                        id="sme-enter-btn",
                                        className="inv-btn-blue px-3 py-1 shadow-sm",
                                        size="sm"
                                    )
                                ],
                                className="text-end"
                            ),
                            dcc.Download(id="sme-download")
                        ],
                        width=4
                    )
                ],
                className='mb-4 mt-2 align-items-end'
            ),

            # Filters Section
            dbc.Card(
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Date Range", className="fw-bold mb-1 small text-muted"),
                                    dcc.DatePickerRange(
                                        id='sme-date-picker',
                                        display_format='DD-MMM-YYYY',
                                        start_date=default_start_date,
                                        end_date=default_end_date,
                                        className="w-100"
                                    )
                                ],
                                xs=12, md=3,
                                className="mb-2 mb-md-0"
                            ),
                            dbc.Col(
                                [
                                    html.Label("Regional Manager", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='sme-rm-filter',
                                        options=rm_options,
                                        placeholder='Select RM'
                                    )
                                ],
                                xs=12, md=3,
                                className="mb-2 mb-md-0"
                            ),
                            dbc.Col(
                                [
                                    html.Label("Zone Manager", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='sme-zm-filter',
                                        options=zm_options,
                                        placeholder='Select ZM'
                                    )
                                ],
                                xs=12, md=3,
                                className="mb-2 mb-md-0"
                            ),
                            dbc.Col(
                                [
                                    html.Label("Comparison Mode", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='sme-comparison-mode',
                                        options=[
                                            {'label': 'All Stores', 'value': 'All'},
                                            {'label': 'Like-to-Like', 'value': 'Like-to-Like'}
                                        ],
                                        value='All',
                                        clearable=False
                                    )
                                ],
                                xs=12, md=3,
                                className="mb-2 mb-md-0"
                            )
                        ]
                    )
                ),
                className="inv-blue-card mb-4"
            ),

            # Tables Container
            dcc.Loading(
                children=[
                    html.Div(
                        id='sme-tables-container'
                    )
                ],
                type='default'
            )
        ],
        fluid=True
    )
)

# ---------------------------------------------------
# Back Button Dynamic Link Callback
# ---------------------------------------------------
@callback(
    [
        Output('sme-back-btn', 'href'),
        Output('sme-back-btn', 'children')
    ],
    Input('url', 'search')
)
def update_back_btn_link(search):
    if search and 'directors-hub' in search:
        return "/directors-hub", "← Directors Hub"
    return "/sales", "← Sales Department"

# ---------------------------------------------------
# Dropdown Options RLS Filtering Callbacks
# ---------------------------------------------------
@callback(
    Output('sme-rm-filter', 'options'),
    Input('sme-rm-filter', 'id')
)
def populate_sme_rm_options(_):
    allowed_locations = get_allowed_locations()
    if not allowed_locations:
        return []
    if 'ALL' in allowed_locations:
        rms = sorted(rm_zm_df['rm'].dropna().unique().tolist())
    else:
        rms = sorted(rm_zm_df[rm_zm_df['location'].isin(allowed_locations)]['rm'].dropna().unique().tolist())
    return [{'label': r, 'value': r} for r in rms]

@callback(
    Output('sme-zm-filter', 'options'),
    Input('sme-zm-filter', 'id')
)
def populate_sme_zm_options(_):
    allowed_locations = get_allowed_locations()
    if not allowed_locations:
        return []
    if 'ALL' in allowed_locations:
        zms = sorted(rm_zm_df['zm'].dropna().unique().tolist())
    else:
        zms = sorted(rm_zm_df[rm_zm_df['location'].isin(allowed_locations)]['zm'].dropna().unique().tolist())
    return [{'label': z, 'value': z} for z in zms]

# ---------------------------------------------------
# Like-to-Like Location Discovery Helper
# ---------------------------------------------------
def get_like_to_like_locations(sales_df, start_date, end_date):
    ly_start = pd.to_datetime(start_date) - pd.DateOffset(years=1)
    ly_end = pd.to_datetime(end_date) - pd.DateOffset(years=1)
    
    # Filter sales to last year date range
    ly_sales = sales_df[
        (sales_df['Invoice Date'] >= ly_start)
        &
        (sales_df['Invoice Date'] <= ly_end)
    ]
    
    # Group by location and sum NSV
    loc_nsv = ly_sales.groupby('Location Name')['Bom Line Amount'].sum()
    active_locs = loc_nsv[loc_nsv > 0].index.tolist()
    return active_locs

# ---------------------------------------------------
# Helper functions for manager calculations
# ---------------------------------------------------
def calculate_manager_comparison_tables(start_dt, end_dt, rm_filter, zm_filter, mode_filter, allowed_locations):
    # 1. Prepare comparison data
    prepared_data = prepare_comparison_data(start_dt, end_dt)
    
    # 2. Get location level tables
    loc_nsv = get_nsv_comparison(prepared_data)
    loc_gold = get_gold_comparison(prepared_data)
    loc_diamond = get_diamond_comparison(prepared_data)
    loc_silver = get_silver_comparison(prepared_data)
    loc_gemstone = get_gemstone_comparison(prepared_data)
    loc_mohor = get_mohor_comparison(prepared_data)
    loc_mc = get_mc_comparison(prepared_data)
    loc_scheme = get_scheme_comparison(prepared_data)
    loc_invoice = get_invoice_comparison(prepared_data)
    loc_tag = get_tag_comparison(prepared_data)
    
    # 3. Handle Like-to-Like filtering
    active_locs = None
    if mode_filter == 'Like-to-Like':
        active_locs = get_like_to_like_locations(merged_sales_df, start_dt, end_dt)
        
        # Filter all location tables
        loc_nsv = loc_nsv[loc_nsv['Location'].isin(active_locs) | (loc_nsv['Location'] == 'TOTAL')]
        loc_gold = loc_gold[loc_gold['Location'].isin(active_locs) | (loc_gold['Location'] == 'TOTAL')]
        loc_diamond = loc_diamond[loc_diamond['Location'].isin(active_locs) | (loc_diamond['Location'] == 'TOTAL')]
        loc_silver = loc_silver[loc_silver['Location'].isin(active_locs) | (loc_silver['Location'] == 'TOTAL')]
        loc_gemstone = loc_gemstone[loc_gemstone['Location'].isin(active_locs) | (loc_gemstone['Location'] == 'TOTAL')]
        loc_mohor = loc_mohor[loc_mohor['Location'].isin(active_locs) | (loc_mohor['Location'] == 'TOTAL')]
        loc_mc = loc_mc[loc_mc['Location'].isin(active_locs) | (loc_mc['Location'] == 'TOTAL')]
        loc_scheme = loc_scheme[loc_scheme['Location'].isin(active_locs) | (loc_scheme['Location'] == 'TOTAL')]
        loc_invoice = loc_invoice[loc_invoice['Location'].isin(active_locs) | (loc_invoice['Location'] == 'TOTAL')]
        loc_tag = loc_tag[loc_tag['Location'].isin(active_locs) | (loc_tag['Location'] == 'TOTAL')]
    
    # 4. Filter RM_ZM mapping based on RLS & Active locations
    if 'ALL' in allowed_locations:
        filtered_rz = rm_zm_df.copy()
    else:
        filtered_rz = rm_zm_df[rm_zm_df['location'].isin(allowed_locations)].copy()
        
    if active_locs is not None:
        filtered_rz = filtered_rz[filtered_rz['location'].isin(active_locs)]
        
    # 5. Filter & Aggregate Targets
    target_df = targets_df.copy()
    if 'ALL' not in allowed_locations:
        target_df = target_df[target_df['location'].isin(allowed_locations)]
    if active_locs is not None:
        target_df = target_df[target_df['location'].isin(active_locs)]
        
    from_month = pd.to_datetime(start_dt).replace(day=1)
    to_month = pd.to_datetime(end_dt).replace(day=1)
    target_df = target_df[(target_df['month'] >= from_month) & (target_df['month'] <= to_month)]
    
    ly_start_dt = start_dt - pd.DateOffset(years=1)
    ly_end_dt = end_dt - pd.DateOffset(years=1)
    ly_from_month = pd.to_datetime(ly_start_dt).replace(day=1)
    ly_to_month = pd.to_datetime(ly_end_dt).replace(day=1)
    ly_target_df = targets_df.copy()
    if 'ALL' not in allowed_locations:
        ly_target_df = ly_target_df[ly_target_df['location'].isin(allowed_locations)]
    if active_locs is not None:
        ly_target_df = ly_target_df[ly_target_df['location'].isin(active_locs)]
    ly_target_df = ly_target_df[(ly_target_df['month'] >= ly_from_month) & (ly_target_df['month'] <= ly_to_month)]
    
    # Group targets by RM and ZM for mapping
    # Merge targets with RM/ZM details
    t_df_merged = target_df.merge(rm_zm_df[['location', 'rm', 'zm']].drop_duplicates(), on='location', how='left')
    ly_t_df_merged = ly_target_df.merge(rm_zm_df[['location', 'rm', 'zm']].drop_duplicates(), on='location', how='left')
    
    rm_t_grp = t_df_merged.groupby('rm')[['nsv', 'gold_w', 'diamond_cts', 'silver_w', 'gemstone_nsv', 'mohor_nsv']].sum()
    rm_t_grp.index = rm_t_grp.index.map(lambda x: f"{x} (RM)")
    zm_t_grp = t_df_merged.groupby('zm')[['nsv', 'gold_w', 'diamond_cts', 'silver_w', 'gemstone_nsv', 'mohor_nsv']].sum()
    zm_t_grp.index = zm_t_grp.index.map(lambda x: f"{x} (ZM)")
    mgr_targets = pd.concat([rm_t_grp, zm_t_grp])
    
    ly_rm_t_grp = ly_t_df_merged.groupby('rm')[['nsv', 'gold_w', 'diamond_cts', 'silver_w', 'gemstone_nsv', 'mohor_nsv']].sum()
    ly_rm_t_grp.index = ly_rm_t_grp.index.map(lambda x: f"{x} (RM)")
    ly_zm_t_grp = ly_t_df_merged.groupby('zm')[['nsv', 'gold_w', 'diamond_cts', 'silver_w', 'gemstone_nsv', 'mohor_nsv']].sum()
    ly_zm_t_grp.index = ly_zm_t_grp.index.map(lambda x: f"{x} (ZM)")
    ly_mgr_targets = pd.concat([ly_rm_t_grp, ly_zm_t_grp])
    
    # Rank managers by NSV dynamically
    loc_nsv_clean = loc_nsv[loc_nsv['Location'] != 'TOTAL'].copy()
    nsv_merged = loc_nsv_clean.merge(filtered_rz, left_on='Location', right_on='location', how='inner')
    
    # Filter dropdowns
    if rm_filter:
        nsv_merged = nsv_merged[nsv_merged['rm'] == rm_filter]
    if zm_filter:
        nsv_merged = nsv_merged[nsv_merged['zm'] == zm_filter]
        
    # Group and sort RMs
    sorted_rms = []
    sorted_zms = []
    if not nsv_merged.empty:
        rm_nsv = nsv_merged.groupby('rm', as_index=False)['TY_MTD'].sum()
        rm_nsv = rm_nsv.sort_values(by='TY_MTD', ascending=False)
        sorted_rms = [f"{r} (RM)" for r in rm_nsv['rm'].dropna().unique()]
        
        # Group and sort ZMs
        zm_nsv = nsv_merged.groupby('zm', as_index=False)['TY_MTD'].sum()
        zm_nsv = zm_nsv.sort_values(by='TY_MTD', ascending=False)
        sorted_zms = [f"{z} (ZM)" for z in zm_nsv['zm'].dropna().unique()]
    
    sorted_managers = sorted_rms + sorted_zms
    
    if not sorted_managers:
        default_rms = sorted(filtered_rz['rm'].dropna().unique())
        default_zms = sorted(filtered_rz['zm'].dropna().unique())
        sorted_managers = [f"{r} (RM)" for r in default_rms] + [f"{z} (ZM)" for z in default_zms]
        
    # Generic aggregation function for comparison tables
    def aggregate_table(df, metric_name, target_col):
        df_clean = df[df['Location'] != 'TOTAL'].copy()
        merged = df_clean.merge(filtered_rz, left_on='Location', right_on='location', how='inner')
        
        if rm_filter:
            merged = merged[merged['rm'] == rm_filter]
        if zm_filter:
            merged = merged[merged['zm'] == zm_filter]
            
        exclude_cols = ['Code', 'Location', 'location', 'code', 'rm', 'zm', 'Pct_Diff', 'V_Diff', 'No_Diff', 'raw_v_diff', 'raw_pct_diff']
        cols_to_sum = [c for c in df.columns if c not in exclude_cols]
        
        if not merged.empty:
            rm_grp = merged.groupby('rm', as_index=False)[cols_to_sum].sum()
            rm_grp.rename(columns={'rm': 'Manager'}, inplace=True)
            rm_grp['Manager'] = rm_grp['Manager'].apply(lambda x: f"{x} (RM)")
            
            zm_grp = merged.groupby('zm', as_index=False)[cols_to_sum].sum()
            zm_grp.rename(columns={'zm': 'Manager'}, inplace=True)
            zm_grp['Manager'] = zm_grp['Manager'].apply(lambda x: f"{x} (ZM)")
            
            agg_df = pd.concat([rm_grp, zm_grp], ignore_index=True)
        else:
            agg_df = pd.DataFrame(columns=['Manager'] + cols_to_sum)
            
        present_mgrs = [m for m in sorted_managers if m in agg_df['Manager'].values]
        
        agg_df.set_index('Manager', inplace=True)
        agg_df = agg_df.reindex(present_mgrs)
        agg_df.reset_index(inplace=True)
        agg_df.fillna(0.0, inplace=True)
        
        # Differences
        if 'TY_MTD' in agg_df.columns and 'LY_MTD' in agg_df.columns:
            agg_df['V_Diff'] = agg_df['TY_MTD'] - agg_df['LY_MTD']
            
            def get_pct(row):
                ly = row['LY_MTD']
                if ly == 0:
                    return 0.0
                return (row['V_Diff'] / ly) * 100
                
            agg_df['Pct_Diff'] = agg_df.apply(get_pct, axis=1)
            agg_df['raw_v_diff'] = agg_df['V_Diff']
            agg_df['raw_pct_diff'] = agg_df['Pct_Diff']
            
        if 'No_TY_MTD' in agg_df.columns and 'No_LY_MTD' in agg_df.columns:
            agg_df['No_Diff'] = agg_df['No_TY_MTD'] - agg_df['No_LY_MTD']
            
        if 'V_TY_MTD' in agg_df.columns and 'V_LY_MTD' in agg_df.columns:
            agg_df['V_Diff'] = agg_df['V_TY_MTD'] - agg_df['V_LY_MTD']
            
        # Target, Achieved, ach % Injection
        # Check if metric belongs to LY table (has LY_ prefix in title)
        is_ly = metric_name.startswith('LY_')
        active_mgr_targets = ly_mgr_targets if is_ly else mgr_targets
        active_target_df = ly_target_df if is_ly else target_df
        
        if target_col and not active_mgr_targets.empty and target_col in active_mgr_targets.columns:
            agg_df['Target'] = agg_df['Manager'].map(lambda m: active_mgr_targets.loc[m, target_col] if m in active_mgr_targets.index else 0.0)
        else:
            agg_df['Target'] = 0.0
            
        achieved_col_name = f"{metric_name} (achieved)"
        if 'TY_MTD' in agg_df.columns:
            agg_df[achieved_col_name] = agg_df['TY_MTD']
        elif 'V_TY_MTD' in agg_df.columns:
            agg_df[achieved_col_name] = agg_df['V_TY_MTD']
        else:
            agg_df[achieved_col_name] = 0.0
            
        def get_ach_pct(row):
            tgt = row['Target']
            ach = row[achieved_col_name]
            if tgt <= 0:
                return 0.0
            return (ach / tgt) * 100
            
        agg_df['ach %'] = agg_df.apply(get_ach_pct, axis=1)
        agg_df['raw_ach_pct'] = agg_df['ach %']
        
        # Calculate TOTAL
        total_data = {'Manager': 'TOTAL'}
        for col in cols_to_sum:
            total_data[col] = agg_df[col].sum()
            
        if 'TY_MTD' in agg_df.columns and 'LY_MTD' in agg_df.columns:
            total_v_diff = total_data['TY_MTD'] - total_data['LY_MTD']
            total_pct_diff = 0.0
            if total_data['LY_MTD'] != 0:
                total_pct_diff = (total_v_diff / total_data['LY_MTD']) * 100
            total_data['V_Diff'] = total_v_diff
            total_data['Pct_Diff'] = total_pct_diff
            total_data['raw_v_diff'] = total_v_diff
            total_data['raw_pct_diff'] = total_pct_diff
            
        if 'No_TY_MTD' in agg_df.columns and 'No_LY_MTD' in agg_df.columns:
            total_data['No_Diff'] = total_data['No_TY_MTD'] - total_data['No_LY_MTD']
            
        if 'V_TY_MTD' in agg_df.columns and 'V_LY_MTD' in agg_df.columns:
            total_data['V_Diff'] = total_data['V_TY_MTD'] - total_data['V_LY_MTD']
            
        if target_col and not active_target_df.empty and target_col in active_target_df.columns:
            total_data['Target'] = active_target_df[target_col].sum()
        else:
            total_data['Target'] = 0.0
            
        total_data[achieved_col_name] = total_data['TY_MTD'] if 'TY_MTD' in total_data else (total_data['V_TY_MTD'] if 'V_TY_MTD' in total_data else 0.0)
        
        if total_data['Target'] > 0:
            total_data['ach %'] = (total_data[achieved_col_name] / total_data['Target']) * 100
        else:
            total_data['ach %'] = 0.0
            
        total_data['raw_ach_pct'] = total_data['ach %']
        
        total_row = pd.DataFrame([total_data])
        final_df = pd.concat([agg_df, total_row], ignore_index=True)
        
        # Order columns placing Manager, Target, Achieved, ach % first
        cols = ['Manager', 'Target', achieved_col_name, 'ach %'] + [c for c in final_df.columns if c not in ['Manager', 'Target', achieved_col_name, 'ach %']]
        final_df = final_df[cols]
        return final_df

    # Aggregate all tables with target column mappings
    nsv_agg = aggregate_table(loc_nsv, "NSV", "nsv")
    gold_agg = aggregate_table(loc_gold, "Gold", "gold_w")
    diamond_agg = aggregate_table(loc_diamond, "Diamond", "diamond_cts")
    silver_agg = aggregate_table(loc_silver, "Silver", "silver_w")
    gemstone_agg = aggregate_table(loc_gemstone, "Gemstone", "gemstone_nsv")
    mohor_agg = aggregate_table(loc_mohor, "Mohor", "mohor_nsv")
    mc_agg = aggregate_table(loc_mc, "Making Charge", None)
    scheme_agg = aggregate_table(loc_scheme, "Scheme", None)
    invoice_agg = aggregate_table(loc_invoice, "Invoices", None)
    tag_agg = aggregate_table(loc_tag, "Tags", None)
    
    return (
        nsv_agg, gold_agg, diamond_agg, silver_agg, gemstone_agg,
        mohor_agg, mc_agg, scheme_agg, invoice_agg, tag_agg
    )

# ---------------------------------------------------
# Primary Enter Callback (Datatables only)
# ---------------------------------------------------
@callback(
    Output('sme-tables-container', 'children'),
    [
        Input('sme-enter-btn', 'n_clicks'),
        Input('url', 'pathname')
    ],
    [
        State('sme-date-picker', 'start_date'),
        State('sme-date-picker', 'end_date'),
        State('sme-rm-filter', 'value'),
        State('sme-zm-filter', 'value'),
        State('sme-comparison-mode', 'value')
    ]
)
def update_sme_dashboard(n_clicks, pathname, start_date, end_date, rm, zm, comp_mode):
    if pathname != '/sme-performance':
        return no_update
        
    start_dt = pd.to_datetime(start_date) if start_date else pd.to_datetime(default_start_date)
    end_dt = pd.to_datetime(end_date) if end_date else pd.to_datetime(default_end_date)
    
    allowed_locations = get_allowed_locations()
    if not allowed_locations:
        return html.Div("No location access authorized.", className="text-center text-muted fw-bold py-4")
        
    # Get aggregated tables
    (
        nsv_table, gold_table, diamond_table, silver_table, gemstone_table,
        mohor_table, mc_table, scheme_table, invoice_table, tag_table
    ) = calculate_manager_comparison_tables(start_dt, end_dt, rm, zm, comp_mode, allowed_locations)
    
    # Drop TOTAL row from tables to satisfy "remove total rows"
    nsv_table = nsv_table[nsv_table['Manager'] != 'TOTAL']
    gold_table = gold_table[gold_table['Manager'] != 'TOTAL']
    diamond_table = diamond_table[diamond_table['Manager'] != 'TOTAL']
    silver_table = silver_table[silver_table['Manager'] != 'TOTAL']
    gemstone_table = gemstone_table[gemstone_table['Manager'] != 'TOTAL']
    mohor_table = mohor_table[mohor_table['Manager'] != 'TOTAL']
    mc_table = mc_table[mc_table['Manager'] != 'TOTAL']
    scheme_table = scheme_table[scheme_table['Manager'] != 'TOTAL']
    invoice_table = invoice_table[invoice_table['Manager'] != 'TOTAL']
    tag_table = tag_table[tag_table['Manager'] != 'TOTAL']
    
    # Ratio metrics table
    ratio_table = create_ratio_metrics_table(nsv_table, invoice_table, tag_table)
    
    # Tables Layout
    tables_layout = [
        dbc.Row(
            [
                dbc.Col(create_sme_comparison_table(nsv_table, "NSV"), xs=12, lg=6),
                dbc.Col(create_sme_comparison_table(gold_table, "Gold"), xs=12, lg=6)
            ]
        ),
        dbc.Row(
            [
                dbc.Col(create_sme_comparison_table(diamond_table, "Diamond"), xs=12, lg=6),
                dbc.Col(create_sme_comparison_table(silver_table, "Silver"), xs=12, lg=6)
            ]
        ),
        dbc.Row(
            [
                dbc.Col(create_sme_comparison_table(gemstone_table, "Gemstone"), xs=12, lg=6),
                dbc.Col(create_sme_comparison_table(mohor_table, "Mohor"), xs=12, lg=6)
            ]
        ),
        dbc.Row(
            [
                dbc.Col(create_sme_comparison_table(mc_table, "Making Charge"), xs=12, lg=6),
                dbc.Col(create_sme_comparison_table(scheme_table, "SS Scheme"), xs=12, lg=6)
            ]
        ),
        dbc.Row(
            [
                dbc.Col(create_sme_comparison_table(invoice_table, "Invoices"), xs=12, lg=6),
                dbc.Col(create_sme_comparison_table(tag_table, "Tags"), xs=12, lg=6)
            ]
        ),
        dbc.Row(
            [
                dbc.Col(ratio_table, width=12)
            ]
        )
    ]
    
    return tables_layout

# ---------------------------------------------------
# Export Data Callback
# ---------------------------------------------------
@callback(
    Output("sme-download", "data"),
    Input("sme-export-btn", "n_clicks"),
    [
        State('sme-date-picker', 'start_date'),
        State('sme-date-picker', 'end_date'),
        State('sme-rm-filter', 'value'),
        State('sme-zm-filter', 'value'),
        State('sme-comparison-mode', 'value')
    ],
    prevent_initial_call=True
)
def export_sme_data(n_clicks, start_date, end_date, rm, zm, comp_mode):
    if not n_clicks:
        return no_update
        
    start_dt = pd.to_datetime(start_date) if start_date else pd.to_datetime(default_start_date)
    end_dt = pd.to_datetime(end_date) if end_date else pd.to_datetime(default_end_date)
    
    # Log Activity
    from backend.services.activity_logger import log_activity
    log_activity(
        session.get('email'),
        "SME Performance Dashboard",
        action="Export Data",
        filters={"start_date": str(start_dt.date()), "end_date": str(end_dt.date()), "rm": rm, "zm": zm, "mode": comp_mode}
    )
    
    allowed_locations = get_allowed_locations()
    if not allowed_locations:
        return no_update
        
    # Get aggregated tables
    (
        nsv_table, gold_table, diamond_table, silver_table, gemstone_table,
        mohor_table, mc_table, scheme_table, invoice_table, tag_table
    ) = calculate_manager_comparison_tables(start_dt, end_dt, rm, zm, comp_mode, allowed_locations)
    
    # Drop TOTAL row for export tables
    nsv_table_export = nsv_table[nsv_table['Manager'] != 'TOTAL']
    gold_table_export = gold_table[gold_table['Manager'] != 'TOTAL']
    diamond_table_export = diamond_table[diamond_table['Manager'] != 'TOTAL']
    silver_table_export = silver_table[silver_table['Manager'] != 'TOTAL']
    gemstone_table_export = gemstone_table[gemstone_table['Manager'] != 'TOTAL']
    mohor_table_export = mohor_table[mohor_table['Manager'] != 'TOTAL']
    mc_table_export = mc_table[mc_table['Manager'] != 'TOTAL']
    scheme_table_export = scheme_table[scheme_table['Manager'] != 'TOTAL']
    invoice_table_export = invoice_table[invoice_table['Manager'] != 'TOTAL']
    tag_table_export = tag_table[tag_table['Manager'] != 'TOTAL']
    
    # Calculate ratio metrics table
    ratio_rows = []
    for manager in nsv_table_export['Manager'].unique():
        nsv_val = float(nsv_table_export[nsv_table_export['Manager'] == manager].iloc[0]['TY_MTD'])
        inv_val = float(invoice_table_export[invoice_table_export['Manager'] == manager].iloc[0]['TY_MTD'])
        tag_val = float(tag_table_export[tag_table_export['Manager'] == manager].iloc[0]['TY_MTD'])
        
        atv = nsv_val / inv_val if inv_val > 0 else 0.0
        asp = nsv_val / tag_val if tag_val > 0 else 0.0
        upt = tag_val / inv_val if inv_val > 0 else 0.0
        
        ratio_rows.append({
            'Manager': manager,
            'ATV': atv,
            'ASP': asp,
            'UPT': upt
        })
    ratio_df = pd.DataFrame(ratio_rows)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        current_row = 0
        
        sheets = [
            ("NSV Table", nsv_table_export),
            ("Gold Table", gold_table_export),
            ("Diamond Table", diamond_table_export),
            ("Silver Table", silver_table_export),
            ("Gemstone Table", gemstone_table_export),
            ("Mohor Table", mohor_table_export),
            ("MC Table", mc_table_export),
            ("Scheme Table", scheme_table_export),
            ("Invoices Table", invoice_table_export),
            ("Tags Table", tag_table_export),
            ("Ratio Metrics Table (ATV|ASP|UPT)", ratio_df)
        ]
        
        for name, df in sheets:
            # Drop formatting columns for export if present
            export_df = df.drop(columns=['raw_v_diff', 'raw_pct_diff', 'raw_ach_pct'], errors='ignore')
            
            # Format and write
            pd.DataFrame({name: []}).to_excel(
                writer,
                sheet_name='SME Performance',
                startrow=current_row,
                index=False
            )
            
            export_df.to_excel(
                writer,
                sheet_name='SME Performance',
                startrow=current_row + 1,
                index=False
            )
            
            current_row += len(export_df) + 4
            
    output.seek(0)
    return dcc.send_bytes(
        output.getvalue(),
        f"sme_performance_export_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.xlsx"
    )
