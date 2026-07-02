from flask import session
from dash import (
    html,
    dcc,
    callback,
    Input,
    Output,
    State,
    MATCH,
    ALL,
    callback_context
)
import json
import pandas as pd
import dash_bootstrap_components as dbc
from datetime import datetime

from backend.services.admin_hub.user_settings_service import (
    load_initial_users,
    get_location_options,
    get_catalog_options,
    download_production_user_access,
    save_and_sync_production_user_access,
    log_audit,
    validate_user_data
)


# Load metadata options dynamically
INITIAL_USERS = load_initial_users()
DB_OPTS, MOD_OPTS = get_catalog_options()
LOC_OPTS = get_location_options()

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

def build_kpi_section(total_users, active_users, total_modules, total_dashboards):
    cards = [
        dbc.Col(create_kpi_card('Total Users', total_users), xs=6, sm=3, md=3, lg=3, className='mb-2'),
        dbc.Col(create_kpi_card('Active Users', active_users), xs=6, sm=3, md=3, lg=3, className='mb-2'),
        dbc.Col(create_kpi_card('Total Modules Assigned', total_modules), xs=6, sm=3, md=3, lg=3, className='mb-2'),
        dbc.Col(create_kpi_card('Total Dashboard Assignments', total_dashboards), xs=6, sm=3, md=3, lg=3, className='mb-2'),
    ]
    return html.Div([
        html.H5(
            'User Access Metrics Summary',
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
# Layout
# ---------------------------------------------------
layout = html.Div(
    className='inv-premium-page-gold',
    children=dbc.Container([
        
        # State Stores
        dcc.Store(id='users-store', data=INITIAL_USERS, storage_type='memory'),
        dcc.Store(id='delete-target-store', data=None),
        dcc.Download(id='user-settings-download'),
        
        # Success Alert Container
        html.Div(id='settings-alert-container', style={'position': 'fixed', 'top': '25px', 'right': '25px', 'zIndex': 9999}),

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
                    'User Settings',
                    className='fw-bold mt-3 mb-1',
                    style={'fontFamily': 'Outfit'}
                ),
            ], width=7),

            dbc.Col([
                html.Div(
                    f"Last Updated : {LATEST_REFRESH}",
                    className='text-end fw-bold mb-2',
                    style={'color': '#5C4D32', 'fontFamily': 'Outfit'},
                ),
                html.Div([
                    dbc.Button(
                        'Add User',
                        id='btn-add-user-trigger',
                        className='inv-btn-gold px-3 py-1 me-2 shadow-sm fw-bold',
                        size='sm',
                    ),
                    dbc.Button(
                        'Export Data',
                        id='users-export-btn',
                        className='inv-btn-dark px-3 py-1 me-2 shadow-sm',
                        size='sm',
                    ),
                    dbc.Button(
                        'Enter',
                        id='users-enter-btn',
                        className='inv-btn-gold px-3 py-1 shadow-sm',
                        size='sm',
                    ),
                ], className='text-end'),
            ], width=5),
        ], className='mb-4 mt-2 align-items-end'),

        # Filters Card
        dbc.Card(
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Email Search", className="fw-bold mb-1 small text-muted"),
                        dbc.Input(
                            id='user-email-search',
                            type='text',
                            placeholder='Search by email address...',
                            className='w-100',
                            style={'height': '38px', 'fontSize': '13px'}
                        )
                    ], xs=12, md=3),

                    dbc.Col([
                        html.Label("Module Filter", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='user-module-filter',
                            options=MOD_OPTS,
                            placeholder='Select Module(s)',
                            multi=True,
                            className='w-100',
                        )
                    ], xs=12, md=3),

                    dbc.Col([
                        html.Label("Dashboard Filter", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='user-dashboard-filter',
                            options=DB_OPTS,
                            placeholder='Select Dashboard(s)',
                            multi=True,
                            className='w-100',
                        )
                    ], xs=12, md=3),

                    dbc.Col([
                        html.Label("Location Filter", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='user-location-filter',
                            options=LOC_OPTS,
                            placeholder='Select Location(s)',
                            multi=True,
                            className='w-100',
                        )
                    ], xs=12, md=3),
                ]),
            ]),
            className='inv-gold-card mb-4',
        ),

        # Metrics KPI block
        html.Div(id='users-kpi-container'),
        
        # User Table block
        dcc.Loading(
            html.Div(id='users-table-container'),
            type='circle',
        ),

        # Add User Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Add New Authorized User", className="fw-bold")),
            dbc.ModalBody([
                dbc.Label("Email Address", className="fw-bold small"),
                dbc.Input(id="add-user-email", type="email", placeholder="Enter email address...", className="mb-3"),
                
                dbc.Label("Password", className="fw-bold small"),
                dbc.Input(id="add-user-password", type="password", placeholder="Enter login password...", className="mb-3"),
                
                dbc.Label("Assign Modules", className="fw-bold small"),
                dcc.Dropdown(
                    id="add-user-modules",
                    options=MOD_OPTS,
                    multi=True,
                    placeholder="Select allowed module(s)...",
                    className="mb-3"
                ),
                
                dbc.Label("Assign Dashboards", className="fw-bold small"),
                dcc.Dropdown(
                    id="add-user-dashboards",
                    options=DB_OPTS,
                    multi=True,
                    placeholder="Select allowed dashboard(s)...",
                    className="mb-3"
                ),
                
                dbc.Label("Assign Locations Scope", className="fw-bold small"),
                dcc.Dropdown(
                    id="add-user-locations",
                    options=LOC_OPTS,
                    multi=True,
                    placeholder="Select branch scope(s)...",
                    className="mb-3"
                ),
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="add-user-cancel", color="secondary", className="me-2", size="sm"),
                dbc.Button("Save User", id="add-user-save", color="warning", className="fw-bold", size="sm")
            ])
        ], id="add-user-modal", is_open=False),

        # Edit User Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Edit Authorized User Settings", className="fw-bold")),
            dbc.ModalBody([
                dbc.Label("Email Address (Primary Key)", className="fw-bold small"),
                dbc.Input(id="edit-user-email", type="email", disabled=True, className="mb-3"),
                
                dbc.Label("Password", className="fw-bold small"),
                dbc.Input(id="edit-user-password", type="text", placeholder="Enter login password...", className="mb-3"),
                
                dbc.Label("Assign Modules", className="fw-bold small"),
                dcc.Dropdown(
                    id="edit-user-modules",
                    options=MOD_OPTS,
                    multi=True,
                    placeholder="Select allowed module(s)...",
                    className="mb-3"
                ),
                
                dbc.Label("Assign Dashboards", className="fw-bold small"),
                dcc.Dropdown(
                    id="edit-user-dashboards",
                    options=DB_OPTS,
                    multi=True,
                    placeholder="Select allowed dashboard(s)...",
                    className="mb-3"
                ),
                
                dbc.Label("Assign Locations Scope", className="fw-bold small"),
                dcc.Dropdown(
                    id="edit-user-locations",
                    options=LOC_OPTS,
                    multi=True,
                    placeholder="Select branch scope(s)...",
                    className="mb-3"
                ),
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="edit-user-cancel", color="secondary", className="me-2", size="sm"),
                dbc.Button("Save Changes", id="edit-user-save", color="warning", className="fw-bold", size="sm")
            ])
        ], id="edit-user-modal", is_open=False),

        # Delete Confirm Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Confirm Deletion", className="fw-bold text-danger")),
            dbc.ModalBody(
                html.Div(id="delete-user-msg", className="fw-semibold")
            ),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="delete-user-cancel", color="secondary", className="me-2", size="sm"),
                dbc.Button("Yes, Delete", id="delete-user-confirm", color="danger", className="fw-bold", size="sm")
            ])
        ], id="delete-confirm-modal", is_open=False)

    ], fluid=True, style={'padding': '0px'})
)

# ---------------------------------------------------
# Table Loader & Search Filter Callback
# ---------------------------------------------------
@callback(
    Output('users-table-container', 'children'),
    Output('users-kpi-container', 'children'),
    Input('users-store', 'data'),
    Input('users-enter-btn', 'n_clicks'),
    State('user-email-search', 'value'),
    State('user-module-filter', 'value'),
    State('user-dashboard-filter', 'value'),
    State('user-location-filter', 'value'),
)
def render_users_table(users_data, n_clicks, email_search, selected_modules, selected_dashboards, selected_locations):
    df = pd.DataFrame(users_data)
    if df.empty:
        df = pd.DataFrame(columns=['email', 'password', 'module', 'dashboards', 'locations'])
        
    # Apply Email search filter
    if email_search:
        df = df[df['email'].str.lower().str.contains(email_search.strip().lower(), na=False)]
        
    # Apply Module selection filter
    if selected_modules:
        mask = df['module'].apply(lambda x: any(m.strip() in selected_modules for m in str(x).split(',')) if pd.notna(x) else False)
        df = df[mask]
        
    # Apply Dashboard selection filter
    if selected_dashboards:
        mask = df['dashboards'].apply(lambda x: any(db.strip() in selected_dashboards for db in str(x).split(',')) if pd.notna(x) else False)
        df = df[mask]
        
    # Apply Locations selection filter (respects RLS 'ALL' access)
    if selected_locations:
        def loc_match(loc_str):
            if pd.isna(loc_str):
                return False
            user_locs = [l.strip() for l in str(loc_str).split(',')]
            if 'ALL' in user_locs:
                return True
            return any(l in selected_locations for l in user_locs)
        df = df[df['locations'].apply(loc_match)]
        
    # Compile KPIs
    total_users = len(df)
    active_users = len(df[df['password'].str.strip() != ''])
    
    total_modules_assigned = 0
    for mods in df['module'].dropna():
        total_modules_assigned += len([m for m in str(mods).split(',') if m.strip()])
        
    total_dashboards_assigned = 0
    for dbs in df['dashboards'].dropna():
        total_dashboards_assigned += len([d for d in str(dbs).split(',') if d.strip()])
        
    kpi_layout = build_kpi_section(
        total_users=total_users,
        active_users=active_users,
        total_modules=total_modules_assigned,
        total_dashboards=total_dashboards_assigned
    )
    
    # Construct rows
    table_rows = []
    for _, row in df.iterrows():
        email = row['email']
        table_rows.append(
            html.Tr([
                html.Td(email, className='fw-semibold text-break'),
                html.Td('••••••••', style={'letterSpacing': '2px'}),
                html.Td(", ".join([m.strip() for m in str(row['module']).split(',') if m.strip()])),
                html.Td(", ".join([d.strip() for d in str(row['dashboards']).split(',') if d.strip()]), style={'fontSize': '12px'}),
                html.Td(", ".join([l.strip() for l in str(row['locations']).split(',') if l.strip()])),
                html.Td([
                    dbc.Button(
                        "✏️ Edit",
                        id={'type': 'edit-user-btn', 'index': email},
                        color="warning",
                        size="sm",
                        className="me-2 px-2 py-1",
                        style={'fontSize': '11px', 'fontWeight': '600'}
                    ),
                    dbc.Button(
                        "🗑️ Delete",
                        id={'type': 'delete-user-btn', 'index': email},
                        color="danger",
                        size="sm",
                        className="px-2 py-1",
                        style={'fontSize': '11px', 'fontWeight': '600'}
                    )
                ], style={'whiteSpace': 'nowrap', 'textAlign': 'center'})
            ])
        )
        
    if not table_rows:
        table_body = html.Tbody([
            html.Tr([
                html.Td("No users found matching current filters.", colSpan=6, className="text-center text-muted py-4 font-italic")
            ])
        ])
    else:
        table_body = html.Tbody(table_rows)
        
    table_layout = dbc.Card([
        dbc.CardHeader(
            html.H5(
                "Authorized Users List",
                className='fw-bold mb-0',
                style={'textAlign': 'left', 'color': '#1C1B19', 'fontFamily': 'Outfit'},
            ),
            style={'backgroundColor': '#FAF9F6', 'borderBottom': '1px solid #E8DFCE'},
        ),
        dbc.CardBody(
            dbc.Table(
                [
                    html.Thead(
                        html.Tr([
                            html.Th("Email"),
                            html.Th("Password"),
                            html.Th("Assigned Modules"),
                            html.Th("Assigned Dashboards"),
                            html.Th("Locations Scope"),
                            html.Th("Actions", style={'textAlign': 'center', 'width': '150px'})
                        ], style={'backgroundColor': '#1C1B19', 'color': '#C5A059'})
                    ),
                    table_body
                ],
                bordered=True,
                hover=True,
                responsive=True,
                striped=True,
                style={'backgroundColor': '#FFFFFF', 'color': '#1C1B19', 'fontSize': '13px'}
            ),
            style={'padding': '6px', 'overflowX': 'auto'},
        )
    ], className='inv-gold-card mb-4')
    
    return table_layout, kpi_layout

# ---------------------------------------------------
# Unified User Actions Callback
# ---------------------------------------------------
@callback(
    Output('add-user-modal', 'is_open'),
    Output('edit-user-modal', 'is_open'),
    Output('delete-confirm-modal', 'is_open'),
    Output('add-user-email', 'value'),
    Output('add-user-password', 'value'),
    Output('add-user-modules', 'value'),
    Output('add-user-dashboards', 'value'),
    Output('add-user-locations', 'value'),
    Output('edit-user-email', 'value'),
    Output('edit-user-password', 'value'),
    Output('edit-user-modules', 'value'),
    Output('edit-user-dashboards', 'value'),
    Output('edit-user-locations', 'value'),
    Output('delete-target-store', 'data'),
    Output('delete-user-msg', 'children'),
    Output('users-store', 'data'),
    Output('settings-alert-container', 'children'),
    
    Input('btn-add-user-trigger', 'n_clicks'),
    Input('add-user-cancel', 'n_clicks'),
    Input('add-user-save', 'n_clicks'),
    Input({'type': 'edit-user-btn', 'index': ALL}, 'n_clicks'),
    Input('edit-user-cancel', 'n_clicks'),
    Input('edit-user-save', 'n_clicks'),
    Input({'type': 'delete-user-btn', 'index': ALL}, 'n_clicks'),
    Input('delete-user-cancel', 'n_clicks'),
    Input('delete-user-confirm', 'n_clicks'),
    
    State('add-user-email', 'value'),
    State('add-user-password', 'value'),
    State('add-user-modules', 'value'),
    State('add-user-dashboards', 'value'),
    State('add-user-locations', 'value'),
    State('edit-user-email', 'value'),
    State('edit-user-password', 'value'),
    State('edit-user-modules', 'value'),
    State('edit-user-dashboards', 'value'),
    State('edit-user-locations', 'value'),
    State('delete-target-store', 'data'),
    State('users-store', 'data'),
    State('add-user-modal', 'is_open'),
    State('edit-user-modal', 'is_open'),
    State('delete-confirm-modal', 'is_open'),
    
    prevent_initial_call=True
)
def handle_user_actions(
    add_trigger, add_cancel, add_save,
    edit_triggers, edit_cancel, edit_save,
    delete_triggers, delete_cancel, delete_confirm,
    add_email, add_pass, add_mods, add_dbs, add_locs,
    edit_email, edit_pass, edit_mods, edit_dbs, edit_locs,
    delete_target, current_users,
    add_open, edit_open, delete_open
):
    ctx = callback_context
    if not ctx.triggered:
        return (
            False, False, False,
            "", "", [], [], [],
            "", "", [], [], [],
            None, "", current_users, None
        )
        
    trigger_id = ctx.triggered[0]['prop_id']
    
    # ---------------------------------------------------
    # ADD USER TRIGGERS
    # ---------------------------------------------------
    if 'btn-add-user-trigger' in trigger_id:
        return (
            True, False, False,
            "", "", [], [], [],
            "", "", [], [], [],
            None, "", current_users, None
        )
        
    elif 'add-user-cancel' in trigger_id:
        return (
            False, False, False,
            "", "", [], [], [],
            "", "", [], [], [],
            None, "", current_users, None
        )
        
    elif 'add-user-save' in trigger_id:
        if not add_email or not add_pass:
            alert = dbc.Alert("Email and Password are required.", color="danger", dismissable=True, duration=4000)
            return (
                True, False, False,
                add_email, add_pass, add_mods, add_dbs, add_locs,
                "", "", [], [], [],
                None, "", current_users, alert
            )
            
        # Step 1: Read latest production user_access
        try:
            prod_df = download_production_user_access()
        except Exception as e:
            alert = dbc.Alert(f"Failed to read production user access from R2: {str(e)}", color="danger", dismissable=True, duration=5000)
            return (
                True, False, False,
                add_email, add_pass, add_mods, add_dbs, add_locs,
                "", "", [], [], [],
                None, "", current_users, alert
            )

            
        # Step 3: Apply modifications
        new_row = {
            'email': add_email.strip(),
            'password': add_pass.strip(),
            'module': ",".join(add_mods) if add_mods else "",
            'dashboards': ",".join(add_dbs) if add_dbs else "",
            'locations': ",".join(add_locs) if add_locs else ""
        }
        
        # Check duplicate email in production
        if any(u.lower() == add_email.strip().lower() for u in prod_df['email'].dropna().tolist()):
            alert = dbc.Alert(f"Validation Error: User '{add_email}' already exists in production database.", color="danger", dismissable=True, duration=5000)
            return (
                True, False, False,
                add_email, add_pass, add_mods, add_dbs, add_locs,
                "", "", [], [], [],
                None, "", current_users, alert
            )
            
        prod_df = pd.concat([prod_df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Step 4: Validate data
        validation_errors = validate_user_data(prod_df, DB_OPTS, MOD_OPTS, LOC_OPTS)
        if validation_errors:
            alert = dbc.Alert(html.Div([html.Div(err) for err in validation_errors]), color="danger", dismissable=True)
            return (
                True, False, False,
                add_email, add_pass, add_mods, add_dbs, add_locs,
                "", "", [], [], [],
                None, "", current_users, alert
            )
            
        # Step 5 & 6: Save and sync
        try:
            save_and_sync_production_user_access(prod_df)
        except Exception as e:
            alert = dbc.Alert(f"Failed to save production user access: {str(e)}", color="danger", dismissable=True, duration=5000)
            return (
                True, False, False,
                add_email, add_pass, add_mods, add_dbs, add_locs,
                "", "", [], [], [],
                None, "", current_users, alert
            )
            
        # Audit Log
        log_audit(session.get('email'), "Added User", add_email.strip())
        
        # Display Success Message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success_msg = f"Users Added: 1, Users Updated: 0, Users Deleted: 0 | Timestamp: {timestamp}"
        alert = dbc.Alert(success_msg, color="success", dismissable=True, duration=5000)
        
        updated_users = prod_df.to_dict('records')
        return (
            False, False, False,
            "", "", [], [], [],
            "", "", [], [], [],
            None, "", updated_users, alert
        )
        
    # ---------------------------------------------------
    # EDIT USER TRIGGERS
    # ---------------------------------------------------
    elif 'edit-user-btn' in trigger_id:
        trigger_dict_str = trigger_id.rsplit('.', 1)[0]
        try:
            trigger_dict = json.loads(trigger_dict_str)
            target_email = trigger_dict['index']
        except Exception:
            return (
                False, False, False,
                "", "", [], [], [],
                "", "", [], [], [],
                None, "", current_users, None
            )
            
        user = next((u for u in current_users if u['email'] == target_email), None)
        if not user:
            return (
                False, False, False,
                "", "", [], [], [],
                "", "", [], [], [],
                None, "", current_users, None
            )
            
        user_modules = [m.strip() for m in str(user.get('module', '')).split(',') if m.strip()]
        user_dashboards = [d.strip() for d in str(user.get('dashboards', '')).split(',') if d.strip()]
        user_locations = [l.strip() for l in str(user.get('locations', '')).split(',') if l.strip()]
        
        return (
            False, True, False,
            "", "", [], [], [],
            user['email'], user['password'], user_modules, user_dashboards, user_locations,
            None, "", current_users, None
        )
        
    elif 'edit-user-cancel' in trigger_id:
        return (
            False, False, False,
            "", "", [], [], [],
            "", "", [], [], [],
            None, "", current_users, None
        )
        
    elif 'edit-user-save' in trigger_id:
        if not edit_pass:
            alert = dbc.Alert("Password is required.", color="danger", dismissable=True, duration=4000)
            return (
                False, True, False,
                "", "", [], [], [],
                edit_email, edit_pass, edit_mods, edit_dbs, edit_locs,
                None, "", current_users, alert
            )
            
        # Step 1: Read latest production user_access
        try:
            prod_df = download_production_user_access()
        except Exception as e:
            alert = dbc.Alert(f"Failed to read production user access from R2: {str(e)}", color="danger", dismissable=True, duration=5000)
            return (
                False, True, False,
                "", "", [], [], [],
                edit_email, edit_pass, edit_mods, edit_dbs, edit_locs,
                None, "", current_users, alert
            )

            
        # Step 3: Apply modifications
        idx_match = prod_df['email'].str.lower() == edit_email.strip().lower()
        if not idx_match.any():
            alert = dbc.Alert(f"Error: User '{edit_email}' was not found in production.", color="danger", dismissable=True, duration=5000)
            return (
                False, False, False,
                "", "", [], [], [],
                "", "", [], [], [],
                None, "", prod_df.to_dict('records'), alert
            )
            
        prod_df.loc[idx_match, 'password'] = edit_pass.strip()
        prod_df.loc[idx_match, 'module'] = ",".join(edit_mods) if edit_mods else ""
        prod_df.loc[idx_match, 'dashboards'] = ",".join(edit_dbs) if edit_dbs else ""
        prod_df.loc[idx_match, 'locations'] = ",".join(edit_locs) if edit_locs else ""
        
        # Step 4: Validate
        validation_errors = validate_user_data(prod_df, DB_OPTS, MOD_OPTS, LOC_OPTS)
        if validation_errors:
            alert = dbc.Alert(html.Div([html.Div(err) for err in validation_errors]), color="danger", dismissable=True)
            return (
                False, True, False,
                "", "", [], [], [],
                edit_email, edit_pass, edit_mods, edit_dbs, edit_locs,
                None, "", current_users, alert
            )
            
        # Step 5 & 6: Save and sync
        try:
            save_and_sync_production_user_access(prod_df)
        except Exception as e:
            alert = dbc.Alert(f"Failed to save production user access: {str(e)}", color="danger", dismissable=True, duration=5000)
            return (
                False, True, False,
                "", "", [], [], [],
                edit_email, edit_pass, edit_mods, edit_dbs, edit_locs,
                None, "", current_users, alert
            )
            
        # Audit Log
        log_audit(session.get('email'), "Updated User Settings", edit_email.strip())
        
        # Display Success Message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success_msg = f"Users Added: 0, Users Updated: 1, Users Deleted: 0 | Timestamp: {timestamp}"
        alert = dbc.Alert(success_msg, color="success", dismissable=True, duration=5000)
        
        updated_users = prod_df.to_dict('records')
        return (
            False, False, False,
            "", "", [], [], [],
            "", "", [], [], [],
            None, "", updated_users, alert
        )
        
    # ---------------------------------------------------
    # DELETE USER TRIGGERS
    # ---------------------------------------------------
    elif 'delete-user-btn' in trigger_id:
        trigger_dict_str = trigger_id.rsplit('.', 1)[0]
        try:
            trigger_dict = json.loads(trigger_dict_str)
            target_email = trigger_dict['index']
        except Exception:
            return (
                False, False, False,
                "", "", [], [], [],
                "", "", [], [], [],
                None, "", current_users, None
            )
            
        msg = f"Are you sure you want to permanently delete user '{target_email}'? This action cannot be undone."
        return (
            False, False, True,
            "", "", [], [], [],
            "", "", [], [], [],
            target_email, msg, current_users, None
        )
        
    elif 'delete-user-cancel' in trigger_id:
        return (
            False, False, False,
            "", "", [], [], [],
            "", "", [], [], [],
            None, "", current_users, None
        )
        
    elif 'delete-user-confirm' in trigger_id:
        if not delete_target:
            return (
                False, False, False,
                "", "", [], [], [],
                "", "", [], [], [],
                None, "", current_users, None
            )
            
        # Step 1: Read latest production
        try:
            prod_df = download_production_user_access()
        except Exception as e:
            alert = dbc.Alert(f"Failed to read production user access from R2: {str(e)}", color="danger", dismissable=True, duration=5000)
            return (
                False, False, False,
                "", "", [], [], [],
                "", "", [], [], [],
                delete_target, "", current_users, alert
            )

            
        # Step 3: Apply modifications
        idx_match = prod_df['email'].str.lower() == delete_target.strip().lower()
        if not idx_match.any():
            alert = dbc.Alert(f"Error: User '{delete_target}' was not found in production.", color="danger", dismissable=True, duration=5000)
            return (
                False, False, False,
                "", "", [], [], [],
                "", "", [], [], [],
                None, "", prod_df.to_dict('records'), alert
            )
            
        prod_df = prod_df[~idx_match]
        
        # Step 4: Validate
        validation_errors = validate_user_data(prod_df, DB_OPTS, MOD_OPTS, LOC_OPTS)
        if validation_errors:
            alert = dbc.Alert(html.Div([html.Div(err) for err in validation_errors]), color="danger", dismissable=True)
            return (
                False, False, False,
                "", "", [], [], [],
                "", "", [], [], [],
                None, "", current_users, alert
            )
            
        # Step 5 & 6: Save and sync
        try:
            save_and_sync_production_user_access(prod_df)
        except Exception as e:
            alert = dbc.Alert(f"Failed to save production user access: {str(e)}", color="danger", dismissable=True, duration=5000)
            return (
                False, False, False,
                "", "", [], [], [],
                "", "", [], [], [],
                delete_target, "", current_users, alert
            )
            
        # Audit Log
        log_audit(session.get('email'), "Deleted User", delete_target.strip())
        
        # Display Success Message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success_msg = f"Users Added: 0, Users Updated: 0, Users Deleted: 1 | Timestamp: {timestamp}"
        alert = dbc.Alert(success_msg, color="success", dismissable=True, duration=5000)
        
        updated_users = prod_df.to_dict('records')
        return (
            False, False, False,
            "", "", [], [], [],
            "", "", [], [], [],
            None, "", updated_users, alert
        )
        
    return (
        add_open, edit_open, delete_open,
        add_email, add_pass, add_mods, add_dbs, add_locs,
        edit_email, edit_pass, edit_mods, edit_dbs, edit_locs,
        delete_target, "", current_users, None
    )

# ---------------------------------------------------
# Export Callback
# ---------------------------------------------------
@callback(
    Output('user-settings-download', 'data'),
    Input('users-export-btn', 'n_clicks'),
    State('user-email-search', 'value'),
    State('user-module-filter', 'value'),
    State('user-dashboard-filter', 'value'),
    State('user-location-filter', 'value'),
    State('users-store', 'data'),
    prevent_initial_call=True,
)
def export_filtered_users(n_clicks, email_search, selected_modules, selected_dashboards, selected_locations, users_data):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "User Settings",
        action="Export Data",
        filters={"email_search": email_search, "selected_modules": selected_modules, "selected_dashboards": selected_dashboards, "selected_locations": selected_locations}
    )

    if not n_clicks:
        return None
        
    df = pd.DataFrame(users_data)
    if df.empty:
        df = pd.DataFrame(columns=['email', 'password', 'module', 'dashboards', 'locations'])
        
    # Apply filters
    if email_search:
        df = df[df['email'].str.lower().str.contains(email_search.strip().lower(), na=False)]
        
    if selected_modules:
        mask = df['module'].apply(lambda x: any(m.strip() in selected_modules for m in str(x).split(',')) if pd.notna(x) else False)
        df = df[mask]
        
    if selected_dashboards:
        mask = df['dashboards'].apply(lambda x: any(db.strip() in selected_dashboards for db in str(x).split(',')) if pd.notna(x) else False)
        df = df[mask]
        
    if selected_locations:
        def loc_match(loc_str):
            if pd.isna(loc_str):
                return False
            user_locs = [l.strip() for l in str(loc_str).split(',')]
            if 'ALL' in user_locs:
                return True
            return any(l in selected_locations for l in user_locs)
        df = df[df['locations'].apply(loc_match)]
        
    return dcc.send_data_frame(
        df.to_csv,
        'user_access_settings_export.csv',
        index=False,
    )
