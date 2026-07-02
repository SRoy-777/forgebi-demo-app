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
                                "ForgeBI Procurement Department",
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
                            "~ Procurement ~",
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
                            "Departmental Vendor Analytics & Sales Reporting",
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
                    id='procurement-dashboards-grid',
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
def build_procurement_card(title, description, href):
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
    Output('procurement-dashboards-grid', 'children'),
    Input('procurement-dashboards-grid', 'id')  # Fires on load
)
def render_procurement_home(grid_id):
    allowed_dashboards = session.get('dashboards', [])
    cards = []

    # 1. Daily Sales Report (copy of performance dashboard)
    if 'performance' in allowed_dashboards or 'procurement-sales' in allowed_dashboards:
        cards.append(build_procurement_card("Daily Sales Report", "MTD target vs achievement analytics across all locations.", "/procurement-sales"))

    # 2. Vendor Analysis
    if 'vendor-analysis' in allowed_dashboards:
        cards.append(build_procurement_card("Vendor Analysis", "Comprehensive vendor performance, transaction volume, and metal mix sales analysis with granular subcategory insights.", "/vendor-analysis"))

    if not cards:
        return dbc.Col(
            html.Div(
                "You do not have access to any dashboards in the Procurement department.",
                className="text-center py-5 text-muted fw-bold"
            ),
            width=12
        )

    return cards
