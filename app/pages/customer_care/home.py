from flask import session
from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc

# ---------------------------------------------------
# Layout
# ---------------------------------------------------
layout = dbc.Container(
    [
        # Header Row
        dbc.Row(
            [
                dbc.Col(
                    html.A(
                        dbc.Button(
                            "← Main Homepage",
                            color="warning",
                            size="sm",
                            className="px-3 py-1",
                            style={'fontWeight': 'bold'}
                        ),
                        href="/",
                        style={'textDecoration': 'none'}
                    ),
                    width=6
                ),
                dbc.Col(
                    html.Div(
                        "Orient BI Customer Care Department",
                        className='text-end fw-bold text-muted small',
                        style={'letterSpacing': '1px', 'color': '#f8d7da'}
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
                    "~ Customer Care ~",
                    style={
                        'textAlign': 'center',
                        'fontSize': '56px',
                        'fontFamily': 'Outfit, sans-serif',
                        'fontWeight': '700',
                        'color': 'white',
                        'letterSpacing': '2px',
                        'marginTop': '40px',
                        'marginBottom': '10px'
                    }
                ),
                html.Div(
                    "Departmental Customer visit metrics, profiles, and Dormancy analytics",
                    style={
                        'textAlign': 'center',
                        'fontSize': '18px',
                        'color': '#f8d7da',
                        'fontStyle': 'italic',
                        'marginBottom': '60px'
                    }
                ),
            ]
        ),

        # Dashboard Cards Grid Container
        dbc.Row(
            id='customer-care-dashboards-grid',
            className='g-4 justify-content-center'
        ),

        # Footer
        html.Div(
            "Developed By Subhankar Roy",
            style={
                'position': 'fixed',
                'bottom': '10px',
                'left': '15px',
                'color': '#f8d7da',
                'fontSize': '12px',
                'opacity': '0.85'
            }
        )
    ],
    fluid=True,
    style={
        'backgroundColor': '#5a0b0b',
        'minHeight': '100vh',
        'padding': '20px'
    }
)

# ---------------------------------------------------
# Helper Card Builder
# ---------------------------------------------------
def build_cc_card(title, description, href):
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
    Output('customer-care-dashboards-grid', 'children'),
    Input('customer-care-dashboards-grid', 'id')  # Fires on load
)
def render_customer_care_home(grid_id):
    allowed_dashboards = session.get('dashboards', [])
    cards = []

    # 1. Daily Customer
    if 'daily-customer' in allowed_dashboards:
        cards.append(build_cc_card("Daily Customer Dashboard", "Customer visit analytics with old/new customer tracking and operational customer insights.", "/daily-customer"))

    # 2. Dormant Customer
    if 'dormant-customer' in allowed_dashboards:
        cards.append(build_cc_card("Dormant Customer List", "Dormant customer lookup across active sales records.", "/dormant-customer"))


    if not cards:
        return dbc.Col(
            html.Div(
                "You do not have access to any dashboards in the Customer Care department.",
                className="text-center py-5 text-muted fw-bold"
            ),
            width=12
        )

    return cards
