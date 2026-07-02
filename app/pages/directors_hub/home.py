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
                        "ForgeBI Directors Hub Department",
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
                    "~ Directors Hub ~",
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
                    "Executive oversight: enterprise performance, comparisons, and MD snapshot overview",
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
            id='directors-hub-dashboards-grid',
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
def build_dh_card(title, description, href):
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
    Output('directors-hub-dashboards-grid', 'children'),
    Input('directors-hub-dashboards-grid', 'id')  # Fires on load
)
def render_directors_hub_home(grid_id):
    allowed_dashboards = session.get('dashboards', [])
    cards = []

    # 1. Daily Performance
    if 'performance' in allowed_dashboards:
        cards.append(build_dh_card("Daily Performance Dashboard", "MTD target vs achievement analytics across all locations.", "/performance"))

    # 2. Comparison
    if 'comparison' in allowed_dashboards:
        cards.append(build_dh_card("Comparison Dashboard", "Last year vs this year enterprise sales comparison analysis.", "/comparison"))

    # SME Performance
    if 'sme-performance' in allowed_dashboards:
        cards.append(build_dh_card("SME Performance", "Total & aggregate achievement comparisons of all RMs & ZMs.", "/sme-performance?from=directors-hub"))

    # 3. Company Snapshot
    if 'company-snapshot' in allowed_dashboards:
        cards.append(build_dh_card("Company Snapshot", "Company-wide D-1 sales summary for MD & ED — KPIs, metal mix, and top products.", "/company-snapshot"))

    # 4. Sales Countdown
    if 'sales-countdown' in allowed_dashboards:
        cards.append(build_dh_card("Sales Countdown", "Live simulating countdown/accumulation of today's sales for TV & board screens.", "/sales-countdown"))

    # 5. Live Customer Counter
    if 'live-customer' in allowed_dashboards:
        cards.append(build_dh_card("Live Customer Counter", "Real-time odometer count of registered customers directly from R2 storage with location breakdowns.", "/live-customer"))

    if not cards:
        return dbc.Col(
            html.Div(
                "You do not have access to any dashboards in the Directors Hub department.",
                className="text-center py-5 text-muted fw-bold"
            ),
            width=12
        )

    return cards
