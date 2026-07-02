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
from datetime import datetime

from backend.services.admin_hub.dashboard_catalog_service import (
    generate_catalog_data,
    generate_export_dataframe,
)

# ---------------------------------------------------
# Last Updated Timestamp
# ---------------------------------------------------
LATEST_REFRESH = datetime.now().strftime('%d-%b-%Y')

# ---------------------------------------------------
# KPI Card Builder
# ---------------------------------------------------
def create_kpi_card(title, value):
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
                str(value),
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

def build_kpi_section(total_modules, total_dashboards, active_dashboards, inactive_dashboards):
    cards = [
        dbc.Col(create_kpi_card('Total Modules', total_modules), xs=6, sm=3, md=3, lg=3, className='mb-2'),
        dbc.Col(create_kpi_card('Total Dashboards', total_dashboards), xs=6, sm=3, md=3, lg=3, className='mb-2'),
        dbc.Col(create_kpi_card('Active Dashboards', active_dashboards), xs=6, sm=3, md=3, lg=3, className='mb-2'),
        dbc.Col(create_kpi_card('Inactive Dashboards', inactive_dashboards), xs=6, sm=3, md=3, lg=3, className='mb-2'),
    ]
    return html.Div([
        html.H5(
            'Discovered Metrics Summary',
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
def build_table(df):
    return dbc.Card([
        dbc.CardHeader(
            html.H5(
                "Discovered Dashboards Master Registry",
                className='fw-bold mb-0',
                style={'textAlign': 'left', 'color': '#1C1B19', 'fontFamily': 'Outfit'},
            ),
            style={'backgroundColor': '#FAF9F6', 'borderBottom': '1px solid #E8DFCE'},
        ),
        dbc.CardBody(
            dash_table.DataTable(
                id='catalog-table',
                data=df.to_dict('records'),
                columns=[
                    {'name': 'Dashboard ID', 'id': 'Dashboard ID'},
                    {'name': 'Dashboard Name', 'id': 'Dashboard Name'},
                    {'name': 'Module', 'id': 'Module'},
                    {'name': 'File Path', 'id': 'File Path'},
                    {'name': 'Python File Name', 'id': 'Python File Name'},
                    {'name': 'Dashboard Active', 'id': 'Dashboard Active'},
                ],
                fixed_rows={'headers': True},
                page_action='none',
                style_as_list_view=True,
                style_table={
                    'overflowX': 'auto',
                    'overflowY': 'auto',
                    'maxHeight': '650px',
                    'width': '100%',
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px 12px',
                    'fontSize': '13px',
                    'fontFamily': "'Outfit', 'Inter', sans-serif",
                    'backgroundColor': '#FFFFFF',
                    'color': '#1C1B19',
                    'borderBottom': '1px solid #FAF6EE',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_cell_conditional=[
                    {'if': {'column_id': 'Dashboard ID'}, 'minWidth': '150px', 'width': '150px', 'maxWidth': '220px'},
                    {'if': {'column_id': 'Dashboard Name'}, 'minWidth': '180px', 'width': '180px', 'maxWidth': '250px'},
                    {'if': {'column_id': 'Module'}, 'minWidth': '120px', 'width': '120px', 'maxWidth': '180px'},
                    {'if': {'column_id': 'File Path'}, 'minWidth': '300px', 'width': '300px', 'maxWidth': '450px'},
                    {'if': {'column_id': 'Python File Name'}, 'minWidth': '180px', 'width': '180px', 'maxWidth': '250px'},
                    {'if': {'column_id': 'Dashboard Active'}, 'minWidth': '120px', 'width': '120px', 'maxWidth': '150px', 'textAlign': 'center'},
                ],
                style_header={
                    'fontWeight': 'bold',
                    'backgroundColor': '#1C1B19',
                    'color': '#C5A059',
                    'fontSize': '13px',
                    'textAlign': 'left',
                    'fontFamily': "'Outfit', sans-serif",
                    'border': '1px solid #E8DFCE',
                    'padding': '10px 12px',
                },
                style_header_conditional=[
                    {'if': {'column_id': 'Dashboard Active'}, 'textAlign': 'center'},
                ],
                style_data_conditional=[
                    {
                        'if': {
                            'column_id': 'Dashboard Active',
                            'filter_query': '{Dashboard Active} eq "Yes"'
                        },
                        'color': '#2e7d32',
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {
                            'column_id': 'Dashboard Active',
                            'filter_query': '{Dashboard Active} eq "No"'
                        },
                        'color': '#c62828',
                        'fontWeight': 'bold'
                    }
                ]
            ),
            style={'padding': '6px'},
        )
    ], className='inv-gold-card mb-4')

# ---------------------------------------------------
# Layout
# ---------------------------------------------------
layout = html.Div(
    className='inv-premium-page-gold',
    children=dbc.Container([
        
        # Header Row
        dbc.Row([
            dbc.Col([
                html.A(
                    dbc.Button(
                        "← Admin Hub",
                        className='inv-btn-dark px-3 py-1',
                        size='sm'
                    ),
                    href="/admin-hub",
                    style={'textDecoration': 'none'}
                ),
                html.H2(
                    'Dashboard Catalog',
                    className='fw-bold mt-3 mb-1',
                    style={'fontFamily': 'Outfit'}
                ),
            ], width=8),

            dbc.Col([
                html.Div(
                    f"Last Updated : {LATEST_REFRESH}",
                    className='text-end fw-bold mb-2',
                    style={'color': '#5C4D32', 'fontFamily': 'Outfit'},
                ),
                html.Div([
                    dbc.Button(
                        'Export Data',
                        id='catalog-export-btn',
                        className='inv-btn-dark px-3 py-1 me-2 shadow-sm',
                        size='sm',
                    ),
                    dbc.Button(
                        'Enter',
                        id='catalog-enter-btn',
                        className='inv-btn-gold px-3 py-1 shadow-sm',
                        size='sm',
                    ),
                ], className='text-end'),
                dcc.Download(id='catalog-download'),
            ], width=4),
        ], className='mb-4 mt-2 align-items-end'),

        # Filter Section Card
        dbc.Card(
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Dashboard Name Search", className="fw-bold mb-1 small text-muted"),
                        dbc.Input(
                            id='catalog-search-input',
                            type='text',
                            placeholder='Search dashboard name or ID...',
                            className='w-100',
                            style={'height': '38px', 'fontSize': '13px'}
                        )
                    ], width=6),

                    dbc.Col([
                        html.Label("Module Filter", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='catalog-module-filter',
                            placeholder='Select Module(s)',
                            multi=True,
                            className='w-100',
                        )
                    ], width=6),
                ]),
            ]),
            className='inv-gold-card mb-4',
        ),

        # Containers for Dynamic Elements
        html.Div(id='catalog-kpi-container'),
        
        dcc.Loading(
            html.Div(id='catalog-table-container'),
            type='circle',
        ),

    ], fluid=True, style={'padding': '0px'})
)

# ---------------------------------------------------
# Module Options Callback
# ---------------------------------------------------
@callback(
    Output('catalog-module-filter', 'options'),
    Input('catalog-module-filter', 'id')
)
def populate_modules_dropdown(_):
    df = generate_catalog_data()
    modules = set()
    for mods in df['Module'].dropna().unique():
        for m in mods.split(','):
            modules.add(m.strip())
    options = sorted(list(modules))
    return [{'label': m, 'value': m} for m in options]

# ---------------------------------------------------
# Main Table & KPI callback
# ---------------------------------------------------
@callback(
    Output('catalog-kpi-container', 'children'),
    Output('catalog-table-container', 'children'),
    Input('catalog-enter-btn', 'n_clicks'),
    State('catalog-search-input', 'value'),
    State('catalog-module-filter', 'value'),
)
def render_catalog_dashboard(n_clicks, search_val, selected_modules):
    df = generate_export_dataframe(search_val, selected_modules)
    
    # Calculate summary metrics
    unique_modules = set()
    for mods in df['Module'].dropna().unique():
        for m in mods.split(','):
            unique_modules.add(m.strip())
    
    total_modules = len(unique_modules)
    total_dashboards = len(df)
    active_dashboards = len(df[df['Dashboard Active'] == 'Yes'])
    inactive_dashboards = len(df[df['Dashboard Active'] == 'No'])
    
    kpi_layout = build_kpi_section(
        total_modules=total_modules,
        total_dashboards=total_dashboards,
        active_dashboards=active_dashboards,
        inactive_dashboards=inactive_dashboards
    )
    
    table_layout = build_table(df)
    
    return kpi_layout, table_layout

# ---------------------------------------------------
# Export Callback
# ---------------------------------------------------
@callback(
    Output('catalog-download', 'data'),
    Input('catalog-export-btn', 'n_clicks'),
    State('catalog-search-input', 'value'),
    State('catalog-module-filter', 'value'),
    prevent_initial_call=True,
)
def export_catalog_data(n_clicks, search_val, selected_modules):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "Dashboard Catalog",
        action="Export Data",
        filters={"search_val": search_val, "selected_modules": selected_modules}
    )

    if not n_clicks:
        return None
    
    export_df = generate_export_dataframe(search_val, selected_modules)
    
    return dcc.send_data_frame(
        export_df.to_csv,
        'dashboard_catalog_export.csv',
        index=False,
    )
