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
                        "Orient BI Accounts Department",
                        className='text-end fw-bold text-muted small',
                        style={'letterSpacing': '1px', 'color': "#f7f7f8"}
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
                    "~ Accounts ~",
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
                    "Financial analytics, profitability reviews, and period comparisons",
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
            id='accounts-dashboards-grid',
            className='g-4 justify-content-center'
        ),

        # Footer
        html.Div(
            "Developed By Subhankar Roy",
            style={
                'position': 'fixed',
                'bottom': '10px',
                'left': '15px',
                'color': '#bfdbfe',
                'fontSize': '12px',
                'opacity': '0.85'
            }
        )
    ],
    fluid=True,
    style={
        'background': 'linear-gradient(135deg, #1e3a8a 0%, #1e40af 50%, #0f172a 100%)',
        'minHeight': '100vh',
        'padding': '20px'
    }
)

# ---------------------------------------------------
# Helper Card Builder
# ---------------------------------------------------
def build_accounts_card(title, description, href):
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
    Output('accounts-dashboards-grid', 'children'),
    Input('accounts-dashboards-grid', 'id')  # Fires on load
)
def render_accounts_home(grid_id):
    allowed_dashboards = session.get('dashboards', [])
    cards = []

    # 1. Profitability Analysis
    if 'profitability-analysis' in allowed_dashboards:
        cards.append(
            build_accounts_card(
                "Profitability Analysis",
                "Consolidated and multi-month comparison of branch sales, gross profit, and key ratios.",
                "/profitability-analysis"
            )
        )

    # 2. ROAS & Conversion Analytics
    if 'roas-conversion-analytics' in allowed_dashboards:
        cards.append(
            build_accounts_card(
                "ROAS & Conversion Analytics",
                "Analysis of advertising costs, footfalls, revenue, ACoS, CPF, and RPV.",
                "/roas-conversion-analytics"
            )
        )

    if not cards:
        return dbc.Col(
            html.Div(
                "You do not have access to any dashboards in the Accounts department.",
                className="text-center py-5 text-muted fw-bold"
            ),
            width=12
        )

    return cards
