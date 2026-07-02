from flask import session
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import os


# ---------------------------------------------------
# Layout Function
# ---------------------------------------------------

def get_layout():

    allowed_dashboards = session.get(

        'dashboards',

        []

    )

    allowed_modules = session.get(

        'modules',

        []

    )

    return html.Div(
        id='home-layout-wrapper',
        className='inv-premium-page-gold',
        children=dbc.Container(

            [
                dcc.Store(id='home-theme-store', data='light'),

                # Menu Button at the extreme top left
                dbc.Button(
                    "☰",
                    id="btn-open-offcanvas",
                    className="home-theme-icon-btn",
                    style={
                        'position': 'absolute',
                        'top': '15px',
                        'left': '15px',
                    }
                ),

                # Search Button directly below Menu Button
                dbc.Button(
                    "🔍",
                    id="btn-open-search",
                    className="home-theme-icon-btn",
                    style={
                        'position': 'absolute',
                        'top': '75px',
                        'left': '15px',
                    }
                ),

                # Dark Mode Toggle Button at the extreme top right
                dbc.Button(
                    "🌙",
                    id="btn-toggle-theme",
                    className="home-theme-icon-btn",
                    style={
                        'position': 'absolute',
                        'top': '15px',
                        'right': '15px',
                    }
                ),

            html.Br(),

            # ---------------------------------------------------
            # Logo
            # ---------------------------------------------------

            html.Div(

                html.Img(
                    id='home-logo',

                    src="/assets/orient_logo.png",

                    style={

                        'height': '110px',

                        'marginBottom': '20px'

                    }

                ),

                style={

                    'textAlign': 'center'

                }

            ),

            # ---------------------------------------------------
            # Header
            # ---------------------------------------------------

            html.Div(

                [

                    dbc.Button(

                        "Download Activity Logs",

                        id="btn-download-logs",

                        color="success",

                        size="sm",

                        className="me-2"

                    ) if session.get('email') == 'business.sroy@gmail.com' else None,

                    dcc.Download(id="download-logs-csv") if session.get('email') == 'business.sroy@gmail.com' else None,

                ],

                style={

                    'textAlign': 'right',

                    'marginBottom': '10px'

                }

            ) if session.get('email') == 'business.sroy@gmail.com' else None,

            html.H1(

                "Orient Business Intelligence",

                style={

                    'fontWeight': 'bold',

                    'textAlign': 'center',

                    'color': '#1C1B19'

                }

            ),

            html.Div(

                "Centralized Enterprise Analytics Application",

                className='home-subheader',

                style={

                    'textAlign': 'center',

                    'fontSize': '18px',

                    'marginBottom': '50px'

                }

            ),

            # ---------------------------------------------------
            # Dashboard Cards
            # ---------------------------------------------------

            dbc.Row(
                [
                    # 1. Execution Tracker
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("📝", className="module-icon"),
                                    html.H4("Execution Tracker", className="module-title"),
                                    html.Div("Real-time task tracking, execution status, and progress metrics across operational departments.", className="module-desc"),
                                    html.A(
                                        dbc.Button("Open Module", className="module-btn"),
                                        href="/execution-tracker",
                                        target="_blank"
                                    )
                                ]
                            ),
                            className="premium-module-card"
                        ),
                        xs=12, sm=6, md=6, lg=3
                    ) if 'execution-tracker' in allowed_modules else None,

                    # 2. Sales
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("💼", className="module-icon"),
                                    html.H4("Sales", className="module-title"),
                                    html.Div("Analytics for performance comparisons, customer visits, basket movements, and MD snapshot.", className="module-desc"),
                                    html.A(
                                        dbc.Button("Open Module", className="module-btn"),
                                        href="/sales",
                                        target="_blank"
                                    )
                                ]
                            ),
                            className="premium-module-card"
                        ),
                        xs=12, sm=6, md=6, lg=3
                    ) if 'sales' in allowed_modules else None,

                    # 3. Inventory
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("📦", className="module-icon"),
                                    html.H4("Inventory", className="module-title"),
                                    html.Div("Stock optimization, inventory aging stock analysis, and stock movement dashboards.", className="module-desc"),
                                    html.A(
                                        dbc.Button("Open Module", className="module-btn"),
                                        href="/inventory",
                                        target="_blank"
                                    )
                                ]
                            ),
                            className="premium-module-card"
                        ),
                        xs=12, sm=6, md=6, lg=3
                    ) if 'inventory' in allowed_modules else None,

                    # 4. Procurement
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("🤝", className="module-icon"),
                                    html.H4("Procurement", className="module-title"),
                                    html.Div("Vendor analysis, category/subcategory procurement performance, and daily sales reports.", className="module-desc"),
                                    html.A(
                                        dbc.Button("Open Module", className="module-btn"),
                                        href="/procurement",
                                        target="_blank"
                                    )
                                ]
                            ),
                            className="premium-module-card"
                        ),
                        xs=12, sm=6, md=6, lg=3
                    ) if 'procurement' in allowed_modules else None,

                    # 5. Accounts
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("💳", className="module-icon"),
                                    html.H4("Accounts", className="module-title"),
                                    html.Div("Financial statements, cash flows, ledger balances, and expense reports tracking.", className="module-desc"),
                                    html.A(
                                        dbc.Button("Open Module", className="module-btn"),
                                        href="/accounts",
                                        target="_blank"
                                    )
                                ]
                            ),
                            className="premium-module-card"
                        ),
                        xs=12, sm=6, md=6, lg=3
                    ) if 'accounts' in allowed_modules else None,

                    # 6. Customer Care
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("❤️", className="module-icon"),
                                    html.H4("Customer Care", className="module-title"),
                                    html.Div("Customer visit profiling, transaction histories, loyalty statistics, and dormancy lookup.", className="module-desc"),
                                    html.A(
                                        dbc.Button("Open Module", className="module-btn"),
                                        href="/customer-care",
                                        target="_blank"
                                    )
                                ]
                            ),
                            className="premium-module-card"
                        ),
                        xs=12, sm=6, md=6, lg=3
                    ) if 'customer-care' in allowed_modules else None,

                    # 7. Directors Hub
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("👑", className="module-icon"),
                                    html.H4("Directors Hub", className="module-title"),
                                    html.Div("High-level executive target benchmarking, year-on-year enterprise comparisons, and MD dashboard.", className="module-desc"),
                                    html.A(
                                        dbc.Button("Open Module", className="module-btn"),
                                        href="/directors-hub",
                                        target="_blank"
                                    )
                                ]
                            ),
                            className="premium-module-card"
                        ),
                        xs=12, sm=6, md=6, lg=3
                    ) if 'directors-hub' in allowed_modules else None,

                    # 8. HR
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("👥", className="module-icon"),
                                    html.H4("HR", className="module-title"),
                                    html.Div("Employee attendance, performance evaluations, sales target mappings, and payouts.", className="module-desc"),
                                    html.A(
                                        dbc.Button("Open Module", className="module-btn"),
                                        href="/hr",
                                        target="_blank"
                                    )
                                ]
                            ),
                            className="premium-module-card"
                        ),
                        xs=12, sm=6, md=6, lg=3
                    ) if 'hr' in allowed_modules else None,

                    # 9. IT
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("💻", className="module-icon"),
                                    html.H4("IT", className="module-title"),
                                    html.Div("System access logs, password audits, notification schedules, and infrastructure controls.", className="module-desc"),
                                    html.A(
                                        dbc.Button("Open Module", className="module-btn"),
                                        href="/it",
                                        target="_blank"
                                    )
                                ]
                            ),
                            className="premium-module-card"
                        ),
                        xs=12, sm=6, md=6, lg=3
                    ) if 'it' in allowed_modules else None,

                    # 10. Marketing
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("📢", className="module-icon"),
                                    html.H4("Marketing", className="module-title"),
                                    html.Div("Campaign conversions, discount code analytics, and customer demographic segments.", className="module-desc"),
                                    html.A(
                                        dbc.Button("Open Module", className="module-btn"),
                                        href="/marketing",
                                        target="_blank"
                                    )
                                ]
                            ),
                            className="premium-module-card"
                        ),
                        xs=12, sm=6, md=6, lg=3
                    ) if 'marketing' in allowed_modules else None,

                    # 11. Admin Hub
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("⚙️", className="module-icon"),
                                    html.H4("Admin Hub", className="module-title"),
                                    html.Div("System administration, user access management, configurations, and logs auditing.", className="module-desc"),
                                    html.A(
                                        dbc.Button("Open Module", className="module-btn"),
                                        href="/admin-hub",
                                        target="_blank"
                                    )
                                ]
                            ),
                            className="premium-module-card"
                        ),
                        xs=12, sm=6, md=6, lg=3
                    ) if 'admin-hub' in allowed_modules else None
                ],
                className="g-4 justify-content-center"
            ),


            # ---------------------------------------------------
            # Footer
            # ---------------------------------------------------

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

            ),

            # Change Password Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Change Password")),
                    dbc.ModalBody(
                        [
                            dbc.Label("Current Password"),
                            dbc.Input(id="change-pw-current", type="password", placeholder="Enter current password", className="mb-2"),
                            dbc.Label("New Password"),
                            dbc.Input(id="change-pw-new", type="password", placeholder="Enter new password", className="mb-2"),
                            dbc.Label("Confirm New Password"),
                            dbc.Input(id="change-pw-confirm", type="password", placeholder="Confirm new password", className="mb-3"),
                            html.Div(id="change-pw-status", style={"textAlign": "center"})
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("Update Password", id="btn-submit-change-pw", color="warning", className="me-2"),
                            dbc.Button("Close", id="btn-close-change-pw", color="secondary")
                        ]
                    )
                ],
                id="change-password-modal",
                is_open=False,
            ),

            # Search Dashboards Modal
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle("Search Dashboards", className="fw-bold"),
                        close_button=True
                    ),
                    dbc.ModalBody(
                        [
                            dbc.Input(
                                id="search-dashboards-input",
                                type="text",
                                placeholder="Search by dashboard name or description...",
                                className="search-input-box mb-3",
                                autoFocus=True,
                                autoComplete="off"
                            ),
                            html.Div(
                                id="search-dashboards-results",
                                style={
                                    'maxHeight': '400px',
                                    'overflowY': 'auto',
                                    'paddingRight': '5px'
                                }
                            )
                        ],
                        className="search-modal-body"
                    ),
                    dbc.ModalFooter(
                        dbc.Button("Close", id="btn-close-search", color="secondary", size="sm")
                    )
                ],
                id="search-dashboards-modal",
                is_open=False,
                contentClassName="search-modal-content-light",
                keyboard=True,
                backdrop=True
            ),

            # System Control Panel (Offcanvas)
            dbc.Offcanvas(
                html.Div([
                    # User profile header
                    html.Div([
                        html.Div(
                            children=session.get('email', 'U')[0].upper() if session.get('email') else 'U',
                            style={
                                'width': '60px',
                                'height': '60px',
                                'borderRadius': '50%',
                                'backgroundColor': '#ffc107',
                                'color': '#5a0b0b',
                                'fontSize': '24px',
                                'fontWeight': 'bold',
                                'display': 'flex',
                                'alignItems': 'center',
                                'justifyContent': 'center',
                                'margin': '0 auto 10px auto',
                                'boxShadow': '0 4px 8px rgba(0,0,0,0.3)'
                            }
                        ),
                        html.H5(session.get('email', 'Guest User'), className='fw-bold mb-0 text-center'),
                        html.Small("Orient BI Authorized Session", className='text-muted d-block text-center mt-1'),
                    ], className='p-3 mb-4 rounded', style={'backgroundColor': 'rgba(255, 255, 255, 0.05)', 'border': '1px solid rgba(255,255,255,0.1)'}),

                    # Navigation links
                    html.Div([
                        html.A(
                            dbc.Button(
                                [
                                    html.Span("📝 Execution Tracker"),
                                    html.Span("→", className='float-end')
                                ],
                                color="link",
                                className="w-100 text-start text-white text-decoration-none py-2 px-1 border-bottom border-secondary",
                                style={'fontSize': '14px', 'borderColor': 'rgba(255,255,255,0.05)'}
                            ),
                            href="/execution-tracker",
                            target="_blank"
                        ) if 'execution-tracker' in allowed_modules else None,
                        html.A(
                            dbc.Button(
                                [
                                    html.Span("💼 Sales"),
                                    html.Span("→", className='float-end')
                                ],
                                color="link",
                                className="w-100 text-start text-white text-decoration-none py-2 px-1 border-bottom border-secondary",
                                style={'fontSize': '14px', 'borderColor': 'rgba(255,255,255,0.05)'}
                            ),
                            href="/sales",
                            target="_blank"
                        ) if 'sales' in allowed_modules else None,
                        html.A(
                            dbc.Button(
                                [
                                    html.Span("📦 Inventory"),
                                    html.Span("→", className='float-end')
                                ],
                                color="link",
                                className="w-100 text-start text-white text-decoration-none py-2 px-1 border-bottom border-secondary",
                                style={'fontSize': '14px', 'borderColor': 'rgba(255,255,255,0.05)'}
                            ),
                            href="/inventory",
                            target="_blank"
                        ) if 'inventory' in allowed_modules else None,
                        html.A(
                            dbc.Button(
                                [
                                    html.Span("💼 Procurement"),
                                    html.Span("→", className='float-end')
                                ],
                                color="link",
                                className="w-100 text-start text-white text-decoration-none py-2 px-1 border-bottom border-secondary",
                                style={'fontSize': '14px', 'borderColor': 'rgba(255,255,255,0.05)'}
                            ),
                            href="/procurement",
                            target="_blank"
                        ) if 'procurement' in allowed_modules else None,
                        html.A(
                            dbc.Button(
                                [
                                    html.Span("💳 Accounts"),
                                    html.Span("→", className='float-end')
                                ],
                                color="link",
                                className="w-100 text-start text-white text-decoration-none py-2 px-1 border-bottom border-secondary",
                                style={'fontSize': '14px', 'borderColor': 'rgba(255,255,255,0.05)'}
                            ),
                            href="/accounts",
                            target="_blank"
                        ) if 'accounts' in allowed_modules else None,
                        html.A(
                            dbc.Button(
                                [
                                    html.Span("❤️ Customer Care"),
                                    html.Span("→", className='float-end')
                                ],
                                color="link",
                                className="w-100 text-start text-white text-decoration-none py-2 px-1 border-bottom border-secondary",
                                style={'fontSize': '14px', 'borderColor': 'rgba(255,255,255,0.05)'}
                            ),
                            href="/customer-care",
                            target="_blank"
                        ) if 'customer-care' in allowed_modules else None,
                        html.A(
                            dbc.Button(
                                [
                                    html.Span("👑 Directors Hub"),
                                    html.Span("→", className='float-end')
                                ],
                                color="link",
                                className="w-100 text-start text-white text-decoration-none py-2 px-1 border-bottom border-secondary",
                                style={'fontSize': '14px', 'borderColor': 'rgba(255,255,255,0.05)'}
                            ),
                            href="/directors-hub",
                            target="_blank"
                        ) if 'directors-hub' in allowed_modules else None,
                        html.A(
                            dbc.Button(
                                [
                                    html.Span("👥 HR"),
                                    html.Span("→", className='float-end')
                                ],
                                color="link",
                                className="w-100 text-start text-white text-decoration-none py-2 px-1 border-bottom border-secondary",
                                style={'fontSize': '14px', 'borderColor': 'rgba(255,255,255,0.05)'}
                            ),
                            href="/hr",
                            target="_blank"
                        ) if 'hr' in allowed_modules else None,
                        html.A(
                            dbc.Button(
                                [
                                    html.Span("💻 IT"),
                                    html.Span("→", className='float-end')
                                ],
                                color="link",
                                className="w-100 text-start text-white text-decoration-none py-2 px-1 border-bottom border-secondary",
                                style={'fontSize': '14px', 'borderColor': 'rgba(255,255,255,0.05)'}
                            ),
                            href="/it",
                            target="_blank"
                        ) if 'it' in allowed_modules else None,
                        html.A(
                            dbc.Button(
                                [
                                    html.Span("📢 Marketing"),
                                    html.Span("→", className='float-end')
                                ],
                                color="link",
                                className="w-100 text-start text-white text-decoration-none py-2 px-1 border-bottom border-secondary",
                                style={'fontSize': '14px', 'borderColor': 'rgba(255,255,255,0.05)'}
                            ),
                            href="/marketing",
                            target="_blank"
                        ) if 'marketing' in allowed_modules else None,
                        html.A(
                            dbc.Button(
                                [
                                    html.Span("⚙️ Admin Hub"),
                                    html.Span("→", className='float-end')
                                ],
                                color="link",
                                className="w-100 text-start text-white text-decoration-none py-2 px-1 border-bottom border-secondary",
                                style={'fontSize': '14px', 'borderColor': 'rgba(255,255,255,0.05)'}
                            ),
                            href="/admin-hub",
                            target="_blank"
                        ) if 'admin-hub' in allowed_modules else None
                    ], className='mb-4'),


                    # Action buttons at the bottom
                    html.Div([
                        dbc.Button(
                            "Change Password",
                            id="btn-change-password-trigger",
                            color="danger",
                            size="sm",
                            className="w-100 mb-2"
                        ),
                        html.A(
                            dbc.Button(
                                "Logout",
                                color="danger",
                                size="sm",
                                className="w-100"
                            ),
                            href="/logout",
                            style={
                                'textDecoration': 'none'
                            }
                        )
                    ], className='mt-auto pt-3 border-top border-secondary')
                ], style={'display': 'flex', 'flexDirection': 'column', 'minHeight': '100%'}),
                id="home-offcanvas",
                title="Menu",
                is_open=False,
                placement="start", # slides from left
                scrollable=True,
                backdrop=True,
                style={
                    'backgroundColor': '#1C1B19', 
                    'color': 'white', 
                    'width': '300px',
                    'borderRight': '2px solid #C5A059'
                }
            )

        ],

        fluid=True,

        style={

            'minHeight': '100vh',

            'padding': '0px'

        }

    )
)


layout = html.Div()


# ---------------------------------------------------
# Download Callback
# ---------------------------------------------------

@callback(
    Output("download-logs-csv", "data"),
    Input("btn-download-logs", "n_clicks"),
    prevent_initial_call=True
)
def download_activity_logs(n_clicks):
    if not n_clicks:
        return None

    if session.get('email') != 'business.sroy@gmail.com':
        return None

    import boto3
    import pandas as pd

    ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "").strip()
    ACCESS_KEY = os.getenv("R2_ACCESS_KEY", "").strip()
    SECRET_KEY = os.getenv("R2_SECRET_KEY", "").strip()
    BUCKET_NAME = "orient-analytics-snapshots"
    FILE_KEY = "user_activity_log.csv"

    local_path = "downloaded_user_activity_log.csv"

    try:
        s3 = boto3.client(
            service_name='s3',
            endpoint_url=f'https://{ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY
        )
        s3.download_file(BUCKET_NAME, FILE_KEY, local_path)
        df = pd.read_csv(local_path)
        return dcc.send_data_frame(df.to_csv, "user_activity_log.csv", index=False)
    except Exception as e:
        print(f"Error downloading logs: {e}")
        err_df = pd.DataFrame([{"error": f"Failed to download logs from R2: {str(e)}"}])
        return dcc.send_data_frame(err_df.to_csv, "log_error.csv", index=False)


# ---------------------------------------------------
# Change Password Callbacks
# ---------------------------------------------------

@callback(
    Output("change-password-modal", "is_open"),
    [
        Input("btn-change-password-trigger", "n_clicks"),
        Input("btn-close-change-pw", "n_clicks")
    ],
    [State("change-password-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_change_password_modal(trigger_clicks, close_clicks, is_open):
    if trigger_clicks or close_clicks:
        return not is_open
    return is_open


@callback(
    [
        Output("change-pw-status", "children"),
        Output("change-pw-status", "style")
    ],
    Input("btn-submit-change-pw", "n_clicks"),
    [
        State("change-pw-current", "value"),
        State("change-pw-new", "value"),
        State("change-pw-confirm", "value")
    ],
    prevent_initial_call=True
)
def handle_password_change(n_clicks, current_pw, new_pw, confirm_pw):
    if not n_clicks:
        return "", {}

    if not current_pw or not new_pw or not confirm_pw:
        return "All fields are required.", {"color": "red", "textAlign": "center"}

    if new_pw != confirm_pw:
        return "New passwords do not match.", {"color": "red", "textAlign": "center"}

    if len(new_pw) < 6:
        return "New password must be at least 6 characters long.", {"color": "red", "textAlign": "center"}

    email = session.get('email')
    if not email:
        return "User session expired. Please log in again.", {"color": "red", "textAlign": "center"}

    # Update database via password manager
    from backend.services.password_manager import change_password
    success, msg = change_password(email, current_pw, new_pw)
    if not success:
        return msg, {"color": "red", "textAlign": "center"}

    # Notify administrator via Resend
    from backend.services.notifier import send_admin_email_alert
    from datetime import datetime

    subject = f"🔒 Security Alert: Password Changed for {email}"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
        <h2 style="color: #337ab7; border-bottom: 2px solid #337ab7; padding-bottom: 10px; margin-top: 0;">Password Changed Successfully</h2>
        <p>This is to confirm that the user has successfully changed their login password.</p>
        <table style="width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 20px;">
            <tr style="background-color: #f9f9f9;">
                <td style="padding: 8px; font-weight: bold; width: 120px; border-bottom: 1px solid #eee;">User Email:</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{email}</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold; border-bottom: 1px solid #eee;">New Password:</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee; font-family: monospace; font-size: 14px; color: #d9534f; font-weight: bold;">{new_pw}</td>
            </tr>
            <tr style="background-color: #f9f9f9;">
                <td style="padding: 8px; font-weight: bold; border-bottom: 1px solid #eee;">Changed At:</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}</td>
            </tr>
        </table>
        <p style="color: #777; font-size: 13px;">If this change was not authorized by the user, please take immediate administrative action to lock or reset the account.</p>
        <hr style="border: 0; border-top: 1px solid #eee; margin-top: 25px;">
        <p style="font-size: 11px; color: #777; margin-bottom: 0;">Sent automatically via Orient BI Security System.</p>
    </div>
    """
    
    send_admin_email_alert(subject, html_content)
    return "Password changed successfully!", {"color": "green", "textAlign": "center"}


# ---------------------------------------------------
# System Control Panel (Offcanvas) Callback
# ---------------------------------------------------

@callback(
    Output("home-offcanvas", "is_open"),
    Input("btn-open-offcanvas", "n_clicks"),
    State("home-offcanvas", "is_open"),
    prevent_initial_call=True
)
def toggle_offcanvas(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open


# ---------------------------------------------------
# Theme Toggle Callback
# ---------------------------------------------------

@callback(
    Output("home-layout-wrapper", "className"),
    Output("btn-toggle-theme", "children"),
    Output("home-theme-store", "data"),
    Output("home-logo", "src"),
    Output("search-dashboards-modal", "contentClassName"),
    Input("btn-toggle-theme", "n_clicks"),
    State("home-theme-store", "data"),
    prevent_initial_call=True
)
def toggle_theme(n_clicks, current_theme):
    if not n_clicks:
        return "inv-premium-page-gold", "🌙", "light", "/assets/orient_logo.png", "search-modal-content-light"
    
    if current_theme == "light":
        return "inv-premium-page-gold-dark", "☀️", "dark", "/assets/orient_logo_for_dark_theme.png", "search-modal-content-dark"
    else:
        return "inv-premium-page-gold", "🌙", "light", "/assets/orient_logo.png", "search-modal-content-light"


# ---------------------------------------------------
# Dashboard Search Catalog & Callbacks
# ---------------------------------------------------

DASHBOARD_CATALOG = [
    {
        'key': 'performance',
        'title': 'Daily Performance Dashboard',
        'desc': 'MTD target vs achievement analytics across all locations.',
        'module': 'Sales',
        'href': '/performance'
    },
    {
        'key': 'comparison',
        'title': 'Comparison Dashboard',
        'desc': 'Last year vs this year enterprise sales comparison analysis.',
        'module': 'Sales',
        'href': '/comparison'
    },
    {
        'key': 'sme-performance',
        'title': 'SME Performance',
        'desc': 'Total & aggregate achievement comparisons of all RMs & ZMs.',
        'module': 'Sales',
        'href': '/sme-performance'
    },
    {
        'key': 'daily-customer',
        'title': 'Daily Customer Dashboard',
        'desc': 'Customer visit analytics with old/new customer tracking and operational customer insights.',
        'module': 'Sales',
        'href': '/daily-customer'
    },
    {
        'key': 'basket-analysis',
        'title': 'Basket Analysis Dashboard',
        'desc': 'Enterprise basket movement analytics with weight bucket level stock, sales and assortment intelligence.',
        'module': 'Sales',
        'href': '/basket-analysis'
    },
    {
        'key': 'branch-health',
        'title': 'Branch Health Dashboard',
        'desc': 'Branch operational health analytics with targets, KPI tracking, collections and performance benchmarking.',
        'module': 'Sales',
        'href': '/branch-health'
    },
    {
        'key': 'period-comparison',
        'title': 'Period Comparison Dashboard',
        'desc': 'Offer period vs benchmark period comparison.',
        'module': 'Sales',
        'href': '/period-comparison'
    },
    {
        'key': 'old-gold',
        'title': 'Old Gold Dashboard',
        'desc': 'Customer level old gold exchange and purchase analytics with value, weight and transaction tracking.',
        'module': 'Sales',
        'href': '/old-gold'
    },
    {
        'key': 'mini-nsv',
        'title': 'Mini NSV Dashboard',
        'desc': 'Mobile Friendly NSV monitoring dashboard for quick business tracking.',
        'module': 'Sales',
        'href': '/mini-nsv'
    },
    {
        'key': 'company-snapshot',
        'title': 'Company Snapshot',
        'desc': 'Company-wide D-1 sales summary for MD & ED — KPIs, metal mix, and top products.',
        'module': 'Sales',
        'href': '/company-snapshot'
    },
    {
        'key': 'employee-performance',
        'title': 'Employee Performance Analysis',
        'desc': 'Employee target vs achievement analytics with dynamic scoring and rankings.',
        'module': 'Sales',
        'href': '/employee-performance'
    },
    {
        'key': 'dormant-customer',
        'title': 'Dormant Customer List',
        'desc': 'Dormant customer lookup across active sales records.',
        'module': 'Sales',
        'href': '/dormant-customer'
    },
    {
        'key': 'customer-bucket',
        'title': 'Customer Bucket Analysis',
        'desc': 'Customer bucket lookup based on revenue levels.',
        'module': 'Sales',
        'href': '/customer-bucket'
    },
    {
        'key': 'procurement-sales',
        'title': 'Daily Sales Report',
        'desc': 'MTD target vs achievement analytics across all locations.',
        'module': 'Procurement',
        'href': '/procurement-sales'
    },
    {
        'key': 'vendor-analysis',
        'title': 'Vendor Analysis',
        'desc': 'Comprehensive vendor performance, transaction volume, and metal mix sales analysis with granular subcategory insights.',
        'module': 'Procurement',
        'href': '/vendor-analysis'
    },
    {
        'key': 'inventory-optimization',
        'title': 'Inventory Optimization',
        'desc': 'Counter and subcategory-level stock target analysis compared against dynamic sales velocity and current holdings.',
        'module': 'Inventory',
        'href': '/inventory-optimization'
    },
    {
        'key': 'aging-stock',
        'title': 'Aging Stock Analysis',
        'desc': 'Operational inventory aging analysis with dynamic stock shelf-life tracking and slow-moving items metrics.',
        'module': 'Inventory',
        'href': '/aging-stock'
    },
    {
        'key': 'stock-movement',
        'title': 'Stock Movement',
        'desc': 'Enterprise stock inward vs sales movement analysis across counters, categories, and subcategories.',
        'module': 'Inventory',
        'href': '/stock-movement'
    },
    {
        'key': 'design-performance',
        'title': 'Design Performance',
        'desc': 'Design code-level performance metrics, weight, revenue, and item tag movement analysis.',
        'module': 'Inventory',
        'href': '/design-performance'
    },
    {
        'key': 'sales-countdown',
        'title': 'Sales Countdown',
        'desc': "Live simulating countdown/accumulation of today's sales for TV & board screens.",
        'module': 'Directors Hub',
        'href': '/sales-countdown'
    },
    {
        'key': 'execution-tracker',
        'title': 'Execution Tracker',
        'desc': 'Real-time task tracking, execution status, and progress metrics across operational departments.',
        'module': 'Execution Tracker',
        'href': '/execution-tracker'
    },
    {
        'key': 'profitability-analysis',
        'title': 'Profitability Analysis',
        'desc': 'Consolidated and multi-month comparison of branch sales, gross profit, and key ratios.',
        'module': 'Accounts',
        'href': '/profitability-analysis'
    },
    {
        'key': 'roas-conversion-analytics',
        'title': 'ROAS & Conversion Analytics',
        'desc': 'Analysis of advertising costs, footfalls, revenue, ACoS, CPF, and RPV.',
        'module': 'Accounts',
        'href': '/roas-conversion-analytics'
    },
    {
        'key': 'dashboard-catalog',
        'title': 'Dashboard Catalog',
        'desc': 'Centralized master registry showing all dynamically discovered dashboards across Orient BI.',
        'module': 'Admin Hub',
        'href': '/dashboard-catalog'
    },
    {
        'key': 'user-settings',
        'title': 'User Settings',
        'desc': 'Manage authorized user profiles, dashboard permissions, modules access, and branch scopes.',
        'module': 'Admin Hub',
        'href': '/user-settings'
    },
    {
        'key': 'sales-countdown-live',
        'title': 'Sales Countdown (Sales)',
        'desc': "Live simulating countdown/accumulation of today's sales for TV & board screens (Sales Department version).",
        'module': 'Sales',
        'href': '/sales-countdown'
    },
    {
        'key': 'live-customer-counter',
        'title': 'Live Customer Counter (Sales)',
        'desc': "Live registered customer counter (Sales Department version).",
        'module': 'Sales',
        'href': '/live-customer-counter'
    }
]




@callback(
    [
        Output("search-dashboards-modal", "is_open"),
        Output("search-dashboards-input", "value")
    ],
    [
        Input("btn-open-search", "n_clicks"),
        Input("btn-close-search", "n_clicks")
    ],
    [
        State("search-dashboards-modal", "is_open")
    ],
    prevent_initial_call=True
)
def toggle_search_modal(open_clicks, close_clicks, is_open):
    if open_clicks or close_clicks:
        return not is_open, ""
    return is_open, ""


@callback(
    Output("search-dashboards-results", "children"),
    Input("search-dashboards-input", "value"),
    prevent_initial_call=False
)
def update_search_results(search_value):
    allowed_dashboards = session.get('dashboards', [])
    allowed_modules = session.get('modules', [])

    if search_value is None:
        search_value = ""

    search_query = search_value.strip().lower()

    results = []
    for db in DASHBOARD_CATALOG:
        # Check permission
        has_access = False
        perm_key = db['key']
        if perm_key == 'sales-countdown-live':
            perm_key = 'sales-countdown'
        elif perm_key == 'live-customer-counter':
            perm_key = 'live-customer'

        if db['key'] == 'execution-tracker':
            has_access = 'execution-tracker' in allowed_modules
        else:
            has_access = perm_key in allowed_dashboards

        if not has_access:
            continue

        # Filter by match
        if (search_query in db['title'].lower()) or (search_query in db['desc'].lower()):
            results.append(db)

    if not results:
        return html.Div(
            "No dashboards found matching your search.",
            style={
                'textAlign': 'center',
                'color': '#8C8476',
                'padding': '20px',
                'fontStyle': 'italic'
            }
        )

    result_components = []
    for db in results:
        result_components.append(
            html.A(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span(db['title'], className="search-result-title"),
                                    html.Span(db['module'], className="search-result-module")
                                ],
                                style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap'}
                            ),
                            html.Div(db['desc'], className="search-result-desc")
                        ],
                        className="search-result-info"
                    ),
                    html.Div("➔", className="search-result-action")
                ],
                href=db['href'],
                target="_blank",
                className="search-result-item"
            )
        )
    return result_components
