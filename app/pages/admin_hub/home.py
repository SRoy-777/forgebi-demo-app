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
                        "ForgeBI Admin Hub",
                        className='text-end fw-bold text-muted small',
                        style={'letterSpacing': '1px', 'color': "#C5A059"}
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
                    "~ Admin Hub ~",
                    style={
                        'textAlign': 'center',
                        'fontSize': '56px',
                        'fontFamily': 'Outfit, sans-serif',
                        'fontWeight': '700',
                        'color': '#C5A059',
                        'letterSpacing': '2px',
                        'marginTop': '40px',
                        'marginBottom': '10px'
                    }
                ),
                html.Div(
                    "System configurations, user authorizations, activity monitoring, and security controls",
                    style={
                        'textAlign': 'center',
                        'fontSize': '18px',
                        'color': '#E3D2B5',
                        'fontStyle': 'italic',
                        'marginBottom': '60px'
                    }
                ),
            ]
        ),

        # Dashboard Cards Grid Container
        dbc.Row(
            id='admin-dashboards-grid',
            className='g-4 justify-content-center'
        ),

        # Footer
        html.Div(
            "Developed By Subhankar Roy",
            style={
                'position': 'fixed',
                'bottom': '10px',
                'left': '15px',
                'color': '#E3D2B5',
                'fontSize': '12px',
                'opacity': '0.85'
            }
        )
    ],
    fluid=True,
    style={
        'background': 'linear-gradient(135deg, #1C1B19 0%, #2D2A26 50%, #0F0E0D 100%)',
        'minHeight': '100vh',
        'padding': '20px'
    }
)

# ---------------------------------------------------
# Helper Card Builder
# ---------------------------------------------------
def build_admin_card(title, description, href):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(title, style={'color': '#C5A059', 'fontWeight': '600', 'fontFamily': 'Outfit, sans-serif'}),
                    html.Div(description, style={'color': '#E3D2B5', 'fontSize': '14px', 'minHeight': '50px', 'fontFamily': 'Inter, sans-serif', 'marginBottom': '20px'}),
                    html.A(
                        dbc.Button(
                            "Open Panel",
                            className="premium-dashboard-btn",
                            style={'background': 'linear-gradient(135deg, #C5A059 0%, #B38F48 100%)', 'border': 'none', 'color': 'white'}
                        ),
                        href=href,
                        target="_blank"
                    )
                ]
            ),
            className="premium-dashboard-card",
            style={
                'background': '#1C1B19',
                'border': '1px solid #C5A059',
                'borderRadius': '12px',
                'boxShadow': '0 4px 20px rgba(0,0,0,0.3)',
            }
        ),
        xs=12, sm=6, md=4
    )

# ---------------------------------------------------
# Dynamic Cards Callback
# ---------------------------------------------------
@callback(
    Output('admin-dashboards-grid', 'children'),
    Input('admin-dashboards-grid', 'id')  # Fires on load
)
def render_admin_home(grid_id):
    allowed_dashboards = session.get('dashboards', [])
    allowed_modules = session.get('modules', [])
    cards = []

    # 1. Dashboard Catalog
    if 'dashboard-catalog' in allowed_dashboards or 'admin-hub' in allowed_modules:
        cards.append(
            build_admin_card(
                "Dashboard Catalog",
                "Centralized master registry showing all dynamically discovered dashboards across ForgeBI.",
                "/dashboard-catalog"
            )
        )

    # 2. User Settings
    if 'user-settings' in allowed_dashboards or 'admin-hub' in allowed_modules:
        cards.append(
            build_admin_card(
                "User Settings",
                "Manage authorized user profiles, dashboard permissions, modules access, and branch scopes.",
                "/user-settings"
            )
        )


    # 3. Activity Logs Auditor (Placeholder)
    if 'activity-logs' in allowed_dashboards or 'admin-hub' in allowed_modules:
        cards.append(
            build_admin_card(
                "Activity Logs Auditor",
                "Audit system activities, logs, downloads, and monitor security events.",
                "/activity-logs"
            )
        )

    # 4. System Settings (Placeholder)
    if 'system-settings' in allowed_dashboards or 'admin-hub' in allowed_modules:
        cards.append(
            build_admin_card(
                "System Settings",
                "Manage database configurations, API keys, cache, and system parameters.",
                "/system-settings"
            )
        )

    if not cards:
        return dbc.Col(
            html.Div(
                "You do not have access to any dashboards in the Admin Hub.",
                className="text-center py-5 text-muted fw-bold"
            ),
            width=12
        )

    return cards

