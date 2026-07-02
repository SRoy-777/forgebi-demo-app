from dash import ( 
    Dash,
    html,
    dcc,
    dash_table,
    callback,
    Input,
    Output,
    State
)
import io
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime

from backend.services.sales.comparison import (
    prepare_comparison_data,
    get_nsv_comparison,
    get_gold_comparison,
    get_diamond_comparison,
    get_silver_comparison,
    get_gemstone_comparison,
    get_mohor_comparison,
    get_mc_comparison,
    get_scheme_comparison,
    get_invoice_comparison,
    get_tag_comparison
)

from backend.cache.data_cache import (
    merged_sales_df,
    rm_zm_df
)

# ---------------------------------------------------
# Filter Options
# ---------------------------------------------------

rm_options = [
    {
        'label': rm,
        'value': rm
    }
    for rm in sorted(
        rm_zm_df['rm']
        .dropna()
        .unique()
    )
]

zm_options = [
    {
        'label': zm,
        'value': zm
    }
    for zm in sorted(
        rm_zm_df['zm']
        .dropna()
        .unique()
    )
]

location_options = [
    {
        'label': location,
        'value': location
    }
    for location in sorted(
        rm_zm_df['location']
        .dropna()
        .unique()
    )
]

# ---------------------------------------------------
# Last Updated & Default Dates
# ---------------------------------------------------

last_updated = merged_sales_df[
    'Invoice Date'
].max()

last_updated_text = last_updated.strftime(
    "%d-%b-%Y %I:%M %p"
)

last_invoice_date = pd.to_datetime(last_updated)
default_end_date = last_invoice_date.date()
default_start_date = last_invoice_date.replace(day=1).date()

# ---------------------------------------------------
# Reusable Table Style (Beige Theme)
# ---------------------------------------------------
TABLE_STYLE = {
    'page_action': 'none',
    'fill_width': False,
    'fixed_rows': {'headers': True},
    'fixed_columns': {'headers': True, 'data': 1},
    'style_table': {
        'overflowX': 'auto',
        'overflowY': 'auto',
        'maxHeight': '500px',
        'width': '100%',
        'minWidth': '100%',
        'border': '1px solid #E3DFD5',
        'borderRadius': '8px'
    },
    'style_cell': {
        'textAlign': 'center',
        'padding': '6px 8px',
        'fontSize': '11px',
        'fontFamily': "'Outfit', 'Inter', sans-serif",
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
                'filter_query': '{No_Diff} > 0',
                'column_id': 'No_Diff'
            },
            'backgroundColor': '#d1e7dd',
            'color': '#0f5132',
            'fontWeight': 'bold'
        },
        {
            'if': {
                'filter_query': '{No_Diff} < 0',
                'column_id': 'No_Diff'
            },
            'backgroundColor': '#f8d7da',
            'color': '#842029',
            'fontWeight': 'bold'
        },
        {
            'if': {
                'filter_query': '{Location} = "TOTAL"'
            },
            'fontWeight': 'bold',
            'backgroundColor': '#FAF2DF',
            'color': '#1C1B19'
        }
    ],
}

# ---------------------------------------------------
# Layout
# ---------------------------------------------------

layout = html.Div(
    className='inv-premium-page',
    children=dbc.Container(
        [
            # ---------------------------------------------------
            # Header Row
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
                                "Last Year Vs This Year Analysis",
                                className="fw-bold mt-3 mb-1"
                            )
                        ],
                        width=8
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                f"Last Updated : {last_updated.strftime('%d-%b-%Y')}",
                                className='text-end fw-bold mb-2',
                                style={'color': '#7F7C75'}
                            ),
                            html.Div(
                                [
                                    dcc.Loading(
                                        type="circle",
                                        children=[
                                            dbc.Button(
                                                "Export Data",
                                                id="export-comparison-btn",
                                                className="inv-btn-dark px-3 py-1 shadow-sm",
                                                size="sm"
                                            )
                                        ],
                                        style={'display': 'inline-block', 'marginRight': '8px'}
                                    ),
                                    dbc.Button(
                                        "Enter",
                                        id="comparison-enter-btn",
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
                id="download-comparison-data"
            ),

            # ---------------------------------------------------
            # Filters Section
            # ---------------------------------------------------
            dbc.Card(
                dbc.CardBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Label("Date Range", className="fw-bold mb-1 small text-muted"),
                                    dcc.DatePickerRange(
                                        id='comparison-date-picker',
                                        display_format='DD-MMM-YYYY',
                                        start_date=default_start_date,
                                        end_date=default_end_date,
                                        className="w-100"
                                    )
                                ],
                                width=3,
                                className="mb-2 mb-md-0"
                            ),
                            dbc.Col(
                                [
                                    html.Label("Regional Manager", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='comparison-rm-filter',
                                        options=rm_options,
                                        placeholder='Select RM'
                                    )
                                ],
                                width=3,
                                className="mb-2 mb-md-0"
                            ),
                            dbc.Col(
                                [
                                    html.Label("Zone Manager", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='comparison-zm-filter',
                                        options=zm_options,
                                        placeholder='Select ZM'
                                    )
                                ],
                                width=3,
                                className="mb-2 mb-md-0"
                            ),
                            dbc.Col(
                                [
                                    html.Label("Location", className="fw-bold mb-1 small text-muted"),
                                    dcc.Dropdown(
                                        id='comparison-location-filter',
                                        options=location_options,
                                        placeholder='Select Location'
                                    )
                                ],
                                width=3,
                                className="mb-2 mb-md-0"
                            )
                        ]
                    )
                ),
                className="inv-premium-card"
            ),

            # ---------------------------------------------------
            # Cards Container
            # ---------------------------------------------------
            dcc.Loading(
                children=[
                    html.Div(
                        id='comparison-cards-container'
                    )
                ],
                type='default'
            ),

            html.Br(),

            # ---------------------------------------------------
            # Tables Container
            # ---------------------------------------------------
            dcc.Loading(
                children=[
                    html.Div(
                        id='comparison-tables-container'
                    )
                ],
                type='default'
            )
        ],
        fluid=True
    )
)

# ---------------------------------------------------
# Indian Number Format
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
# KPI Card
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
            'boxShadow': '0 2px 8px rgba(28, 27, 25, 0.02)',
            'height': '100%'
        }
    )

# ---------------------------------------------------
# Reusable Table
# ---------------------------------------------------

def create_comparison_table(df, table_title):
    monetary_tables = [
        'NSV',
        'Gemstone',
        'Mohor',
        'Making Charge',
        'Invoices',
        'Tags'
    ]

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
        'V_TY_MTD'
    ]

    for col in format_cols:
        if col in df.columns:
            if table_title in weight_tables:
                df[col] = df[col].apply(lambda x: indian_format(x, 2))
            else:
                df[col] = df[col].apply(lambda x: indian_format(x, 0))

    count_cols = [
        'No_LYM',
        'No_LY_MTD',
        'No_TY_MTD',
        'No_Diff'
    ]

    for col in count_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: indian_format(x, 0))

    if 'Pct_Diff' in df.columns:
        df['Pct_Diff'] = df['Pct_Diff'].apply(lambda x: f"{x:.2f}%")

    return dbc.Card(
        [
            dbc.CardHeader(
                table_title,
                style={
                    'fontWeight': '700',
                    'fontSize': '14px',
                    'color': '#1C1B19',
                    'backgroundColor': '#FAF9F6',
                    'borderBottom': '1px solid #E3DFD5',
                    'borderTopLeftRadius': '12px',
                    'borderTopRightRadius': '12px',
                    'padding': '10px 16px'
                }
            ),
            dbc.CardBody(
                [
                    dash_table.DataTable(
                        data=df.to_dict('records'),
                        columns=[
                            {
                                'name': col,
                                'id': col
                            }
                            for col in df.columns
                            if col not in [
                                'raw_v_diff',
                                'raw_pct_diff'
                            ]
                        ],
                        **TABLE_STYLE
                    )
                ],
                style={
                    'padding': '8px',
                    'backgroundColor': 'white'
                }
            )
        ],
        className="inv-premium-card"
    )

# ---------------------------------------------------
# Main Callback
# ---------------------------------------------------

@callback(
    [
        Output('comparison-cards-container', 'children'),
        Output('comparison-tables-container', 'children')
    ],
    [
        Input('comparison-enter-btn', 'n_clicks'),
        Input('url', 'pathname')
    ],
    [
        State('comparison-date-picker', 'start_date'),
        State('comparison-date-picker', 'end_date'),
        State('comparison-rm-filter', 'value'),
        State('comparison-zm-filter', 'value'),
        State('comparison-location-filter', 'value')
    ]
)
def update_comparison_dashboard(
    n_clicks,
    pathname,
    start_date,
    end_date,
    rm,
    zm,
    location
):
    # Determine date range defaults robustly
    start_dt = pd.to_datetime(start_date) if start_date else pd.to_datetime(default_start_date)
    end_dt = pd.to_datetime(end_date) if end_date else pd.to_datetime(default_end_date)

    # ---------------------------------------------------
    # Prepare Data
    # ---------------------------------------------------

    prepared_data = prepare_comparison_data(
        start_dt,
        end_dt,
        rm,
        zm,
        location
    )

    # ---------------------------------------------------
    # Tables
    # ---------------------------------------------------

    nsv_table = get_nsv_comparison(prepared_data)
    gold_table = get_gold_comparison(prepared_data)
    diamond_table = get_diamond_comparison(prepared_data)
    silver_table = get_silver_comparison(prepared_data)
    gemstone_table = get_gemstone_comparison(prepared_data)
    mohor_table = get_mohor_comparison(prepared_data)
    mc_table = get_mc_comparison(prepared_data)
    scheme_table = get_scheme_comparison(prepared_data)
    invoice_table = get_invoice_comparison(prepared_data)
    tag_table = get_tag_comparison(prepared_data)

    # ---------------------------------------------------
    # Total Rows For Cards
    # ---------------------------------------------------

    nsv_total = nsv_table.iloc[-1]
    gold_total = gold_table.iloc[-1]
    diamond_total = diamond_table.iloc[-1]
    silver_total = silver_table.iloc[-1]
    gemstone_total = gemstone_table.iloc[-1]
    mohor_total = mohor_table.iloc[-1]
    mc_total = mc_table.iloc[-1]
    invoice_total = invoice_table.iloc[-1]
    tag_total = tag_table.iloc[-1]

    cards = dbc.Row(
        [
            dbc.Col(
                create_kpi_card(
                    "NSV",
                    nsv_total['V_Diff'],
                    nsv_total['Pct_Diff']
                ),
                style={'flex': '1', 'padding': '4px'}
            ),
            dbc.Col(
                create_kpi_card(
                    "Gold_g",
                    gold_total['V_Diff'],
                    gold_total['Pct_Diff']
                ),
                style={'flex': '1', 'padding': '4px'}
            ),
            dbc.Col(
                create_kpi_card(
                    "Diamond_cts",
                    diamond_total['V_Diff'],
                    diamond_total['Pct_Diff']
                ),
                style={'flex': '1', 'padding': '4px'}
            ),
            dbc.Col(
                create_kpi_card(
                    "Silver_g",
                    silver_total['V_Diff'],
                    silver_total['Pct_Diff']
                ),
                style={'flex': '1', 'padding': '4px'}
            ),
            dbc.Col(
                create_kpi_card(
                    "Mohor",
                    mohor_total['V_Diff'],
                    mohor_total['Pct_Diff']
                ),
                style={'flex': '1', 'padding': '4px'}
            ),
            dbc.Col(
                create_kpi_card(
                    "Gemstone",
                    gemstone_total['V_Diff'],
                    gemstone_total['Pct_Diff']
                ),
                style={'flex': '1', 'padding': '4px'}
            ),
            dbc.Col(
                create_kpi_card(
                    "MC",
                    mc_total['V_Diff'],
                    mc_total['Pct_Diff']
                ),
                style={'flex': '1', 'padding': '4px'}
            ),
            dbc.Col(
                create_kpi_card(
                    "Invoices",
                    invoice_total['V_Diff'],
                    invoice_total['Pct_Diff']
                ),
                style={'flex': '1', 'padding': '4px'}
            ),
            dbc.Col(
                create_kpi_card(
                    "Tags",
                    tag_total['V_Diff'],
                    tag_total['Pct_Diff']
                ),
                style={'flex': '1', 'padding': '4px'}
            )
        ],
        className="mb-3 g-2"
    )

    # ---------------------------------------------------
    # Tables Layout
    # ---------------------------------------------------

    tables = [
        dbc.Row(
            [
                dbc.Col(
                    create_comparison_table(nsv_table, "NSV"),
                    width=6
                ),
                dbc.Col(
                    create_comparison_table(gold_table, "Gold"),
                    width=6
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    create_comparison_table(diamond_table, "Diamond"),
                    width=6
                ),
                dbc.Col(
                    create_comparison_table(silver_table, "Silver"),
                    width=6
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    create_comparison_table(gemstone_table, "Gemstone"),
                    width=6
                ),
                dbc.Col(
                    create_comparison_table(mohor_table, "Mohor"),
                    width=6
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    create_comparison_table(mc_table, "Making Charge"),
                    width=6
                ),
                dbc.Col(
                    create_comparison_table(scheme_table, "SS Scheme"),
                    width=6
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    create_comparison_table(invoice_table, "Invoices"),
                    width=6
                ),
                dbc.Col(
                    create_comparison_table(tag_table, "Tags"),
                    width=6
                )
            ]
        )
    ]

    return cards, tables

# ---------------------------------------------------
# Export Callback
# ---------------------------------------------------

@callback(
    Output("download-comparison-data", "data"),
    Input("export-comparison-btn", "n_clicks"),
    State('comparison-date-picker', 'start_date'),
    State('comparison-date-picker', 'end_date'),
    State('comparison-rm-filter', 'value'),
    State('comparison-zm-filter', 'value'),
    State('comparison-location-filter', 'value'),
    prevent_initial_call=True
)
def export_comparison_data(
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
        "Comparison Dashboard",
        action="Export Data",
        filters={"start_date": start_date, "end_date": end_date, "rm": rm, "zm": zm, "location": location}
    )

    prepared_data = prepare_comparison_data(
        start_date,
        end_date,
        rm,
        zm,
        location
    )

    nsv_table = get_nsv_comparison(prepared_data).iloc[:-1]
    gold_table = get_gold_comparison(prepared_data).iloc[:-1]
    diamond_table = get_diamond_comparison(prepared_data).iloc[:-1]
    silver_table = get_silver_comparison(prepared_data).iloc[:-1]
    gemstone_table = get_gemstone_comparison(prepared_data).iloc[:-1]
    mohor_table = get_mohor_comparison(prepared_data).iloc[:-1]
    mc_table = get_mc_comparison(prepared_data).iloc[:-1]
    scheme_table = get_scheme_comparison(prepared_data).iloc[:-1]
    invoice_table = get_invoice_comparison(prepared_data).iloc[:-1]
    tag_table = get_tag_comparison(prepared_data).iloc[:-1]

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        current_row = 0

        tables = [
            ("NSV", nsv_table),
            ("Gold", gold_table),
            ("Diamond", diamond_table),
            ("Silver", silver_table),
            ("Gemstone", gemstone_table),
            ("Mohor", mohor_table),
            ("MC", mc_table),
            ("Scheme", scheme_table),
            ("Invoices", invoice_table),
            ("Tags", tag_table)
        ]

        for table_name, df in tables:
            df = df.drop(
                columns=[
                    'raw_v_diff',
                    'raw_pct_diff'
                ],
                errors='ignore'
            )

            pd.DataFrame({table_name: []}).to_excel(
                writer,
                sheet_name='Comparison Dashboard',
                startrow=current_row,
                index=False
            )

            df.to_excel(
                writer,
                sheet_name='Comparison Dashboard',
                startrow=current_row + 1,
                index=False
            )

            current_row += len(df) + 4

    output.seek(0)

    return dcc.send_bytes(
        output.getvalue(),
        "comparison_dashboard_export.xlsx"
    )

# ---------------------------------------------------
# Dynamic Location Dropdown Options RLS
# ---------------------------------------------------

@callback(
    Output('comparison-location-filter', 'options'),
    Input('comparison-location-filter', 'id')
)
def populate_comparison_location_filter_options(_):
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
