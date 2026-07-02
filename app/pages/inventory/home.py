from dash import html, callback, Output, Input, State
import dash_bootstrap_components as dbc
from flask import session

# ---------------------------------------------------
# Layout
# ---------------------------------------------------
layout = html.Div(
    className='inv-premium-page',
    style={
        'position': 'relative',
        'overflow': 'hidden'
    },
    children=[
        # Tree Background Watermark
        html.Div(
            style={
                'position': 'fixed',
                'top': '0',
                'left': '0',
                'right': '0',
                'bottom': '0',
                'backgroundImage': "url('/assets/280-2801975_tree-cartoon-black-and-white-outline-drawing-banyan-tree.png')",
                'backgroundRepeat': 'no-repeat',
                'backgroundPosition': 'center center',
                'backgroundSize': '70% auto',
                'opacity': '0.15',
                'mixBlendMode': 'multiply',
                'zIndex': '0',
                'pointerEvents': 'none'
            }
        ),
        dbc.Container(
            [
                # Header Row
                dbc.Row(
                    [
                        dbc.Col(
                            html.A(
                                dbc.Button(
                                    "← Main Homepage",
                                    className='inv-btn-dark px-3 py-1',
                                    size='sm'
                                ),
                                href="/",
                                style={'textDecoration': 'none'}
                            ),
                            width=6
                        ),
                        dbc.Col(
                            html.Div(
                                "ForgeBI Inventory Department",
                                className='text-end fw-bold text-muted small',
                                style={'letterSpacing': '1px'}
                            ),
                            width=6
                        )
                    ],
                    className='mb-5 mt-2 align-items-center'
                ),

                # Center Banner Title
                html.Div(
                    [
                        html.H1(
                            "~ Inventory ~",
                            style={
                                'textAlign': 'center',
                                'fontSize': '56px',
                                'fontFamily': 'Outfit, sans-serif',
                                'fontWeight': '700',
                                'color': '#1C1B19',
                                'letterSpacing': '2px',
                                'marginTop': '40px',
                                'marginBottom': '10px'
                            }
                        ),
                        html.Div(
                            "Departmental Stock Control & Performance Dashboards",
                            style={
                                'textAlign': 'center',
                                'fontSize': '18px',
                                'color': '#7F7C75',
                                'fontStyle': 'italic',
                                'marginBottom': '60px'
                            }
                        ),
                    ]
                ),

                # Dashboard Cards Grid Container
                dbc.Row(
                    id='inventory-dashboards-grid',
                    className='g-4 justify-content-center'
                )
            ],
            fluid=True,
            style={
                'position': 'relative',
                'zIndex': '1'
            }
        ),
        # Signature Line
        html.Div(
            "Developed By Subhankar Roy",
            style={
                'position': 'fixed',
                'bottom': '15px',
                'right': '30px',
                'color': '#7F7C75',
                'fontSize': '12px',
                'opacity': '0.85',
                'fontFamily': 'Outfit, sans-serif',
                'fontStyle': 'italic',
                'zIndex': '2'
            }
        )
    ]
)

# Helper Card Builder
# ---------------------------------------------------
def build_inventory_card(title, description, href):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(title),
                    html.Div(description),
                    html.A(
                        dbc.Button(
                            "Open Dashboard",
                            className="premium-dashboard-btn"
                        ),
                        href=href,
                        target="_blank"
                    )
                ]
            ),
            className="premium-dashboard-card"
        ),
        xs=12, sm=6, md=4
    )

# ---------------------------------------------------
# Dynamic Cards Callback
# ---------------------------------------------------
@callback(
    Output('inventory-dashboards-grid', 'children'),
    Input('inventory-dashboards-grid', 'id')  # Fires on load
)
def render_inventory_home(grid_id):
    allowed_dashboards = session.get('dashboards', [])
    cards = []

    # 0. Daily Performance Dashboard Card
    if 'performance' in allowed_dashboards:
        cards.append(build_inventory_card("Daily Performance Dashboard", "MTD target vs achievement analytics across all locations.", "/performance"))

    # 1. Inventory Optimization Card
    if 'inventory-optimization' in allowed_dashboards:
        cards.append(build_inventory_card("Inventory Optimization", "Counter and subcategory-level stock target analysis compared against dynamic sales velocity and current holdings.", "/inventory-optimization"))

    # 2. Aging Stock Card
    if 'aging-stock' in allowed_dashboards:
        cards.append(build_inventory_card("Aging Stock Analysis", "Operational inventory aging analysis with dynamic stock shelf-life tracking and slow-moving items metrics.", "/aging-stock"))

    # 3. Stock Movement Card
    if 'stock-movement' in allowed_dashboards:
        cards.append(build_inventory_card("Stock Movement", "Enterprise stock inward vs sales movement analysis across counters, categories, and subcategories.", "/stock-movement"))

    # 4. Design Performance Card
    if 'design-performance' in allowed_dashboards:
        cards.append(build_inventory_card("Design Performance", "Design code-level performance metrics, weight, revenue, and item tag movement analysis.", "/design-performance"))

    if not cards:
        return dbc.Col(
            html.Div(
                "You do not have access to any dashboards in the Inventory department.",
                className="text-center py-5 text-muted fw-bold"
            ),
            width=12
        )

    return cards
