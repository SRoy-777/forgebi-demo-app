from dash import (
    html,
    dcc,
    dash_table,
    callback,
    Input,
    Output,
    State,
)

import pandas as pd
import dash_bootstrap_components as dbc

from backend.cache.data_cache import (
    merged_sales_df,
    rm_zm_df,
)

from backend.services.directors_hub.company_snapshot_service import (
    generate_company_snapshot_dashboard_data,
    generate_export_dataframe,
)


# ---------------------------------------------------
# Indian Formatting
# ---------------------------------------------------

def indian_format(value, decimals=0):

    try:
        value = float(value)
    except Exception:
        return value

    if pd.isna(value):
        return ''

    negative = value < 0
    value = abs(value)

    # Format to fixed decimals first to handle rounding correctly
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


# ---------------------------------------------------
# Filter Options
# ---------------------------------------------------

location_options = sorted(
    rm_zm_df['location'].dropna().unique()
)

rm_options = sorted(
    rm_zm_df['rm'].dropna().unique()
)

zm_options = sorted(
    rm_zm_df['zm'].dropna().unique()
)

latest_invoice_date = pd.to_datetime(
    merged_sales_df['Invoice Date'].max()
)

default_start_date = latest_invoice_date


# ---------------------------------------------------
# KPI Card
# ---------------------------------------------------

def create_kpi_card(title, value, background='#ffe082', is_percentage=False):

    title_lower = title.lower().strip() if title else ""
    two_decimal_kpis = {
        'gold gms sold',
        'diamond cts sold',
        'silver gms sold',
        'mohor gms sold',
        'gold 18k',
        'gold 22k',
        'gold 14k',
        'gold 24k'
    }

    if is_percentage:
        formatted_value = f"{indian_format(value, 2)}%"
    elif title_lower in two_decimal_kpis:
        formatted_value = indian_format(value, 2)
    else:
        formatted_value = indian_format(value, 0)

    return dbc.Card(

        dbc.CardBody([

            html.Div(
                title,
                style={
                    'fontSize': '12px',
                    'fontWeight': '700',
                    'textAlign': 'center',
                    'whiteSpace': 'nowrap',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'color': '#000000',
                }
            ),

            html.Div(
                formatted_value,
                style={
                    'fontSize': '18px',
                    'fontWeight': '800',
                    'textAlign': 'center',
                    'marginTop': '2px',
                    'color': '#FFFFFF',
                }
            ),

        ], style={'padding': '6px 4px', 'width': '100%'}),

        className='inv-kpi-card-gold'

    )



def build_kpi_section(title, kpi_items, background='#ffe082'):

    cards = []

    for kpi_name, value, is_pct in kpi_items:

        cards.append(

            dbc.Col(

                create_kpi_card(
                    title=kpi_name,
                    value=value,
                    background=background,
                    is_percentage=is_pct,
                ),

                xs=6,
                sm=4,
                md=2,
                lg=2,
                xl=2,
                className='mb-2',

            )

        )

    return html.Div([

        html.H5(
            title,
            className='fw-bold mb-2 mt-3',
            style={
                'color': '#1C1B19',
                'textAlign': 'left',
                'fontFamily': 'Outfit',
            }
        ),

        dbc.Row(cards, className='g-2'),

    ])


# ---------------------------------------------------
# Table Builder
# ---------------------------------------------------

def build_table(df, table_title):

    formatted_df = df.copy()

    qty_cols = ['Qty', 'Qty Sold']
    money_cols = ['NSV', 'Revenue']
    pct_cols = ['Contribution %']

    for col in formatted_df.columns:

        if col in ['Metal', 'Product Name', 'Sub Category']:
            continue

        formatted_df[col] = pd.to_numeric(
            formatted_df[col],
            errors='coerce',
        )

    formatted_df = formatted_df.astype(object)

    for idx in formatted_df.index:

        for col in formatted_df.columns:

            if col in ['Metal', 'Product Name', 'Sub Category']:
                continue

            value = formatted_df.loc[idx, col]

            if pd.isna(value) or value == '':
                formatted_df.loc[idx, col] = ''
                continue

            if col in qty_cols:
                formatted_df.loc[idx, col] = str(
                    indian_format(value, 2)
                )
            elif col in pct_cols:
                formatted_df.loc[idx, col] = f"{indian_format(value, 2)}%"
            elif col in money_cols:
                formatted_df.loc[idx, col] = str(
                    indian_format(value, 0)
                )
            else:
                formatted_df.loc[idx, col] = str(
                    indian_format(value, 0)
                )

    left_align_cols = [
        c for c in formatted_df.columns
        if c in ['Metal', 'Product Name', 'Sub Category']
    ]

    cell_conditional = [

        {
            'if': {'column_id': col},
            'textAlign': 'center',
            'fontWeight': 'bold' if col == 'Metal' else 'normal',
            'minWidth': '160px',
            'width': '160px',
            'maxWidth': '220px',
        }

        for col in left_align_cols

    ]

    return dbc.Card([

        dbc.CardHeader(

            html.H5(
                table_title,
                className='fw-bold mb-0',
                style={'textAlign': 'left', 'color': '#1C1B19', 'fontFamily': 'Outfit'},
            ),

            style={'backgroundColor': '#FAF9F6', 'borderBottom': '1px solid #E8DFCE'},

        ),

        dbc.CardBody(

            dash_table.DataTable(

                data=formatted_df.to_dict('records'),

                columns=[
                    {
                        'name': i,
                        'id': i,
                        'type': 'text',
                    }
                    for i in formatted_df.columns
                ],

                fixed_rows={'headers': True},
                page_action='none',
                style_as_list_view=True,

                style_table={
                    'overflowX': 'hidden',
                    'overflowY': 'auto',
                    'maxHeight': '650px',
                    'width': '100%',
                    'margin': '0 auto',
                },

                style_cell={
                    'textAlign': 'center',
                    'padding': '8px 10px',
                    'fontSize': '13px',
                    'fontFamily': "'Outfit', 'Inter', sans-serif",
                    'minWidth': '90px',
                    'width': '90px',
                    'maxWidth': '110px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'backgroundColor': '#FFFFFF',
                    'color': '#1C1B19',
                    'borderBottom': '1px solid #FAF6EE',
                },

                style_cell_conditional=cell_conditional,

                style_header={
                    'fontWeight': 'bold',
                    'backgroundColor': '#1C1B19',
                    'color': '#C5A059',
                    'fontSize': '13px',
                    'textAlign': 'center',
                    'fontFamily': "'Outfit', sans-serif",
                    'border': '1px solid #E8DFCE',
                },


            ),

            style={'padding': '6px'},

        ),

    ], className='inv-gold-card mb-4')


# ---------------------------------------------------
# Layout
# ---------------------------------------------------

layout = html.Div(
    className='inv-premium-page-gold',
    children=dbc.Container([

        dbc.Row([

            dbc.Col([
                html.A(
                    dbc.Button(
                        "← Directors Hub",
                        className='inv-btn-dark px-3 py-1',
                        size='sm'
                    ),
                    href="/directors-hub",
                    style={'textDecoration': 'none'}
                ),
                html.H2(
                    'Company Snapshot',
                    className='fw-bold mt-3 mb-1',
                    style={'fontFamily': 'Outfit'}
                ),
            ], width=8),

            dbc.Col([

                html.Div(
                    f"Last Updated : {latest_invoice_date.strftime('%d-%b-%Y')}",
                    className='text-end fw-bold mb-2',
                    style={'color': '#5C4D32', 'fontFamily': 'Outfit'},
                ),

                html.Div([
                    dbc.Button(
                        'Export Data',
                        id='cs-export-btn',
                        className='inv-btn-dark px-3 py-1 me-2 shadow-sm',
                        size='sm',
                    ),
                    dbc.Button(
                        'Enter',
                        id='cs-enter-btn',
                        className='inv-btn-gold px-3 py-1 shadow-sm',
                        size='sm',
                    ),
                ], className='text-end'),

                dcc.Download(id='cs-download'),

            ], width=4),

        ], className='mb-4 mt-2 align-items-end'),

        dbc.Card(

            dbc.CardBody([

                dbc.Row([

                    dbc.Col([
                        html.Label("Date Range", className="fw-bold mb-1 small text-muted"),
                        dcc.DatePickerRange(
                            id='cs-date-filter',
                            start_date=default_start_date,
                            end_date=latest_invoice_date,
                            display_format='DD-MMM-YYYY',
                            className='w-100',
                        ),
                    ], width=3),

                    dbc.Col([
                        html.Label("Location", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='cs-location-filter',
                            options=[
                                {'label': i, 'value': i}
                                for i in location_options
                            ],
                            multi=True,
                            placeholder='Select Location',
                        ),
                    ], width=3),

                    dbc.Col([
                        html.Label("Regional Manager", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='cs-rm-filter',
                            options=[
                                {'label': i, 'value': i}
                                for i in rm_options
                            ],
                            multi=True,
                            placeholder='Select RM',
                        ),
                    ], width=3),

                    dbc.Col([
                        html.Label("Zone Manager", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='cs-zm-filter',
                            options=[
                                {'label': i, 'value': i}
                                for i in zm_options
                            ],
                            multi=True,
                            placeholder='Select ZM',
                        ),
                    ], width=3),

                ]),

            ]),

            className='inv-gold-card mb-4',

        ),

        html.Div(id='cs-kpi-container'),

        dcc.Loading(
            html.Div(id='cs-table-container'),
            type='circle',
        ),

    ], fluid=True, style={'padding': '0px'})
)



# ---------------------------------------------------
# Main Callback
# ---------------------------------------------------

@callback(

    Output('cs-kpi-container', 'children'),
    Output('cs-table-container', 'children'),

    Input('cs-enter-btn', 'n_clicks'),

    State('cs-date-filter', 'start_date'),
    State('cs-date-filter', 'end_date'),
    State('cs-location-filter', 'value'),
    State('cs-rm-filter', 'value'),
    State('cs-zm-filter', 'value'),

)

def render_company_snapshot(
    n_clicks,
    start_date,
    end_date,
    locations,
    rms,
    zms,
):

    if not start_date or not end_date:
        return html.Div(), html.Div()

    try:

        data = generate_company_snapshot_dashboard_data(
            start_date=start_date,
            end_date=end_date,
            locations=locations,
            rms=rms,
            zms=zms,
        )

    except Exception as e:
        return html.Div(str(e)), html.Div()

    p1 = data['part1']
    part3 = data['part3']

    kpi_layout = html.Div([

        build_kpi_section(
            'Part 1 — Company KPIs',
            [
                ('Gross Sales (with tax)', p1['gross_sales'], False),
                ('Net Sales (NSV)', p1['net_sales'], False),
                ('Invoices Generated', p1['invoices'], False),
                ('ATV', p1['atv'], False),
                ('Conversion %', p1['conversion_pct'], True),
                ('Footfall', p1['footfall'], False),
                ('Gold Gms Sold', p1['gold_gms'], False),
                ('Diamond Cts Sold', p1['diamond_cts'], False),
                ('Silver Gms Sold', p1['silver_gms'], False),
                ('Mohor Gms Sold', p1['mohor_gms'], False),
                ('Mohor NSV Sold', p1['mohor_nsv'], False),
                ('Gemstone NSV Sold', p1['gemstone_nsv'], False),
            ],
        ),

        build_kpi_section(
            'Gold Purity Breakdown (Gms)',
            [
                ('Gold 18K', p1['purity_18k'], False),
                ('Gold 22K', p1['purity_22k'], False),
                ('Gold 14K', p1['purity_14k'], False),
                ('Gold 24K', p1['purity_24k'], False),
            ],
            background='#ffb74d',
        ),

    ])

    period_title = (
        f"Part 3 — Top 5 Products (Selected Period: "
        f"{data['start_date']} to {data['end_date']})"
    )

    full_months_title = (
        f"Part 3 — Top 5 Products (Full Months: "
        f"{part3['full_month_start']} to {part3['full_month_end']})"
    )

    table_layout = html.Div([

        build_table(
            data['part2'],
            'Part 2 — Metal Contribution on Total NSV',
        ),

        build_table(
            part3['period'],
            period_title,
        ),

        build_table(
            part3['full_months'],
            full_months_title,
        ),

    ])

    return kpi_layout, table_layout


# ---------------------------------------------------
# Export Callback
# ---------------------------------------------------

@callback(

    Output('cs-download', 'data'),

    Input('cs-export-btn', 'n_clicks'),

    State('cs-date-filter', 'start_date'),
    State('cs-date-filter', 'end_date'),
    State('cs-location-filter', 'value'),
    State('cs-rm-filter', 'value'),
    State('cs-zm-filter', 'value'),

    prevent_initial_call=True,

)

def export_company_snapshot(
    n_clicks,
    start_date,
    end_date,
    locations,
    rms,
    zms,
):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "Company Snapshot",
        action="Export Data",
        filters={"start_date": start_date, "end_date": end_date, "locations": locations, "rms": rms, "zms": zms}
    )


    export_df = generate_export_dataframe(
        start_date=start_date,
        end_date=end_date,
        locations=locations,
        rms=rms,
        zms=zms,
    )

    return dcc.send_data_frame(
        export_df.to_csv,
        'company_snapshot_export.csv',
        index=False,
    )


# ---------------------------------------------------
# Dynamic Location Dropdown Options RLS
# ---------------------------------------------------
from dash import callback, Output, Input

@callback(
    Output('cs-location-filter', 'options'),
    Input('cs-location-filter', 'id')
)
def populate_cs_location_filter_options(_):
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
