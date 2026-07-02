from dash import (
    html,
    dcc,
    dash_table,
    callback,
    Input,
    Output,
    State
)
import pandas as pd
import dash_bootstrap_components as dbc
from flask import session

from backend.cache.data_cache import (
    tag_sold_df,
    tag_received_df,
    tag_list_df,
    opt_gold_df
)

from backend.services.inventory.inventory_optimization import (
    prepare_inventory_data,
    generate_all_inventory_tables,
    COUNTER_ORDER
)

# ---------------------------------------------------
# Filter Options
# ---------------------------------------------------
location_options = sorted(
    opt_gold_df['location_name']
    .dropna()
    .unique()
)

category_options = sorted(
    opt_gold_df['ornament_category']
    .dropna()
    .unique()
)

subcategory_options = sorted(
    opt_gold_df['ornament_sub_category']
    .dropna()
    .unique()
)

# ---------------------------------------------------
# Default Dates
# ---------------------------------------------------
latest_invoice_date = pd.to_datetime(
    tag_sold_df['invoice_date']
).max()

if pd.isnull(latest_invoice_date):
    latest_invoice_date = pd.Timestamp.now()

default_start_date = latest_invoice_date.replace(
    day=1
)

# ---------------------------------------------------
# Layout
# ---------------------------------------------------
layout = html.Div(
    className='inv-premium-page',
    children=dbc.Container(
        [
            # ---------------------------------------------------
            # Header
            # ---------------------------------------------------
            dbc.Row(
                [
                    dbc.Col(
                        html.H2(
                            "Inventory Optimization Dashboard",
                            className='fw-bold mb-1'
                        ),
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
                                    id='inventory-opt-export-btn',
                                    className='inv-btn-dark px-3 py-1',
                                    size='sm'
                                ),
                                className='text-end'
                            ),
                            dcc.Download(
                                id='inventory-opt-download'
                            )
                        ],
                        width=6
                    )
                ],
                className='mb-4 mt-2 align-items-end'
            ),

            # ---------------------------------------------------
            # Filters Panel
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
                                            id='inventory-opt-date-filter',
                                            start_date=default_start_date,
                                            end_date=latest_invoice_date,
                                            display_format='DD-MMM-YYYY',
                                            className="w-100"
                                        )
                                    ],
                                    width=3
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Location", className="fw-bold mb-1 small text-muted"),
                                        dcc.Dropdown(
                                            id='inventory-opt-location-filter',
                                            options=[
                                                {'label': i, 'value': i}
                                                for i in location_options
                                            ],
                                            multi=True,
                                            placeholder='Select Location'
                                        )
                                    ],
                                    width=2
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Category", className="fw-bold mb-1 small text-muted"),
                                        dcc.Dropdown(
                                            id='inventory-opt-category-filter',
                                            options=[
                                                {'label': i, 'value': i}
                                                for i in category_options
                                            ],
                                            multi=True,
                                            placeholder='Select Category'
                                        )
                                    ],
                                    width=3
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Subcategory", className="fw-bold mb-1 small text-muted"),
                                        dcc.Dropdown(
                                            id='inventory-opt-subcategory-filter',
                                            options=[
                                                {'label': i, 'value': i}
                                                for i in subcategory_options
                                            ],
                                            multi=True,
                                            placeholder='Select Subcategory'
                                        )
                                    ],
                                    width=3
                                ),
                                dbc.Col(
                                    [
                                        html.Label("Action", className="fw-bold mb-1 small text-transparent", style={'color': 'transparent'}),
                                        dbc.Button(
                                            "Enter",
                                            id='inventory-opt-enter-btn',
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
            # Tables Section
            # ---------------------------------------------------
            dcc.Loading(
                html.Div(
                    id='inventory-opt-tables-container'
                ),
                type='default',
                color='#C5A059'
            )
        ],
        fluid=True
    )
)

# ---------------------------------------------------
# Main Callback
# ---------------------------------------------------
@callback(
    Output('inventory-opt-tables-container', 'children'),
    Input('inventory-opt-date-filter', 'start_date'),
    Input('inventory-opt-enter-btn', 'n_clicks'),
    State('inventory-opt-date-filter', 'end_date'),
    State('inventory-opt-location-filter', 'value'),
    State('inventory-opt-category-filter', 'value'),
    State('inventory-opt-subcategory-filter', 'value'),
    prevent_initial_call=False
)
def render_inventory_dashboard(
    start_date,
    n_clicks,
    end_date,
    locations,
    categories,
    sub_categories
):
    # 1. Prepare Data
    opt_gold_filtered, sold_filtered, received_filtered, existing_filtered = prepare_inventory_data(
        opt_gold_df=opt_gold_df,
        sold_df=tag_sold_df,
        received_df=tag_received_df,
        tag_list_df=tag_list_df,
        start_date=start_date,
        end_date=end_date,
        locations=locations,
        categories=categories,
        sub_categories=sub_categories
    )

    # 2. Generate Tables Dict
    all_tables = generate_all_inventory_tables(
        opt_gold_df=opt_gold_filtered,
        sold_df=sold_filtered,
        received_df=received_filtered,
        existing_received_df=existing_filtered
    )

    # 3. Render Dashboard Tables Layout
    cards = []

    for counter in COUNTER_ORDER:
        if counter not in all_tables:
            continue

        df = all_tables[counter]
        if df.empty:
            continue

        # Setup DataTable columns to match output format
        tbl_columns = [
            {'name': 'Location', 'id': 'Location'},
            {'name': 'Counter', 'id': 'Counter'},
            {'name': 'Category', 'id': 'Category'},
            {'name': 'Subcategory', 'id': 'Subcategory'},
            {'name': 'Weight Range Code', 'id': 'weight_range_code'},
            {'name': 'Weight Range', 'id': 'weight_range'},
            {'name': 'Pcs Rcv', 'id': 'Pcs Rcv'},
            {'name': 'Weight Rcv', 'id': 'Weight Rcv'},
            {'name': 'Pcs Sold', 'id': 'Pcs Sold'},
            {'name': 'Weight Sold', 'id': 'Weight Sold'},
            {'name': 'Existing Pcs', 'id': 'Existing Pcs'},
            {'name': 'Existing Weight', 'id': 'Existing Weight'},
            {'name': 'Min Pcs', 'id': 'min_pcs'},
            {'name': 'Min Qty', 'id': 'min_qty'},
            {'name': 'Diff Pcs', 'id': 'Diff_pieces'},
            {'name': 'Diff Weight', 'id': 'Diff_weight'}
        ]

        table = dash_table.DataTable(
            data=df.to_dict('records'),
            columns=tbl_columns,
            fixed_rows={'headers': True},
            fixed_columns={'headers': True, 'data': 1},
            page_action='native',
            page_size=25,
            style_table={
                'overflowX': 'auto',
                'overflowY': 'auto',
                'height': '380px',
                'width': '100%',
                'minWidth': '100%'
            },
            style_cell={
                'textAlign': 'center',
                'padding': '6px 8px',
                'fontSize': '11px',
                'fontFamily': 'Outfit, Inter, sans-serif',
                'whiteSpace': 'normal',
                'height': '30px',
                'minWidth': '80px',
                'width': '95px',
                'maxWidth': '120px',
                'backgroundColor': '#FFFFFF',
                'color': '#1C1B19',
                'border': '1px solid #E3DFD5'
            },
            style_header={
                'fontWeight': 'bold',
                'backgroundColor': '#FAF9F6',
                'color': '#1C1B19',
                'border': '1px solid #D9D4C7',
                'position': 'sticky',
                'top': 0,
                'zIndex': 1
            },
            style_data_conditional=[
                # Bold and highlight total row
                {
                    'if': {
                        'filter_query': '{Location} contains "TOTAL"'
                    },
                    'fontWeight': 'bold',
                    'backgroundColor': '#FAF2DF',
                    'color': '#1C1B19'
                },
                # Bold weight range code column
                {
                    'if': {
                        'column_id': 'weight_range_code'
                    },
                    'fontWeight': 'bold'
                }
            ]
        )

        card = dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H5(
                            counter,
                            className='fw-bold mb-0 text-center py-1'
                        ),
                        style={
                            'borderBottom': '1px solid #E3DFD5',
                            'backgroundColor': '#FAF9F6'
                        }
                    ),
                    dbc.CardBody(
                        table,
                        style={'padding': '6px', 'backgroundColor': '#FFFFFF'}
                    )
                ],
                className='inv-premium-card h-100'
            ),
            xs=12,
            sm=12,
            md=12,
            lg=12,
            xl=12,
            className='mb-4'
        )

        cards.append(card)

    if not cards:
        return html.Div(
            "No data matching select criteria.",
            className="text-center py-5 text-muted fw-bold"
        )

    return dbc.Row(cards)


# ---------------------------------------------------
# Export Callback
# ---------------------------------------------------
@callback(
    Output('inventory-opt-download', 'data'),
    Input('inventory-opt-export-btn', 'n_clicks'),
    State('inventory-opt-date-filter', 'start_date'),
    State('inventory-opt-date-filter', 'end_date'),
    State('inventory-opt-location-filter', 'value'),
    State('inventory-opt-category-filter', 'value'),
    State('inventory-opt-subcategory-filter', 'value'),
    prevent_initial_call=True
)
def export_inventory_data(
    n_clicks,
    start_date,
    end_date,
    locations,
    categories,
    sub_categories
):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "Inventory Optimization Dashboard",
        action="Export Data",
        filters={"start_date": start_date, "end_date": end_date, "locations": locations, "categories": categories, "sub_categories": sub_categories}
    )

    allowed_locations = session.get('locations', [])

    if 'ALL' not in allowed_locations:
        if locations:
            locations = [loc for loc in locations if loc in allowed_locations]
        else:
            locations = allowed_locations

    opt_gold_filtered, sold_filtered, received_filtered, existing_filtered = prepare_inventory_data(
        opt_gold_df=opt_gold_df,
        sold_df=tag_sold_df,
        received_df=tag_received_df,
        tag_list_df=tag_list_df,
        start_date=start_date,
        end_date=end_date,
        locations=locations,
        categories=categories,
        sub_categories=sub_categories
    )

    all_tables = generate_all_inventory_tables(
        opt_gold_df=opt_gold_filtered,
        sold_df=sold_filtered,
        received_df=received_filtered,
        existing_received_df=existing_filtered
    )

    export_dfs = []
    for counter in COUNTER_ORDER:
        if counter not in all_tables:
            continue

        df = all_tables[counter]
        if df.empty:
            continue

        export_dfs.append(df)

    if not export_dfs:
        return None

    final_export_df = pd.concat(
        export_dfs,
        ignore_index=True
    )

    import io
    output = io.BytesIO()

    # Rename columns to user-friendly display headers matching the UI
    rename_cols = {
        'weight_range_code': 'Weight Range Code',
        'weight_range': 'Weight Range',
        'min_pcs': 'Min Pcs',
        'min_qty': 'Min Qty',
        'Diff_pieces': 'Diff Pcs',
        'Diff_weight': 'Diff Weight'
    }
    final_export_df = final_export_df.rename(columns=rename_cols)

    # Force weight range columns to string type explicitly to prevent Excel from converting them to dates
    for col in ['Weight Range Code', 'Weight Range']:
        if col in final_export_df.columns:
            final_export_df[col] = final_export_df[col].astype(str)

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        final_export_df.to_excel(
            writer,
            sheet_name='Inventory Optimization',
            index=False
        )
    output.seek(0)

    return dcc.send_bytes(
        output.getvalue(),
        'inventory_optimization_export.xlsx'
    )



# ---------------------------------------------------
# Dynamic Location Dropdown Options RLS
# ---------------------------------------------------
from dash import callback, Output, Input

@callback(
    Output('inventory-opt-location-filter', 'options'),
    Input('inventory-opt-location-filter', 'id')
)
def populate_inventory_opt_location_filter_options(_):
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
