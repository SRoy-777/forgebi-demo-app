from flask import session
from dash import html, dcc, callback, Output, Input, State
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
                        "Orient BI Sales Department",
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
                    "~ Sales ~",
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
                    "Enterprise Sales, Customer Analytics & Business Snapshot",
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
            id='sales-dashboards-grid',
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
def build_sales_card(title, description, href):
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
    Output('sales-dashboards-grid', 'children'),
    Input('sales-dashboards-grid', 'id')  # Fires on load
)
def render_sales_home(grid_id):
    allowed_dashboards = session.get('dashboards', [])
    cards = []

    # 1. Daily Performance
    if 'performance' in allowed_dashboards:
        cards.append(build_sales_card("Daily Performance Dashboard", "MTD target vs achievement analytics across all locations.", "/performance"))

    # 2. Comparison
    if 'comparison' in allowed_dashboards:
        cards.append(build_sales_card("Comparison Dashboard", "Last year vs this year enterprise sales comparison analysis.", "/comparison"))

    # SME Performance
    if 'sme-performance' in allowed_dashboards:
        cards.append(build_sales_card("SME Performance", "Total & aggregate achievement comparisons of all RMs & ZMs.", "/sme-performance?from=sales"))

    # 3. Daily Customer
    if 'daily-customer' in allowed_dashboards:
        cards.append(build_sales_card("Daily Customer Dashboard", "Customer visit analytics with old/new customer tracking and operational customer insights.", "/daily-customer"))

    # 4. Basket Analysis
    if 'basket-analysis' in allowed_dashboards:
        cards.append(build_sales_card("Basket Analysis Dashboard", "Enterprise basket movement analytics with weight bucket level stock, sales and assortment intelligence.", "/basket-analysis"))

    # 5. Branch Health
    if 'branch-health' in allowed_dashboards:
        cards.append(build_sales_card("Branch Health Dashboard", "Branch operational health analytics with targets, KPI tracking, collections and performance benchmarking.", "/branch-health"))

    # 6. Period Comparison
    if 'period-comparison' in allowed_dashboards:
        cards.append(build_sales_card("Period Comparison Dashboard", "Offer period vs benchmark period comparison.", "/period-comparison"))

    # 7. Old Gold
    if 'old-gold' in allowed_dashboards:
        cards.append(build_sales_card("Old Gold Dashboard", "Customer level old gold exchange and purchase analytics with value, weight and transaction tracking.", "/old-gold"))

    # 8. Mini NSV
    if 'mini-nsv' in allowed_dashboards:
        cards.append(build_sales_card("Mini NSV Dashboard", "Mobile Friendly NSV monitoring dashboard for quick business tracking.", "/mini-nsv"))

    # 9. Company Snapshot
    if 'company-snapshot' in allowed_dashboards:
        cards.append(build_sales_card("Company Snapshot", "Company-wide D-1 sales summary for MD & ED — KPIs, metal mix, and top products.", "/company-snapshot"))

    # 10. Employee Performance
    if 'employee-performance' in allowed_dashboards:
        cards.append(build_sales_card("Employee Performance Analysis", "Employee target vs achievement analytics with dynamic scoring and rankings.", "/employee-performance"))

    # 11. Dormant Customer
    if 'dormant-customer' in allowed_dashboards:
        cards.append(build_sales_card("Dormant Customer List", "Dormant customer lookup across active sales records.", "/dormant-customer"))

    # 12. Customer Bucket
    if 'customer-bucket' in allowed_dashboards:
        cards.append(build_sales_card("Customer Bucket Analysis", "Customer bucket lookup based on revenue levels.", "/customer-bucket"))

    # 13. Sales Countdown
    if 'sales-countdown' in allowed_dashboards:
        cards.append(build_sales_card("Sales Countdown", "Live simulating countdown/accumulation of today's sales for TV & board screens.", "/sales-countdown"))

    # 14. Live Customer Counter
    if 'live-customer' in allowed_dashboards:
        cards.append(build_sales_card("Live Customer Counter", "Live registered customer counter.", "/live-customer-counter"))

    # 15. Geo Analytics
    if 'geo-analytics' in allowed_dashboards:
        cards.append(build_sales_card("Geo Analytics", "Interactive GIS platform for branch reach, sales concentration and customer distribution mapping.", "/geo-analytics"))

    if not cards:
        return dbc.Col(
            html.Div(
                "You do not have access to any dashboards in the Sales department.",
                className="text-center py-5 text-muted fw-bold"
            ),
            width=12
        )

    return cards
