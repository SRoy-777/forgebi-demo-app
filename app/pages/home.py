from flask import session
from dash import html, dcc, callback, Output, Input, State, callback_context
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
                dcc.Store(id='home-mould-store', data='default'),

                html.Div(
                    id="default-layout-container",
                    style={'display': 'block'},
                    children=[

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

                # Atelier Theme Toggle Button
                dbc.Button(
                    "✨ Atelier Workspace",
                    id="btn-toggle-mould",
                    className="home-mould-btn",
                    style={
                        'position': 'absolute',
                        'top': '15px',
                        'right': '65px',
                        'fontSize': '12px',
                        'fontWeight': 'bold',
                        'border': '1px solid #C8A04D',
                        'backgroundColor': 'transparent',
                        'color': '#C8A04D',
                        'borderRadius': '20px',
                        'padding': '5px 12px',
                    }
                ),

                # Factory Theme Toggle Button beside Atelier Button
                dbc.Button(
                    "🏭 Factory Workspace",
                    id="btn-toggle-mould-factory",
                    className="home-mould-btn",
                    style={
                        'position': 'absolute',
                        'top': '15px',
                        'right': '215px',
                        'fontSize': '12px',
                        'fontWeight': 'bold',
                        'border': '1px solid #72B095',
                        'backgroundColor': 'transparent',
                        'color': '#72B095',
                        'borderRadius': '20px',
                        'padding': '5px 12px',
                    }
                ),

                # F&B Kitchen Toggle Button
                dbc.Button(
                    "🍳 F&B Kitchen",
                    id="btn-toggle-mould-kitchen",
                    className="home-mould-btn",
                    style={
                        'position': 'absolute',
                        'top': '15px',
                        'right': '375px',
                        'fontSize': '12px',
                        'fontWeight': 'bold',
                        'border': '1px solid #D84315',
                        'backgroundColor': 'transparent',
                        'color': '#D84315',
                        'borderRadius': '20px',
                        'padding': '5px 12px',
                    }
                ),

            html.Br(),

            # ---------------------------------------------------
            # Logo
            # ---------------------------------------------------

            html.Div(
                [
                    # Hidden logo image to satisfy theme callback output without errors
                    html.Img(
                        id='home-logo',
                        src="/assets/orient_logo.png",
                        style={'display': 'none'}
                    ),
                    # Visible typography logo
                    html.Span(
                        "ForgeBI",
                        id="home-logo-text",
                        style={
                            'fontFamily': '"Outfit", sans-serif',
                            'fontSize': '42px',
                            'fontWeight': '800',
                            'color': '#C8A04D',
                            'letterSpacing': '2px',
                            'display': 'inline-block',
                            'marginBottom': '20px'
                        }
                    )
                ],
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

                "ForgeBI Business Intelligence Demo",
                id="home-header-title",
                style={
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                    'color': '#1C1B19'
                }
            ),

            # Tagline / Disclaimer
            html.Div(
                "(Since this is a demo, the dashboards might not show figures as expected)",
                id="home-header-tagline",
                style={
                    'textAlign': 'center',
                    'fontSize': '14px',
                    'fontStyle': 'italic',
                    'color': '#E26D5C',
                    'marginBottom': '10px'
                }
            ),

            # Mouldable Layout Note
            html.Div(
                "Completely mouldable. Don't want this layout? We can change it to however you like.",
                id="home-header-mouldnote",
                style={
                    'textAlign': 'center',
                    'fontSize': '14px',
                    'fontWeight': '500',
                    'color': '#C8A04D',
                    'marginBottom': '45px'
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
                    ]
                ),

                html.Div(
                    id="fashion-layout-container",
                    style={'display': 'none'},
                    className="fashion-layout-wrapper",
                    children=dbc.Row(
                        [
                            # Left Panel Column
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Div("M A I S O N", className="fashion-brand-sup"),
                                        html.Div("ATELIER", className="fashion-brand-main"),
                                        html.Div("ForgeBI OPERATIONAL LEDGER // SS26", className="fashion-brand-sub"),
                                        html.Hr(style={'borderColor': '#D4AF37', 'borderWidth': '1.5px', 'margin': '2rem 0'}),
                                        
                                        html.Div(
                                            [
                                                html.Div([
                                                    html.Span("SEASON SHOWROOM NET REVENUE"),
                                                    html.Strong("₹4.82 Cr")
                                                ], className="fashion-stat-item"),
                                                html.Div([
                                                    html.Span("ACTIVE COLLECTION SKUs"),
                                                    html.Strong("184 Items")
                                                ], className="fashion-stat-item"),
                                                html.Div([
                                                    html.Span("ATELIER PRODUCTION RATE"),
                                                    html.Strong("96.8%")
                                                ], className="fashion-stat-item"),
                                                html.Div([
                                                    html.Span("SUPPLIER LEAD TIME"),
                                                    html.Strong("4.2 Days")
                                                ], className="fashion-stat-item"),
                                            ],
                                            className="fashion-stats-panel"
                                        ),
                                        
                                        html.Div(
                                            [
                                                dbc.Button(
                                                    "💎 Revert Layout",
                                                    id="btn-toggle-mould-fashion",
                                                    className="fashion-control-btn-mould"
                                                ),
                                                dbc.Button(
                                                    "🌙",
                                                    id="btn-toggle-theme-fashion",
                                                    className="fashion-control-btn-theme"
                                                ),
                                            ],
                                            className="fashion-controls-group"
                                        )
                                    ],
                                    className="fashion-left-panel"
                                ),
                                xs=12, md=4
                            ),
                            
                            # Right Catalog Column
                            dbc.Col(
                                html.Div(
                                    [
                                        html.H2("THE COLLECTION INDEX", className="fashion-collection-title"),
                                        
                                        html.Div(
                                            [
                                                # Item 1: Execution Tracker
                                                html.Div(
                                                    [
                                                        html.Span("01 //", className="fashion-number"),
                                                        html.Div([
                                                            html.H5("ATELIER EXECUTION BOARD", className="fashion-title"),
                                                            html.P("Real-time runway launch tracking, milestone targets, and operational status logs.", className="fashion-desc"),
                                                        ], className="fashion-info"),
                                                        html.A("Enter Collection Workspace ➔", href="/execution-tracker", target="_blank", className="fashion-link")
                                                    ],
                                                    className="fashion-row"
                                                ) if 'execution-tracker' in allowed_modules else None,
                                                
                                                # Item 2: Sales
                                                html.Div(
                                                    [
                                                        html.Span("02 //", className="fashion-number"),
                                                        html.Div([
                                                            html.H5("SHOWROOM SALES VELOCITY", className="fashion-title"),
                                                            html.P("Daily conversion metrics, showroom velocity, and basket analysis.", className="fashion-desc"),
                                                        ], className="fashion-info"),
                                                        html.A("Enter Collection Workspace ➔", href="/sales", target="_blank", className="fashion-link")
                                                    ],
                                                    className="fashion-row"
                                                ) if 'sales' in allowed_modules else None,
                                                
                                                # Item 3: Inventory
                                                html.Div(
                                                    [
                                                        html.Span("03 //", className="fashion-number"),
                                                        html.Div([
                                                            html.H5("GARMENT LOGISTICS & AGING", className="fashion-title"),
                                                            html.P("Inventory aging index, collection turn rate, and active supply logs.", className="fashion-desc"),
                                                        ], className="fashion-info"),
                                                        html.A("Enter Collection Workspace ➔", href="/inventory", target="_blank", className="fashion-link")
                                                    ],
                                                    className="fashion-row"
                                                ) if 'inventory' in allowed_modules else None,
                                                
                                                # Item 4: Accounts
                                                html.Div(
                                                    [
                                                        html.Span("04 //", className="fashion-number"),
                                                        html.Div([
                                                            html.H5("MAISON FINANCE & LEDGER", className="fashion-title"),
                                                            html.P("Operational audit, revenue aggregation, and EBITDA forecasts.", className="fashion-desc"),
                                                        ], className="fashion-info"),
                                                        html.A("Enter Collection Workspace ➔", href="/accounts", target="_blank", className="fashion-link")
                                                    ],
                                                    className="fashion-row"
                                                ) if 'accounts' in allowed_modules else None,
                                                
                                                # Item 5: Procurement
                                                html.Div(
                                                    [
                                                        html.Span("05 //", className="fashion-number"),
                                                        html.Div([
                                                            html.H5("FABRICATION & MATERIAL OUTLET", className="fashion-title"),
                                                            html.P("Raw textile orders, supply pipeline, and design materials tracker.", className="fashion-desc"),
                                                        ], className="fashion-info"),
                                                        html.A("Enter Collection Workspace ➔", href="/procurement", target="_blank", className="fashion-link")
                                                    ],
                                                    className="fashion-row"
                                                ) if 'procurement' in allowed_modules else None,
                                                
                                                # Item 6: Marketing
                                                html.Div(
                                                    [
                                                        html.Span("06 //", className="fashion-number"),
                                                        html.Div([
                                                            html.H5("HAUTE COUTURE CAMPAIGNS", className="fashion-title"),
                                                            html.P("Brand engagement levels, social catalog conversions, and CAC auditing.", className="fashion-desc"),
                                                        ], className="fashion-info"),
                                                        html.A("Enter Collection Workspace ➔", href="/marketing", target="_blank", className="fashion-link")
                                                    ],
                                                    className="fashion-row"
                                                ) if 'marketing' in allowed_modules else None,
                                                
                                                # Item 7: Customer Care
                                                html.Div(
                                                    [
                                                        html.Span("07 //", className="fashion-number"),
                                                        html.Div([
                                                            html.H5("CLIENT CARE CONCIERGE", className="fashion-title"),
                                                            html.P("VIP concierge tickets, loyalty conversions, and service speed logs.", className="fashion-desc"),
                                                        ], className="fashion-info"),
                                                        html.A("Enter Collection Workspace ➔", href="/customer-care", target="_blank", className="fashion-link")
                                                    ],
                                                    className="fashion-row"
                                                ) if 'customer-care' in allowed_modules else None,
                                                
                                                # Item 8: HR
                                                html.Div(
                                                    [
                                                        html.Span("08 //", className="fashion-number"),
                                                        html.Div([
                                                            html.H5("ATELIER WORKFORCE & TALENT", className="fashion-title"),
                                                            html.P("Designers payroll overview, attendance rates, and headcount audits.", className="fashion-desc"),
                                                        ], className="fashion-info"),
                                                        html.A("Enter Collection Workspace ➔", href="/hr", target="_blank", className="fashion-link")
                                                    ],
                                                    className="fashion-row"
                                                ) if 'hr' in allowed_modules else None,
                                                
                                                # Item 9: Directors Hub
                                                html.Div(
                                                    [
                                                        html.Span("09 //", className="fashion-number"),
                                                        html.Div([
                                                            html.H5("EXECUTIVE RUNWAY COCKPIT", className="fashion-title"),
                                                            html.P("Consolidated executive turnover, brand KPI index, and global health metrics.", className="fashion-desc"),
                                                        ], className="fashion-info"),
                                                        html.A("Enter Collection Workspace ➔", href="/directors-hub", target="_blank", className="fashion-link")
                                                    ],
                                                    className="fashion-row"
                                                ) if 'directors-hub' in allowed_modules else None,
                                                
                                                # Item 10: Admin Hub
                                                html.Div(
                                                    [
                                                        html.Span("10 //", className="fashion-number"),
                                                        html.Div([
                                                            html.H5("MAISON ANALYTICS CORE SETTINGS", className="fashion-title"),
                                                            html.P("Configure security keys, register brand dashboards, and inspect audit logs.", className="fashion-desc"),
                                                        ], className="fashion-info"),
                                                        html.A("Enter Collection Workspace ➔", href="/admin-hub", target="_blank", className="fashion-link")
                                                    ],
                                                    className="fashion-row"
                                                ) if 'admin-hub' in allowed_modules else None,
                                            ],
                                            className="fashion-catalog-list"
                                        )
                                    ],
                                    className="fashion-right-panel"
                                ),
                                xs=12, md=8
                            )
                        ]
                    )
                ),

                html.Div(
                    id="factory-layout-container",
                    style={'display': 'none'},
                    className="factory-layout-wrapper",
                    children=dbc.Row(
                        [
                            # Left Column: Telemetry Billboard
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Div("SYSTEM CORE", className="factory-tag"),
                                        html.Div("FORGE_IND", className="factory-brand-main"),
                                        html.Div("INDUSTRIAL HUD CONSOLE v2.6", className="factory-brand-sub"),
                                        html.Hr(style={'borderColor': '#00E676', 'borderWidth': '1px', 'margin': '1.5rem 0'}),
                                        
                                        html.Div(
                                            [
                                                html.Div([
                                                    html.Span("OEE (EQUIPMENT EFFECTIVENESS)"),
                                                    html.Strong("87.4%"),
                                                    html.Div(className="factory-progress-bar", children=html.Div(className="factory-progress-fill", style={'width': '87.4%'}))
                                                ], className="factory-telemetry-item"),
                                                html.Div([
                                                    html.Span("ACTIVE ASSEMBLY LINES"),
                                                    html.Strong("8 / 8 ACTIVE"),
                                                    html.Div(className="factory-progress-bar", children=html.Div(className="factory-progress-fill", style={'width': '100%'}))
                                                ], className="factory-telemetry-item"),
                                                html.Div([
                                                    html.Span("DAILY TARGET PROGRESS"),
                                                    html.Strong("3,842 / 4,820 Unit"),
                                                    html.Div(className="factory-progress-bar", children=html.Div(className="factory-progress-fill", style={'width': '79.7%'}))
                                                ], className="factory-telemetry-item"),
                                                html.Div([
                                                    html.Span("FLOOR INCIDENT RECORD"),
                                                    html.Strong("420 DAYS CLEAR"),
                                                ], className="factory-telemetry-item"),
                                            ],
                                            className="factory-telemetry-panel"
                                        ),
                                        
                                        html.Div(
                                            [
                                                dbc.Button(
                                                    "🔌 Return to Control Core",
                                                    id="btn-toggle-mould-factory-back",
                                                    className="factory-control-btn me-2"
                                                ),
                                                dbc.Button(
                                                    "🌙",
                                                    id="btn-toggle-theme-factory",
                                                    className="factory-control-btn-theme"
                                                ),
                                            ],
                                            className="factory-controls-group"
                                        )
                                    ],
                                    className="factory-left-panel"
                                ),
                                xs=12, md=3
                            ),
                            
                            # Center Column: Operations Hub Cards
                            dbc.Col(
                                html.Div(
                                    [
                                        html.H3("MACHINERY & CONTROL MODULES", className="factory-section-title"),
                                        dbc.Row(
                                            [
                                                # Module 1: Execution Tracker -> Assembly Line Status
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div("SYS_NODE_01", className="factory-node-id"),
                                                            html.H4("⚙️ Assembly Line Status", className="factory-card-title"),
                                                            html.P("Monitor floor tasks, active workflow backlogs, and target speeds.", className="factory-card-desc"),
                                                            html.A(dbc.Button("LAUNCH CONSOLE", className="factory-card-btn"), href="/execution-tracker", target="_blank")
                                                        ],
                                                        className="factory-card"
                                                    ),
                                                    xs=12, sm=6, md=6, lg=4
                                                ) if 'execution-tracker' in allowed_modules else None,
                                                
                                                # Module 2: Inventory -> Parts Inventory
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div("SYS_NODE_02", className="factory-node-id"),
                                                            html.H4("📦 Logistics & Inventory", className="factory-card-title"),
                                                            html.P("Raw material stock counts, shipping orders, and turnaround index.", className="factory-card-desc"),
                                                            html.A(dbc.Button("LAUNCH CONSOLE", className="factory-card-btn"), href="/inventory", target="_blank")
                                                        ],
                                                        className="factory-card"
                                                    ),
                                                    xs=12, sm=6, md=6, lg=4
                                                ) if 'inventory' in allowed_modules else None,
                                                
                                                # Module 3: Procurement -> Material Inputs
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div("SYS_NODE_03", className="factory-node-id"),
                                                            html.H4("🏭 Material Raw Inputs", className="factory-card-title"),
                                                            html.P("Fabrication vendor lead times, quality audits, and procurement logs.", className="factory-card-desc"),
                                                            html.A(dbc.Button("LAUNCH CONSOLE", className="factory-card-btn"), href="/procurement", target="_blank")
                                                        ],
                                                        className="factory-card"
                                                    ),
                                                    xs=12, sm=6, md=6, lg=4
                                                ) if 'procurement' in allowed_modules else None,

                                                # Module 4: Sales -> Showroom Velocity
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div("SYS_NODE_04", className="factory-node-id"),
                                                            html.H4("📊 Showroom Sales Velocity", className="factory-card-title"),
                                                            html.P("Shipment distributions, dealer purchase conversions, and revenue analysis.", className="factory-card-desc"),
                                                            html.A(dbc.Button("LAUNCH CONSOLE", className="factory-card-btn"), href="/sales", target="_blank")
                                                        ],
                                                        className="factory-card"
                                                    ),
                                                    xs=12, sm=6, md=6, lg=4
                                                ) if 'sales' in allowed_modules else None,

                                                # Module 5: Accounts -> Costing Analysis
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div("SYS_NODE_05", className="factory-node-id"),
                                                            html.H4("📉 Ledger & Cost Analysis", className="factory-card-title"),
                                                            html.P("Operation expenditures, asset audits, and operational EBITDA ledger.", className="factory-card-desc"),
                                                            html.A(dbc.Button("LAUNCH CONSOLE", className="factory-card-btn"), href="/accounts", target="_blank")
                                                        ],
                                                        className="factory-card"
                                                    ),
                                                    xs=12, sm=6, md=6, lg=4
                                                ) if 'accounts' in allowed_modules else None,

                                                # Module 6: Directors Hub -> Control Room
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div("SYS_NODE_06", className="factory-node-id"),
                                                            html.H4("🎛️ Control Room Telemetry", className="factory-card-title"),
                                                            html.P("Consolidated operation scorecards, global factory KPI dials.", className="factory-card-desc"),
                                                            html.A(dbc.Button("LAUNCH CONSOLE", className="factory-card-btn"), href="/directors-hub", target="_blank")
                                                        ],
                                                        className="factory-card"
                                                    ),
                                                    xs=12, sm=6, md=6, lg=4
                                                ) if 'directors-hub' in allowed_modules else None,
                                            ]
                                        )
                                    ],
                                    className="factory-center-panel"
                                ),
                                xs=12, md=6
                            ),
                            
                            # Right Column: System Terminal Logs
                            dbc.Col(
                                html.Div(
                                    [
                                        html.H3("LIVE CONSOLE LOGGER", className="factory-section-title"),
                                        html.Div(
                                            [
                                                html.Div(">> INITIATING SYSTEM TELEMETRY...", className="factory-log-line green"),
                                                html.Div(">> NODE_01: ONLINE [ASSEMBLY_LINE_STATUS]", className="factory-log-line"),
                                                html.Div(">> NODE_02: ONLINE [LOGISTICS_PARTS_INVENTORY]", className="factory-log-line"),
                                                html.Div(">> NODE_03: ONLINE [MATERIAL_RAW_INPUTS]", className="factory-log-line"),
                                                html.Div(">> 00:36:12 - LINE 1: ASSEMBLY CYCLE COMPLETED", className="factory-log-line"),
                                                html.Div(">> 00:41:45 - LINE 3: PARTS STOCK VERIFIED", className="factory-log-line"),
                                                html.Div(">> 00:48:02 - OUTLET 2: PACKAGING BUNDLE LOCKED", className="factory-log-line"),
                                                html.Div(">> 00:52:10 - LOGISTICS: FREIGHT TRANSIT DEPLOYED", className="factory-log-line orange"),
                                                html.Div(">> 00:55:18 - LINE 2: OEE RATE CALIBRATED [87.4%]", className="factory-log-line green"),
                                                html.Div(">> 01:02:40 - ASSEMBLY: TARGET LEVEL 79.7% REACHED", className="factory-log-line"),
                                                html.Div(">> 01:05:12 - SAFETY SENSORS: NOMINAL STABILITY", className="factory-log-line green"),
                                                html.Div(">> 01:10:04 - DATABASE SNAPSHOT UPLOAD SUCCESSFUL", className="factory-log-line green"),
                                                html.Div(">> SYSTEM RUNNING IN STEADY STATE...", className="factory-log-line green blinking"),
                                            ],
                                            className="factory-terminal-logs"
                                        )
                                    ],
                                    className="factory-right-panel"
                                ),
                                xs=12, md=3
                            )
                        ]
                    )
                ),

                html.Div(
                    id="kitchen-layout-container",
                    style={'display': 'none'},
                    className="kitchen-layout-wrapper",
                    children=dbc.Row(
                        [
                            # Left Column: Bistro Sidebar Panel
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Div("FORGE KITCHEN", className="kitchen-brand-main"),
                                        html.Div("F&B OPERATIONS CONSOLE // ACTIVE", className="kitchen-brand-sub"),
                                        html.Hr(style={'borderColor': '#E65100', 'borderWidth': '1px', 'margin': '1.5rem 0'}),
                                        
                                        html.Div(
                                            [
                                                html.Div([
                                                    html.Span("🍳 LIVE STATIONS ACTIVE"),
                                                    html.Strong("142 Orders")
                                                ], className="kitchen-stat-item"),
                                                html.Div([
                                                    html.Span("⏱️ AVERAGE PREPARATION TIME"),
                                                    html.Strong("12.4 Mins")
                                                ], className="kitchen-stat-item"),
                                                html.Div([
                                                    html.Span("⭐ CLIENT SATISFACTION (CSAT)"),
                                                    html.Strong("94.6%")
                                                ], className="kitchen-stat-item"),
                                                html.Div([
                                                    html.Span("🌾 WASTE REDUCTION INDEX"),
                                                    html.Strong("98.2%")
                                                ], className="kitchen-stat-item"),
                                            ],
                                            className="kitchen-stats-panel"
                                        ),
                                        
                                        html.Div(
                                            [
                                                dbc.Button(
                                                    "🍳 Return to Kitchen Core",
                                                    id="btn-toggle-mould-kitchen-back",
                                                    className="kitchen-control-btn me-2"
                                                ),
                                                dbc.Button(
                                                    "🌙",
                                                    id="btn-toggle-theme-kitchen",
                                                    className="kitchen-control-btn-theme"
                                                ),
                                            ],
                                            className="kitchen-controls-group"
                                        )
                                    ],
                                    className="kitchen-left-panel"
                                ),
                                xs=12, md=3
                            ),
                            
                            # Right Column: Kitchen Station Board
                            dbc.Col(
                                html.Div(
                                    [
                                        html.H3("ACTIVE KITCHEN STATIONS", className="kitchen-section-title"),
                                        dbc.Row(
                                            [
                                                # Station 1: Sourcing (Procurement)
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div("STATION // 01", className="kitchen-station-id"),
                                                            html.H4("🌾 Pantry Sourcing", className="kitchen-card-title"),
                                                            html.P("Ingredient suppliers lead times, fresh stock orders, and quality logs.", className="kitchen-card-desc"),
                                                            html.A(dbc.Button("OPEN STATION", className="kitchen-card-btn"), href="/procurement", target="_blank")
                                                        ],
                                                        className="kitchen-card"
                                                    ),
                                                    xs=12, sm=6, md=6, lg=4
                                                ) if 'procurement' in allowed_modules else None,
                                                
                                                # Station 2: Stock (Inventory)
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div("STATION // 02", className="kitchen-station-id"),
                                                            html.H4("🥩 Cold Storage & Stock", className="kitchen-card-title"),
                                                            html.P("Cold room inventory counts, stock expiration tracking, and buffer limits.", className="kitchen-card-desc"),
                                                            html.A(dbc.Button("OPEN STATION", className="kitchen-card-btn"), href="/inventory", target="_blank")
                                                        ],
                                                        className="kitchen-card"
                                                    ),
                                                    xs=12, sm=6, md=6, lg=4
                                                ) if 'inventory' in allowed_modules else None,
                                                
                                                # Station 3: Tickets (Execution Tracker)
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div("STATION // 03", className="kitchen-station-id"),
                                                            html.H4("👨‍🍳 Kitchen Prep Ticket Line", className="kitchen-card-title"),
                                                            html.P("Active prep sheets, chefs workstation assignment, and launch milestones.", className="kitchen-card-desc"),
                                                            html.A(dbc.Button("OPEN STATION", className="kitchen-card-btn"), href="/execution-tracker", target="_blank")
                                                        ],
                                                        className="kitchen-card"
                                                    ),
                                                    xs=12, sm=6, md=6, lg=4
                                                ) if 'execution-tracker' in allowed_modules else None,

                                                # Station 4: Revenue (Accounts)
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div("STATION // 04", className="kitchen-station-id"),
                                                            html.H4("💰 Buffet Cost & Revenue", className="kitchen-card-title"),
                                                            html.P("Daily ledger audits, restaurant cost margins, and recipe EBITDA index.", className="kitchen-card-desc"),
                                                            html.A(dbc.Button("OPEN STATION", className="kitchen-card-btn"), href="/accounts", target="_blank")
                                                        ],
                                                        className="kitchen-card"
                                                    ),
                                                    xs=12, sm=6, md=6, lg=4
                                                ) if 'accounts' in allowed_modules else None,

                                                # Station 5: POS Logs (Sales)
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div("STATION // 05", className="kitchen-station-id"),
                                                            html.H4("🍔 POS Order Logs", className="kitchen-card-title"),
                                                            html.P("Table bills summary, MTD sales comparisons, and checkout velocity.", className="kitchen-card-desc"),
                                                            html.A(dbc.Button("OPEN STATION", className="kitchen-card-btn"), href="/sales", target="_blank")
                                                        ],
                                                        className="kitchen-card"
                                                    ),
                                                    xs=12, sm=6, md=6, lg=4
                                                ) if 'sales' in allowed_modules else None,

                                                # Station 6: Group Cockpit (Directors Hub)
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            html.Div("STATION // 06", className="kitchen-station-id"),
                                                            html.H4("🍷 Restaurant Group Cockpit", className="kitchen-card-title"),
                                                            html.P("Aggregated franchisee scorecards and global hospitality indicators.", className="kitchen-card-desc"),
                                                            html.A(dbc.Button("OPEN STATION", className="kitchen-card-btn"), href="/directors-hub", target="_blank")
                                                        ],
                                                        className="kitchen-card"
                                                    ),
                                                    xs=12, sm=6, md=6, lg=4
                                                ) if 'directors-hub' in allowed_modules else None,
                                            ]
                                        )
                                    ],
                                    className="kitchen-right-panel"
                                ),
                                xs=12, md=9
                            )
                        ]
                    )
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
                        html.Small("ForgeBI Authorized Session", className='text-muted d-block text-center mt-1'),
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
        <p style="font-size: 11px; color: #777; margin-bottom: 0;">Sent automatically via ForgeBI Security System.</p>
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
# Theme & Mould Toggle Callback
# ---------------------------------------------------

@callback(
    Output("home-layout-wrapper", "className"),
    Output("btn-toggle-theme", "children"),
    Output("btn-toggle-theme-fashion", "children"),
    Output("btn-toggle-theme-factory", "children"),
    Output("btn-toggle-theme-kitchen", "children"),
    Output("home-theme-store", "data"),
    Output("home-logo", "src"),
    Output("search-dashboards-modal", "contentClassName"),
    Output("home-mould-store", "data"),
    Output("btn-toggle-mould", "children"),
    Output("btn-toggle-mould-fashion", "children"),
    Output("btn-toggle-mould-factory", "children"),
    Output("btn-toggle-mould-factory-back", "children"),
    Output("btn-toggle-mould-kitchen", "children"),
    Output("btn-toggle-mould-kitchen-back", "children"),
    Output("default-layout-container", "style"),
    Output("fashion-layout-container", "style"),
    Output("factory-layout-container", "style"),
    Output("kitchen-layout-container", "style"),
    Output("home-header-title", "children"),
    Output("home-header-tagline", "children"),
    Output("home-header-mouldnote", "children"),
    Output("home-logo-text", "children"),
    Input("btn-toggle-theme", "n_clicks"),
    Input("btn-toggle-theme-fashion", "n_clicks"),
    Input("btn-toggle-theme-factory", "n_clicks"),
    Input("btn-toggle-theme-kitchen", "n_clicks"),
    Input("btn-toggle-mould", "n_clicks"),
    Input("btn-toggle-mould-fashion", "n_clicks"),
    Input("btn-toggle-mould-factory", "n_clicks"),
    Input("btn-toggle-mould-factory-back", "n_clicks"),
    Input("btn-toggle-mould-kitchen", "n_clicks"),
    Input("btn-toggle-mould-kitchen-back", "n_clicks"),
    State("home-theme-store", "data"),
    State("home-mould-store", "data"),
    prevent_initial_call=True
)
def handle_workspace_controls(theme_clicks, theme_fashion_clicks, theme_factory_clicks, theme_kitchen_clicks, mould_clicks, mould_fashion_clicks, mould_factory_clicks, mould_factory_back_clicks, mould_kitchen_clicks, mould_kitchen_back_clicks, current_theme, current_mould):
    from dash import callback_context
    ctx = callback_context
    if not ctx.triggered:
        return (
            "inv-premium-page-gold", "🌙", "🌙", "🌙", "🌙", "light", 
            "/assets/orient_logo.png", "search-modal-content-light",
            "default", "✨ Atelier Workspace", "💎 Revert Layout", "🏭 Factory Workspace", "🔌 Return to Control Core", "🍳 F&B Kitchen", "🍳 Return to Kitchen Core",
            {'display': 'block'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'},
            "ForgeBI Business Intelligence Demo",
            "(Since this is a demo, the dashboards might not show figures as expected)",
            "Completely mouldable. Don't want this layout? We can change it to however you like.",
            "ForgeBI"
        )
        
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    new_theme = current_theme
    new_mould = current_mould
    
    # Theme Toggles
    if trigger_id in ["btn-toggle-theme", "btn-toggle-theme-fashion", "btn-toggle-theme-factory", "btn-toggle-theme-kitchen"]:
        new_theme = "dark" if current_theme == "light" else "light"
        
    # Workspace Layout Toggles
    elif trigger_id == "btn-toggle-mould":
        new_mould = "fashion"
    elif trigger_id == "btn-toggle-mould-fashion":
        new_mould = "default"
    elif trigger_id == "btn-toggle-mould-factory":
        new_mould = "factory"
    elif trigger_id == "btn-toggle-mould-factory-back":
        new_mould = "default"
    elif trigger_id == "btn-toggle-mould-kitchen":
        new_mould = "kitchen"
    elif trigger_id == "btn-toggle-mould-kitchen-back":
        new_mould = "default"
        
    # Build className
    wrapper_class = "inv-premium-page-gold" if new_theme == "light" else "inv-premium-page-gold-dark"
    if new_mould == "fashion":
        wrapper_class += " fashion-workspace"
    elif new_mould == "factory":
        wrapper_class += " factory-workspace"
    elif new_mould == "kitchen":
        wrapper_class += " kitchen-workspace"
        
    theme_btn_label = "🌙" if new_theme == "light" else "☀️"
    logo_src = "/assets/orient_logo.png" if new_theme == "light" else "/assets/orient_logo_for_dark_theme.png"
    modal_class = "search-modal-content-light" if new_theme == "light" else "search-modal-content-dark"
    
    # Styles for containers
    default_style = {'display': 'none'}
    fashion_style = {'display': 'none'}
    factory_style = {'display': 'none'}
    kitchen_style = {'display': 'none'}
    
    if new_mould == "fashion":
        fashion_style = {'display': 'block'}
    elif new_mould == "factory":
        factory_style = {'display': 'block'}
    elif new_mould == "kitchen":
        kitchen_style = {'display': 'block'}
    else:
        default_style = {'display': 'block'}
        
    title = "ForgeBI Business Intelligence Demo"
    tagline = "(Since this is a demo, the dashboards might not show figures as expected)"
    mouldnote = "Completely mouldable. Don't want this layout? We can change it to however you like."
    logo_text = "ForgeBI"
    
    if new_mould == "fashion":
        title = "ATELIER ForgeBI // Executive Analytics Hub"
        tagline = "(Demo Mode - Showroom metrics and ledger updates are simulated)"
        mouldnote = "Bespoke Workspace. Custom editorial styling mapped to your brand's digital ecosystem."
        logo_text = "ATELIER"
    elif new_mould == "factory":
        title = "FORGE INDUSTRIAL // CORE CONSOLE"
        tagline = "(SYSTEM TELEMETRY - Simulated Factory Run Logs)"
        mouldnote = "Industrial HUD Console. Engineered for high-throughput floor management and real-time operations."
        logo_text = "FORGE_IND"
    elif new_mould == "kitchen":
        title = "FORGE KITCHEN // F&B HUB"
        tagline = "(KITCHEN OPERATIONS - Real-Time Station Preparation Speeds)"
        mouldnote = "Food & Beverage Station Console. Configured for culinary chain workflows, cost margin audits, and logistics."
        logo_text = "FORGE_FB"
        
    return (
        wrapper_class, theme_btn_label, theme_btn_label, theme_btn_label, theme_btn_label, new_theme, 
        logo_src, modal_class, new_mould, "✨ Atelier Workspace", "💎 Revert Layout", "🏭 Factory Workspace", "🔌 Return to Control Core", "🍳 F&B Kitchen", "🍳 Return to Kitchen Core",
        default_style, fashion_style, factory_style, kitchen_style, title, tagline, mouldnote, logo_text
    )


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
        'desc': 'Centralized master registry showing all dynamically discovered dashboards across ForgeBI.',
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
