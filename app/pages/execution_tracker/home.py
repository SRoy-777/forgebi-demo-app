import sys
import os
import io
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np

import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table, callback, Input, Output, State, no_update, ALL, callback_context
from flask import session
from database.connections.postgres_connection import engine
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.services.execution_tracker.execution_tracker import (
    get_goals_for_user,
    get_goal_by_id,
    create_goal,
    update_goal,
    delete_goal,
    get_goal_hierarchy,
    get_goal_comments,
    get_subordinates,
    get_role_from_email,
    get_name_from_email,
    ROLE_HIERARCHY,
    get_goal_attachments_by_user,
    get_all_attachments_for_goal,
    get_attachment_by_id,
    delete_attachment_by_id
)

# ---------------------------------------------------
# Categories, Priorities, Status Lists
# ---------------------------------------------------
CATEGORIES = [
    "Sales", "Inventory", "Operations", "Customer Service",
    "Production", "Accounts", "HR", "Training", "Marketing", "Other"
]

PRIORITIES = ["Critical", "High", "Medium", "Low"]

STATUS_OPTIONS = [
    "Open", "In Progress", "Waiting for Dependency",
    "Blocked", "Completed", "Cancelled", "Overdue"
]

PROGRESS_OPTIONS = [0, 25, 50, 75, 100]

# ---------------------------------------------------
# DataTable Styling (Consistent with Orient BI Theme)
# ---------------------------------------------------
TABLE_STYLE = {
    'page_action': 'none',
    'fill_width': True,
    'fixed_rows': {'headers': True},
    'style_table': {
        'overflowX': 'auto',
        'overflowY': 'auto',
        'maxHeight': '500px',
        'width': '100%',
        'minWidth': '100%',
        'border': '1px solid #334155',
        'borderRadius': '12px'
    },
    'style_cell': {
        'fontSize': '12px',
        'fontFamily': "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        'padding': '12px 14px',
        'textAlign': 'center',
        'whiteSpace': 'normal',
        'minWidth': '80px',
        'width': '110px',
        'maxWidth': '180px',
        'border': '1px solid #334155',
        'backgroundColor': '#1e293b',
        'color': '#cbd5e1'
    },
    'style_header': {
        'backgroundColor': '#0f172a',
        'color': '#f8fafc',
        'fontWeight': 'bold',
        'fontSize': '12px',
        'textAlign': 'center',
        'border': '1px solid #334155',
        'height': '44px',
        'minHeight': '44px',
        'maxHeight': '44px',
        'lineHeight': '16px'
    },
    'style_data': {
        'backgroundColor': '#1e293b',
        'color': '#e2e8f0'
      },
      'style_data_conditional': [
          # Alternating rows
          {
              'if': {'row_index': 'odd'},
              'backgroundColor': '#111827'
          },
          {
              'if': {'column_id': 'title'},
              'fontWeight': 'bold',
              'textAlign': 'left',
              'minWidth': '160px',
              'color': '#f8fafc'
          },
          # Pill badges for action columns
          {
              'if': {'column_id': 'btn_update'},
              'color': '#3b82f6',
              'fontWeight': 'bold',
              'backgroundColor': 'rgba(59, 130, 246, 0.12)',
              'border': '1px solid rgba(59, 130, 246, 0.3)',
              'borderRadius': '16px',
              'cursor': 'pointer',
              'padding': '4px 8px'
          },
          {
              'if': {'column_id': 'btn_hierarchy'},
              'color': '#10b981',
              'fontWeight': 'bold',
              'backgroundColor': 'rgba(16, 185, 129, 0.12)',
              'border': '1px solid rgba(16, 185, 129, 0.3)',
              'borderRadius': '16px',
              'cursor': 'pointer',
              'padding': '4px 8px'
          },
          {
              'if': {'column_id': 'btn_delete'},
              'color': '#ef4444',
              'fontWeight': 'bold',
              'backgroundColor': 'rgba(239, 68, 68, 0.12)',
              'border': '1px solid rgba(239, 68, 68, 0.3)',
              'borderRadius': '16px',
              'cursor': 'pointer',
              'padding': '4px 8px'
          },
          {
              'if': {'column_id': 'attachment_name'},
              'color': '#38bdf8',
              'cursor': 'pointer',
              'textDecoration': 'underline'
          },
          # Status coloring
          {
              'if': {'column_id': 'status', 'filter_query': '{status} = "Completed"'},
              'color': '#10b981',
              'fontWeight': 'bold'
          },
          {
              'if': {'column_id': 'status', 'filter_query': '{status} = "In Progress"'},
              'color': '#3b82f6',
              'fontWeight': 'bold'
          },
          {
              'if': {'column_id': 'status', 'filter_query': '{status} = "Blocked"'},
              'color': '#ef4444',
              'fontWeight': 'bold'
          },
          {
              'if': {'column_id': 'status', 'filter_query': '{status} = "Open"'},
              'color': '#94a3b8',
              'fontWeight': 'bold'
          },
          {
              'if': {'column_id': 'status', 'filter_query': '{status} = "Overdue"'},
              'color': '#f59e0b',
              'fontWeight': 'bold'
          },
          {
              'if': {'column_id': 'status', 'filter_query': '{status} = "Waiting for Dependency"'},
              'color': '#a855f7',
              'fontWeight': 'bold'
          },
          {
              'if': {'column_id': 'status', 'filter_query': '{status} = "Cancelled"'},
              'color': '#64748b',
              'fontWeight': 'bold'
          },
      ]
}

# ---------------------------------------------------
# Layout
# ---------------------------------------------------
layout = dbc.Container([
    # Store dynamic current session user info hidden
    dcc.Store(id='et-user-store'),
    dcc.Download(id='et-download-attachment'),
    
    # Modal: Select Attachment to Download (for multiple files)
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Select File to Download")),
        dbc.ModalBody(id='et-download-selection-list'),
        dbc.ModalFooter([
            dbc.Button("Close", id='et-download-selection-close-btn', className='et-btn-glow-secondary')
        ])
    ], id='et-download-selection-modal', is_open=False, size='md'),
    
    # ---------------------------------------------------
    # Header
    # ---------------------------------------------------
    dbc.Row([
        dbc.Col([
            html.H2("Execution Tracker", className='fw-bold mb-1', style={'letterSpacing': '-0.02em', 'color': '#f8fafc'}),
            html.Div("Enterprise Goal Management & Progress Tracker", style={'fontSize': '13px', 'color': '#94a3b8'})
        ], width=8),
        dbc.Col([
            html.Div([
                dbc.Button("Create Goal", id='et-new-goal-btn', className='et-btn-glow-warning me-2', size='sm', style={'display': 'none'}),
                dbc.Button("Refresh", id='et-refresh-btn', className='et-btn-glow-secondary', size='sm')
            ], className='text-end d-flex align-items-center justify-content-end', style={'height': '100%'})
        ], width=4)
    ], className='mb-4 mt-2'),

    # Alert messages container
    html.Div(id='et-alert-container'),

    # ---------------------------------------------------
    # KPI Row
    # ---------------------------------------------------
    dcc.Loading(
        id='et-kpis-loading',
        children=html.Div(id='et-kpi-container', className='mb-3'),
        type='circle'
    ),

    # ---------------------------------------------------
    # Filter Panel
    # ---------------------------------------------------
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Category"),
                    dcc.Dropdown(
                        id='et-filter-category',
                        options=[{'label': 'All Categories', 'value': 'ALL'}] + [{'label': c, 'value': c} for c in CATEGORIES],
                        value='ALL',
                        placeholder='Category',
                        style={'color': '#000000'}
                    )
                ], width=3, xs=12, sm=6, md=3),
                dbc.Col([
                    html.Label("Status"),
                    dcc.Dropdown(
                        id='et-filter-status',
                        options=[{'label': 'All Statuses', 'value': 'ALL'}] + [{'label': s, 'value': s} for s in STATUS_OPTIONS],
                        value='ALL',
                        placeholder='Status',
                        style={'color': '#000000'}
                    )
                ], width=3, xs=12, sm=6, md=3),
                dbc.Col([
                    html.Label("Priority"),
                    dcc.Dropdown(
                        id='et-filter-priority',
                        options=[{'label': 'All Priorities', 'value': 'ALL'}] + [{'label': p, 'value': p} for p in PRIORITIES],
                        value='ALL',
                        placeholder='Priority',
                        style={'color': '#000000'}
                    )
                ], width=3, xs=12, sm=6, md=3),
                dbc.Col([
                    html.Label("Search Goals"),
                    dbc.Input(
                        id='et-filter-search',
                        placeholder='Search title / desc / name...',
                        type='text'
                    )
                ], width=3, xs=12, sm=6, md=3)
            ])
        ])
    ], className='et-filter-card mb-4 shadow-lg'),

    # ---------------------------------------------------
    # Goals Data Grid
    # ---------------------------------------------------
    dcc.Loading(
        id='et-grid-loading',
        children=dbc.Card([
            dbc.CardHeader(
                html.H5("Execution Instruction Goals Matrix", className='fw-bold mb-0 text-light', style={'fontSize': '15px'})
            ),
            dbc.CardBody([
                dash_table.DataTable(
                    id='goals-table',
                    columns=[],
                    data=[],
                    merge_duplicate_headers=True,
                    sort_action='native',
                    **TABLE_STYLE
                )
            ])
        ], className='et-grid-card mb-4 shadow-lg'),
        type='circle'
    ),

    # ---------------------------------------------------
    # Modal: Create Goal
    # ---------------------------------------------------
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Create and Assign Goal")),
        dbc.ModalBody([
            dbc.Label("Goal Title", className='fw-bold'),
            dbc.Input(id='et-create-title', type='text', placeholder='Enter goal summary...', className='mb-2'),
            
            dbc.Label("Description", className='fw-bold'),
            dbc.Textarea(id='et-create-desc', placeholder='Describe details and action items...', rows=4, className='mb-2'),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Category", className='fw-bold'),
                    dcc.Dropdown(id='et-create-category', options=[{'label': c, 'value': c} for c in CATEGORIES], placeholder='Select Category', style={'color': '#000000'})
                ], width=6),
                dbc.Col([
                    dbc.Label("Priority", className='fw-bold'),
                    dcc.Dropdown(id='et-create-priority', options=[{'label': p, 'value': p} for p in PRIORITIES], value='Medium', style={'color': '#000000'})
                ], width=6)
            ], className='mb-2'),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Assign To (Subordinate)", className='fw-bold'),
                    dcc.Dropdown(id='et-create-assigned-to', placeholder='Select Subordinate', multi=True, style={'color': '#000000'})
                ], width=6),
                dbc.Col([
                    dbc.Label("Due Date", className='fw-bold'),
                    html.Br(),
                    dcc.DatePickerSingle(
                        id='et-create-due-date',
                        display_format='DD-MMM-YYYY',
                        date=date.today() + timedelta(days=7),
                        style={'width': '100%'}
                    )
                ], width=6)
            ], className='mb-2'),
            
            dbc.Label("Expected Outcome", className='fw-bold'),
            dbc.Textarea(id='et-create-outcome', placeholder='Define what successful completion looks like...', rows=2, className='mb-3'),
            
            dbc.Label("Attachment (Optional)", className='fw-bold'),
            dcc.Upload(
                id='et-create-upload',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select a File', style={'color': '#3b82f6', 'textDecoration': 'underline'})
                ]),
                className='et-upload-zone mb-2',
                multiple=True
            ),
            html.Div(id='et-create-upload-filename', style={'fontSize': '11px', 'color': '#94a3b8', 'marginTop': '-5px', 'marginBottom': '10px'}),
            
            html.Div(id='et-create-error', style={'color': '#ef4444', 'textAlign': 'center', 'fontWeight': 'bold'})
        ]),
        dbc.ModalFooter([
            dbc.Button("Assign Goal", id='et-create-submit-btn', className='et-btn-glow-warning'),
            dbc.Button("Cancel", id='et-create-cancel-btn', className='et-btn-glow-secondary')
        ])
    ], id='et-create-modal', is_open=False, size='lg'),

    # ---------------------------------------------------
    # Modal: Update Goal
    # ---------------------------------------------------
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Update Goal Progress")),
        dbc.ModalBody([
            html.Div(id='et-update-readonly-section', className='p-3 mb-3 rounded', style={'backgroundColor': '#0f172a', 'border': '1px solid #334155'}),
            
            dcc.Store(id='et-update-goal-id-store'),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Status", className='fw-bold'),
                    dcc.Dropdown(id='et-update-status', options=[{'label': s, 'value': s} for s in STATUS_OPTIONS], style={'color': '#000000'})
                ], width=6),
                dbc.Col([
                    dbc.Label("Progress Percentage", className='fw-bold'),
                    dcc.Dropdown(id='et-update-progress', options=[{'label': f"{p}%", 'value': p} for p in PROGRESS_OPTIONS], style={'color': '#000000'})
                ], width=6)
            ], className='mb-2'),
            
            dbc.Label("Reason for Delay / Remarks (Optional)", className='fw-bold'),
            dbc.Textarea(id='et-update-delay-reason', placeholder='Enter explanations for delay or general remarks...', rows=2, className='mb-2'),
            
            # Edit Due Date section (only visible/enabled for the goal creator)
            html.Div(id='et-update-due-date-container', children=[
                dbc.Label("Extend / Edit Due Date", className='fw-bold', style={'color': '#10b981'}),
                html.Br(),
                dcc.DatePickerSingle(
                    id='et-update-due-date',
                    display_format='DD-MMM-YYYY',
                    style={'width': '100%'}
                ),
            ], className='p-3 mb-3 rounded border', style={'backgroundColor': 'rgba(16, 185, 129, 0.04)', 'borderColor': '#10b981', 'display': 'none'}),
            
            dbc.Label("Add Comment", className='fw-bold'),
            dbc.Textarea(id='et-update-comment', placeholder='Type a message to comment...', rows=2, className='mb-3'),
            
            dbc.Label("Attachment (Optional)", className='fw-bold'),
            dcc.Upload(
                id='et-update-upload',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select a File', style={'color': '#3b82f6', 'textDecoration': 'underline'})
                ]),
                className='et-upload-zone mb-2',
                multiple=True
            ),
            html.Div(id='et-update-upload-filename', style={'fontSize': '11px', 'color': '#94a3b8', 'marginTop': '-5px', 'marginBottom': '10px'}),
            
            # Delegation block inside update form
            html.Div(id='et-update-delegate-container', children=[
                dbc.Checkbox(id='et-update-delegate-chk', label="Delegate further down the hierarchy", className='mb-2 fw-bold', style={'color': '#3b82f6'}),
                html.Div(id='et-update-delegate-fields', children=[
                    dbc.Label("Delegate To (Subordinate)", className='fw-bold'),
                    dcc.Dropdown(id='et-update-delegate-assignee', placeholder='Select Subordinate', multi=True, className='mb-2', style={'color': '#000000'}),
                    
                    dbc.Label("Delegated Due Date", className='fw-bold'),
                    html.Br(),
                    dcc.DatePickerSingle(
                        id='et-update-delegate-due-date',
                        display_format='DD-MMM-YYYY',
                        style={'width': '100%'},
                        className='mb-2'
                    ),
                    html.Br(),
                    
                    dbc.Label("Remarks / Description for Delegate", className='fw-bold'),
                    dbc.Textarea(id='et-update-delegate-remarks', placeholder='Enter custom remarks or instructions for the delegate...', rows=2, className='mb-2'),
                    
                    html.Small("This will automatically spawn a child goal under this hierarchy.", className='text-muted d-block mb-3')
                ], style={'display': 'none'})
            ], className='p-3 mb-3 rounded border', style={'backgroundColor': 'rgba(59, 130, 246, 0.04)', 'borderColor': '#2563eb'}),
            
            # Comment history block
            html.H6("Comment History", className='fw-bold text-secondary border-bottom pb-1 mb-2'),
            html.Div(id='et-comment-history-div', style={'maxHeight': '180px', 'overflowY': 'auto', 'backgroundColor': '#0f172a', 'padding': '12px', 'borderRadius': '8px', 'border': '1px solid #334155'}),
            
            html.Div(id='et-update-error', style={'color': '#ef4444', 'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '10px'})
        ]),
        dbc.ModalFooter([
            dbc.Button("Save Updates", id='et-update-submit-btn', className='et-btn-glow-blue'),
            dbc.Button("Close", id='et-update-cancel-btn', className='et-btn-glow-secondary')
        ])
    ], id='et-update-modal', is_open=False, size='lg'),

    # ---------------------------------------------------
    # Modal: Hierarchy Popup
    # ---------------------------------------------------
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Execution Delegation Chain")),
        dbc.ModalBody([
            html.Div(id='et-hierarchy-tree-container', style={'padding': '10px', 'backgroundColor': 'transparent'})
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id='et-hierarchy-close-btn', className='et-btn-glow-secondary')
        ])
    ], id='et-hierarchy-modal', is_open=False, size='lg'),

    # ---------------------------------------------------
    # Modal: Confirm Goal Deletion
    # ---------------------------------------------------
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Confirm Goal Deletion")),
        dbc.ModalBody(id='et-delete-confirm-text', className='fw-bold text-light'),
        dcc.Store(id='et-delete-goal-id-store'),
        dbc.ModalFooter([
            dbc.Button("Yes, Delete", id='et-delete-confirm-btn', className='et-btn-glow-danger'),
            dbc.Button("Cancel", id='et-delete-cancel-btn', className='et-btn-glow-secondary')
        ])
    ], id='et-delete-confirm-modal', is_open=False, size='md')
], fluid=True, className='et-container')

# ---------------------------------------------------
# Callback 1: Initialize User Context & Subordinate Dropdowns
# ---------------------------------------------------
@callback(
    [
        Output('et-user-store', 'data'),
        Output('et-new-goal-btn', 'style'),
        Output('et-create-assigned-to', 'options'),
        Output('et-update-delegate-assignee', 'options'),
        Output('et-update-delegate-container', 'style')
    ],
    [
        Input('url', 'pathname')
    ]
)
def init_user_context(pathname):
    email = session.get('email')
    if not email:
        return {}, {'display': 'none'}, [], [], {'display': 'none'}
        
    role = get_role_from_email(email)
    role_level = ROLE_HIERARCHY.get(role, 0)
    
    # Hide 'Create Goal' if Store Manager (level 0)
    btn_style = {'fontWeight': 'bold'} if role_level > 0 else {'display': 'none'}
    delegate_container_style = {'padding': '12px', 'borderRadius': '6px'} if role_level > 0 else {'display': 'none'}
    
    # Find subordinates list
    sub_list = get_subordinates(email)
    sub_opts = [{'label': f"{s['name']} ({s['role']}) - {s['email']}", 'value': s['email']} for s in sub_list]
    
    user_data = {'email': email, 'role': role, 'level': role_level}
    
    return user_data, btn_style, sub_opts, sub_opts, delegate_container_style

# ---------------------------------------------------
# Callback 2: Toggle Delegate Sub-Fields in Update Modal
# ---------------------------------------------------
@callback(
    Output('et-update-delegate-fields', 'style'),
    Input('et-update-delegate-chk', 'value'),
    prevent_initial_call=True
)
def toggle_delegate_fields(checked):
    if checked:
        return {'display': 'block', 'marginTop': '8px'}
    return {'display': 'none'}

# ---------------------------------------------------
# Callback 3: Open Goal Creation Modal
# ---------------------------------------------------
@callback(
    Output('et-create-modal', 'is_open'),
    [
        Input('et-new-goal-btn', 'n_clicks'),
        Input('et-create-cancel-btn', 'n_clicks')
    ],
    State('et-create-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_create_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

# ---------------------------------------------------
# Callback 4: Load Grid, KPIs, and perform Goal Deletions
# ---------------------------------------------------
@callback(
    [
        Output('et-kpi-container', 'children'),
        Output('goals-table', 'data'),
        Output('goals-table', 'columns'),
        Output('et-alert-container', 'children')
    ],
    [
        Input('et-refresh-btn', 'n_clicks'),
        Input('et-create-submit-btn', 'n_clicks'),
        Input('et-update-submit-btn', 'n_clicks'),
        Input('et-delete-confirm-btn', 'n_clicks')
    ],
    [
        State('et-user-store', 'data'),
        State('et-filter-category', 'value'),
        State('et-filter-status', 'value'),
        State('et-filter-priority', 'value'),
        State('et-filter-search', 'value')
    ]
)
def load_tracker_data(n_refresh, n_create, n_update, n_delete, user_data, cat_f, status_f, priority_f, search_f):
    email = session.get('email')
    if not email:
        return "", [], [], ""
        
    alert_msg = ""
    
    # Fetch goals dataframe
    df = get_goals_for_user(email)
    
    role = get_role_from_email(email)
    if df.empty:
        empty_kpis = build_kpi_layout(0, 0, 0, 0, 0, 0, 0, avg_rating=0.0, role=role)
        columns = [
            {'name': ['Goal Info', 'ID'], 'id': 'goal_id'},
            {'name': ['Goal Info', 'Title'], 'id': 'title'},
            {'name': ['Goal Info', 'Category'], 'id': 'goal_category'},
            {'name': ['Goal Info', 'Priority'], 'id': 'priority'},
            {'name': ['Assignment', 'Assigned By'], 'id': 'assigned_by_name'},
            {'name': ['Assignment', 'Assigned To'], 'id': 'assigned_to_name'},
            {'name': ['Dates', 'Due Date'], 'id': 'due_date'},
            {'name': ['Dates', 'Days Remaining'], 'id': 'days_remaining'},
            {'name': ['Progress', 'Status'], 'id': 'status'},
            {'name': ['Progress', 'Progress %'], 'id': 'progress_pct'},
            {'name': ['Progress', 'Attachment'], 'id': 'attachment_name'},
            {'name': ['Updates', 'Last Updated By'], 'id': 'last_updated_by'},
            {'name': ['Updates', 'Last Updated On'], 'id': 'updated_at'},
            {'name': ['Actions', 'Update'], 'id': 'btn_update'}
        ]
        columns.append({'name': ['Actions', 'Goal Hierarchy'], 'id': 'btn_hierarchy'})
        columns.append({'name': ['Actions', 'Delete'], 'id': 'btn_delete'})
        return empty_kpis, [], columns, alert_msg

    # Apply dropdown filters
    if cat_f and cat_f != 'ALL':
        df = df[df['goal_category'] == cat_f]
        
    if status_f and status_f != 'ALL':
        df = df[df['status'] == status_f]
        
    if priority_f and priority_f != 'ALL':
        df = df[df['priority'] == priority_f]
        
    if search_f and str(search_f).strip() != "":
        q = str(search_f).strip().upper()
        df = df[
            df['title'].astype(str).str.upper().str.contains(q, na=False) |
            df['description'].astype(str).str.upper().str.contains(q, na=False) |
            df['assigned_by_name'].astype(str).str.upper().str.contains(q, na=False) |
            df['assigned_to_name'].astype(str).str.upper().str.contains(q, na=False)
        ]

    # Calculate KPIs
    total_goals = len(df)
    open_statuses = ['Open', 'In Progress', 'Waiting for Dependency', 'Blocked']
    open_goals = len(df[df['status'].isin(open_statuses)])
    completed_goals = len(df[df['status'] == 'Completed'])
    overdue_goals = len(df[df['status'] == 'Overdue'])
    blocked_goals = len(df[df['status'] == 'Blocked'])
    critical_goals = len(df[df['priority'] == 'Critical'])
    
    # Calculate Due This Week
    today = datetime.today().date()
    start_week = today - timedelta(days=today.weekday())
    end_week = start_week + timedelta(days=6)
    
    due_week_count = 0
    for d in df['due_date'].dropna():
        try:
            d_date = pd.to_datetime(d).date()
            if start_week <= d_date <= end_week:
                due_week_count += 1
        except Exception:
            pass
            
    completion_rate = round((completed_goals / total_goals) * 100, 1) if total_goals > 0 else 0.0
    
    # Calculate user's average rating on tasks assigned to them (excluding ED/MD)
    avg_rating = 0.0
    if role not in ['ED', 'MD']:
        assigned_to_me_completed = df[
            (df['assigned_to_employee_code'].str.lower() == email.lower()) & 
            (df['status'] == 'Completed')
        ]
        ratings = []
        for idx, row in assigned_to_me_completed.iterrows():
            rating = calculate_goal_rating(
                row['created_at'],
                row['due_date'],
                row['status'],
                row['completed_at']
            )
            if rating > 0:
                ratings.append(rating)
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
        
    kpi_cards = build_kpi_layout(open_goals, completed_goals, overdue_goals, blocked_goals, due_week_count, critical_goals, completion_rate, avg_rating=avg_rating, role=role)
    
    # Grid Data Formatting
    disp_df = df.copy()
    if 'attachment_data' in disp_df.columns:
        disp_df.drop(columns=['attachment_data'], inplace=True, errors='ignore')
    
    # Query attachments uploaded by this user in a single batch
    attachments_map = {}
    if engine is not None:
        try:
            with engine.connect() as conn:
                res = conn.execute(text("""
                    SELECT goal_id, attachment_name 
                    FROM goal_attachments 
                    WHERE LOWER(uploaded_by_employee_code) = LOWER(:email)
                """), {"email": email})
                for r in res.fetchall():
                    g_id = r[0]
                    name = r[1]
                    if g_id not in attachments_map:
                        attachments_map[g_id] = []
                    attachments_map[g_id].append(name)
        except Exception as e:
            print(f"Error loading user attachments: {e}")

    def format_attachments(row):
        g_id = row['goal_id']
        names = attachments_map.get(g_id, [])
        if not names:
            return ""
        elif len(names) == 1:
            return f"📎 {names[0]}"
        else:
            return f"📎 ({len(names)} files) {', '.join(names)}"

    disp_df['attachment_name'] = disp_df.apply(format_attachments, axis=1)
    
    # Add display properties
    disp_df['btn_update'] = "✏️ Update"
    disp_df['btn_hierarchy'] = "👁️ View Chain"
    disp_df['btn_delete'] = "🗑️ Delete"
    
    # Compute Days Remaining
    disp_df['days_remaining'] = disp_df['due_date'].apply(lambda x: get_days_remaining(x))
    
    # Format dates
    disp_df['due_date'] = pd.to_datetime(disp_df['due_date']).dt.strftime('%d-%b-%Y')
    disp_df['updated_at'] = pd.to_datetime(disp_df['updated_at']).dt.strftime('%d-%b-%Y %H:%M')
    
    # Format progress pct
    disp_df['progress_pct'] = disp_df['progress_pct'].apply(lambda x: f"{x}%")
    
    # Setup columns list conditionally based on user role
    role = user_data.get('role', 'Store Manager')
    columns = [
        {'name': ['Goal Info', 'ID'], 'id': 'goal_id'},
        {'name': ['Goal Info', 'Title'], 'id': 'title'},
        {'name': ['Goal Info', 'Category'], 'id': 'goal_category'},
        {'name': ['Goal Info', 'Priority'], 'id': 'priority'},
        {'name': ['Assignment', 'Assigned By'], 'id': 'assigned_by_name'},
        {'name': ['Assignment', 'Assigned To'], 'id': 'assigned_to_name'},
        {'name': ['Dates', 'Due Date'], 'id': 'due_date'},
        {'name': ['Dates', 'Days Remaining'], 'id': 'days_remaining'},
        {'name': ['Progress', 'Status'], 'id': 'status'},
        {'name': ['Progress', 'Progress %'], 'id': 'progress_pct'},
        {'name': ['Progress', 'Attachment'], 'id': 'attachment_name'},
        {'name': ['Updates', 'Last Updated By'], 'id': 'last_updated_by'},
        {'name': ['Updates', 'Last Updated On'], 'id': 'updated_at'},
        {'name': ['Actions', 'Update'], 'id': 'btn_update'}
    ]
    
    columns.append({'name': ['Actions', 'Goal Hierarchy'], 'id': 'btn_hierarchy'})
    columns.append({'name': ['Actions', 'Delete'], 'id': 'btn_delete'})
    
    return kpi_cards, disp_df.to_dict('records'), columns, alert_msg

# Helpers for DataTable formatting
def calculate_goal_rating(created_at, due_date, status, completed_at):
    if status != 'Completed' or not completed_at or not due_date or not created_at:
        return 0
        
    created_dt = pd.to_datetime(created_at)
    due_dt = pd.to_datetime(due_date)
    completed_dt = pd.to_datetime(completed_at)
    
    total_timeframe = (due_dt - created_dt).total_seconds()
    if total_timeframe <= 0:
        return 2
        
    time_used = (completed_dt - created_dt).total_seconds()
    if time_used < 0:
        time_used = 0
        
    ratio = time_used / total_timeframe
    
    if ratio <= 0.1:     # 90% timeframe faster
        return 5
    elif ratio <= 0.3:   # 70% timeframe faster
        return 4
    elif ratio <= 0.5:   # 50% timeframe faster
        return 3
    elif ratio <= 1.0:   # Completed on time
        return 2
    else:                # Completed late
        return 1

def format_avg_stars(rating):
    if rating <= 0:
        return "No ratings"
    full_stars = int(rating)
    half_star = (rating - full_stars) >= 0.25
    stars_str = "⭐" * full_stars
    if half_star:
        stars_str += "½"
    return f"{stars_str} ({rating:.1f})"

def get_days_remaining(due_date):
    if pd.isna(due_date):
        return "N/A"
    try:
        due = pd.to_datetime(due_date).date()
        diff = (due - datetime.today().date()).days
        if diff < 0:
            return f"{abs(diff)} Days Overdue"
        elif diff == 0:
            return "Due Today"
        else:
            return f"{diff} Days Left"
    except Exception:
        return "N/A"

def build_kpi_layout(open_g, comp_g, over_g, block_g, due_wk, crit_g, rate, avg_rating=0.0, role='Store Manager'):
    cols = [
        dbc.Col(build_kpi_card("Open Goals", open_g, "et-kpi-open"), width=2, xs=6, sm=4, md=2),
        dbc.Col(build_kpi_card("Completed", comp_g, "et-kpi-completed"), width=2, xs=6, sm=4, md=2),
        dbc.Col(build_kpi_card("Overdue", over_g, "et-kpi-overdue"), width=2, xs=6, sm=4, md=2),
        dbc.Col(build_kpi_card("Blocked", block_g, "et-kpi-blocked"), width=2, xs=6, sm=4, md=2),
        dbc.Col(build_kpi_card("Due This Week", due_wk, "et-kpi-week"), width=2, xs=6, sm=4, md=2),
        dbc.Col(build_kpi_card("Critical Priority", crit_g, "et-kpi-critical"), width=2, xs=6, sm=4, md=2),
        dbc.Col(build_kpi_card("Completion Rate", f"{rate}%", "et-kpi-rate"), width=2, xs=12, sm=6, md=2),
    ]
    if role not in ['ED', 'MD']:
        cols.append(dbc.Col(build_kpi_card("Average Rating", format_avg_stars(avg_rating), "et-kpi-rate"), width=2, xs=12, sm=6, md=2))
    return dbc.Row(cols, className='g-2')

def build_kpi_card(title, value, bg_class):
    return dbc.Card([
        dbc.CardBody([
            html.Div(title, style={
                'fontSize': '10px',
                'fontWeight': '600',
                'textAlign': 'center',
                'color': '#94a3b8',
                'whiteSpace': 'nowrap',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'textTransform': 'uppercase',
                'letterSpacing': '0.05em'
            }),
            html.Div(value, style={
                'fontSize': '18px',
                'fontWeight': '700',
                'textAlign': 'center',
                'marginTop': '2px',
                'color': '#f8fafc'
            })
        ], style={'padding': '8px 10px'})
    ], className=f'et-kpi-card {bg_class}')

# ---------------------------------------------------
# Callback 5: Create Goal Submission
# ---------------------------------------------------
@callback(
    [
        Output('et-create-modal', 'is_open', allow_duplicate=True),
        Output('et-create-error', 'children'),
        Output('et-create-title', 'value'),
        Output('et-create-desc', 'value'),
        Output('et-create-category', 'value'),
        Output('et-create-assigned-to', 'value'),
        Output('et-create-outcome', 'value'),
        Output('et-create-upload', 'contents'),
        Output('et-create-upload-filename', 'children')
    ],
    Input('et-create-submit-btn', 'n_clicks'),
    [
        State('et-create-title', 'value'),
        State('et-create-desc', 'value'),
        State('et-create-category', 'value'),
        State('et-create-priority', 'value'),
        State('et-create-assigned-to', 'value'),
        State('et-create-due-date', 'date'),
        State('et-create-outcome', 'value'),
        State('et-create-upload', 'contents'),
        State('et-create-upload', 'filename')
    ],
    prevent_initial_call=True
)
def handle_create_goal(n_clicks, title, desc, cat, priority, assigned_to, due_date, outcome, upload_contents, upload_filename):
    email = session.get('email')
    if not email:
        return no_update
        
    if not title or not str(title).strip():
        return no_update, "Goal Title is required.", no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
    if not cat:
        return no_update, "Goal Category is required.", no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
    if not assigned_to:
        return no_update, "Assignee (Subordinate) is required.", no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
    if not due_date:
        return no_update, "Due Date is required.", no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
    attachments = []
    if upload_contents and upload_filename:
        import base64
        contents_list = upload_contents if isinstance(upload_contents, list) else [upload_contents]
        filenames_list = upload_filename if isinstance(upload_filename, list) else [upload_filename]
        for content, name in zip(contents_list, filenames_list):
            try:
                content_type, content_string = content.split(',')
                file_bytes = base64.b64decode(content_string)
                if len(file_bytes) > 10 * 1024 * 1024:
                    return no_update, f"File size exceeds the 10MB limit for {name}.", no_update, no_update, no_update, no_update, no_update, no_update, no_update
                attachments.append({"name": name, "data": file_bytes})
            except Exception as e:
                return no_update, f"Error parsing uploaded file {name}: {str(e)}", no_update, no_update, no_update, no_update, no_update, no_update, no_update
            
    try:
        assignees = assigned_to if isinstance(assigned_to, list) else [assigned_to]
        success_count = 0
        for email_to in assignees:
            new_id = create_goal(
                title=title.strip(),
                description=desc.strip() if desc else "",
                category=cat,
                priority=priority,
                assigned_by_email=email,
                assigned_to_email=email_to,
                due_date=due_date,
                expected_outcome=outcome.strip() if outcome else "",
                attachments=attachments
            )
            if new_id:
                success_count += 1
                
        if success_count > 0:
            return False, "", "", "", None, None, "", None, ""
        else:
            return no_update, "Failed to write goal to Database.", no_update, no_update, no_update, no_update, no_update, no_update, no_update
    except Exception as e:
        return no_update, f"Error creating goal: {str(e)}", no_update, no_update, no_update, no_update, no_update, no_update, no_update

# ---------------------------------------------------
# Callback 6: Handle Cell clicks (Updates & Hierarchy modals popup trigger)
# ---------------------------------------------------
@callback(
    [
        Output('et-update-modal', 'is_open'),
        Output('et-update-goal-id-store', 'data'),
        Output('et-update-readonly-section', 'children'),
        Output('et-update-status', 'value'),
        Output('et-update-progress', 'value'),
        Output('et-update-delay-reason', 'value'),
        Output('et-update-comment', 'value'),
        Output('et-update-delegate-chk', 'value'),
        Output('et-update-delegate-assignee', 'value'),
        Output('et-update-delegate-due-date', 'date'),
        Output('et-update-delegate-remarks', 'value'),
        Output('et-comment-history-div', 'children'),
        Output('et-update-due-date-container', 'style'),
        Output('et-update-due-date', 'date'),
        Output('et-update-upload', 'contents'),
        Output('et-update-upload-filename', 'children'),
        
        Output('et-hierarchy-modal', 'is_open'),
        Output('et-hierarchy-tree-container', 'children'),
        
        Output('et-delete-confirm-modal', 'is_open'),
        Output('et-delete-goal-id-store', 'data'),
        Output('et-delete-confirm-text', 'children'),
        Output('et-alert-container', 'children', allow_duplicate=True)
    ],
    Input('goals-table', 'active_cell'),
    [
        State('goals-table', 'data')
    ],
    prevent_initial_call=True
)
def handle_grid_interactions(active_cell, table_data):
    if not active_cell or not table_data:
        return no_update
        
    row_idx = active_cell['row']
    col_id = active_cell['column_id']
    
    if row_idx >= len(table_data):
        return no_update
        
    row_data = table_data[row_idx]
    goal_id = row_data['goal_id']
    
    # ---------------------------------------------------
    # Path A: Clicked Update Goal
    # ---------------------------------------------------
    if col_id == 'btn_update':
        goal = get_goal_by_id(goal_id)
        if not goal:
            return no_update
            
        title = goal.get('title', '')
        desc = goal.get('description', '')
        cat = goal.get('goal_category', '')
        prio = goal.get('priority', '')
        assigned_by = goal.get('assigned_by_name', '')
        due_date_val = goal.get('due_date')
        outcome = goal.get('expected_outcome', '')
        status = goal.get('status', 'Open')
        progress = goal.get('progress_pct', 0)
        delay = goal.get('reason_for_delay', '')
        
        due_formatted = ""
        raw_due_date = None
        if due_date_val:
            try:
                due_dt = pd.to_datetime(due_date_val)
                due_formatted = due_dt.strftime('%d-%b-%Y')
                raw_due_date = due_dt.strftime('%Y-%m-%d')
            except Exception:
                due_formatted = str(due_date_val)
                raw_due_date = None

        # Construct readonly header HTML
        readonly_html = html.Div([
            html.Div([html.Strong("Goal: ", style={'color': '#94a3b8'}), html.Span(title, style={'color': '#f8fafc', 'fontWeight': 'bold'})], className='mb-2', style={'fontSize': '14px'}),
            html.Div([html.Strong("Description: ", style={'color': '#94a3b8'}), html.Span(desc or "No description provided.", style={'color': '#cbd5e1'})], className='mb-2'),
            dbc.Row([
                dbc.Col([html.Strong("Category: ", style={'color': '#94a3b8'}), html.Span(cat, style={'color': '#f8fafc'})], width=4),
                dbc.Col([html.Strong("Priority: ", style={'color': '#94a3b8'}), html.Span(prio, style={'color': '#f8fafc'})], width=4),
                dbc.Col([html.Strong("Due Date: ", style={'color': '#94a3b8'}), html.Span(due_formatted, style={'color': '#f8fafc'})], width=4),
            ], className='mb-2'),
            dbc.Row([
                dbc.Col([html.Strong("Assigned By: ", style={'color': '#94a3b8'}), html.Span(assigned_by, style={'color': '#f8fafc'})], width=6),
                dbc.Col([html.Strong("Expected Outcome: ", style={'color': '#94a3b8'}), html.Span(outcome or "N/A", style={'color': '#cbd5e1'})], width=6),
            ]),
        ], style={'fontSize': '12px', 'lineHeight': '18px'})
        
        # Load comment history
        comments = get_goal_comments(goal_id)
        if comments:
            comments_layout = html.Div([
                html.Div([
                    html.Div([
                        html.Strong(f"{c['name']} ({c['role']})", style={'color': '#f8fafc'}),
                        html.Span(f" - {pd.to_datetime(c['created_at']).strftime('%d-%b-%Y %H:%M')}", style={'color': '#64748b', 'fontSize': '10px', 'marginLeft': '6px'})
                    ], style={'fontSize': '11px'}),
                    html.Div(c['comment'], style={'fontSize': '12px', 'color': '#cbd5e1', 'paddingLeft': '10px', 'marginTop': '4px'})
                ], className='p-2 mb-2 rounded', style={'backgroundColor': '#0f172a', 'borderLeft': '3px solid #3b82f6'})
                for c in comments
            ])
        else:
            comments_layout = html.Div("No comments added yet.", style={'fontStyle': 'italic', 'color': '#64748b', 'fontSize': '12px'})
            
        # Check if the logged-in user is the creator of the goal
        assigned_by_email = goal.get('assigned_by_employee_code', '')
        email = session.get('email', '')
        is_creator = False
        if email and assigned_by_email:
            is_creator = (assigned_by_email.lower().strip() == email.lower().strip())
            
        due_date_style = {'display': 'block'} if is_creator else {'display': 'none'}
        
        # Fetch current user's attachments for the goal to display in the update modal
        user_atts = get_goal_attachments_by_user(goal_id, email) if email else []
        if user_atts:
            att_names = [att['attachment_name'] for att in user_atts]
            current_filename = f"Current attachments: {', '.join(att_names)}"
        else:
            current_filename = "No files attached"
            
        return (
            True, goal_id, readonly_html, status, progress, delay, "", False, None,
            raw_due_date, "",  # Initialize delegated due date and custom remarks fields
            comments_layout, due_date_style, raw_due_date, None, current_filename,
            False, "",
            False, None, "", no_update
        )
        
    # ---------------------------------------------------
    # Path B: Clicked View Hierarchy Chain
    # ---------------------------------------------------
    elif col_id == 'btn_hierarchy':
        chain = get_goal_hierarchy(goal_id)
        
        if not chain:
            hierarchy_layout = html.Div("Failed to fetch delegation tree.", style={'color': 'red'})
        else:
            # Group all attachments by the uploader's email across the chain
            attachments_by_user = {}
            for node in chain:
                g_id = node['goal_id']
                atts = get_all_attachments_for_goal(g_id)
                for att in atts:
                    uploader = att['uploaded_by_employee_code'].lower().strip()
                    if uploader not in attachments_by_user:
                        attachments_by_user[uploader] = []
                    attachments_by_user[uploader].append(att)

            elements = []
            
            # 1. Render Root Goal Initiator Box (Level 0)
            root_goal = chain[0]
            initiator_email = root_goal['assigned_by_employee_code'].lower().strip()
            initiator_name = root_goal['assigned_by_name']
            initiator_role = root_goal['assigned_by_role']
            initiator_atts = attachments_by_user.get(initiator_email, [])
            
            initiator_div = html.Div([
                html.Div([
                    html.Span("Goal Initiator: ", className='fw-bold text-success', style={'color': '#10b981'}),
                    html.Span(initiator_name, className='fw-bold text-light', style={'fontSize': '14px'}),
                    html.Span(f" ({initiator_role}) - {initiator_email}", style={'color': '#94a3b8', 'fontSize': '11px', 'marginLeft': '6px'}),
                ], className='mb-2'),
                html.Div([
                    html.Strong("Attachments: ", style={'color': '#94a3b8'}),
                    html.Span([
                        html.Span(
                            f"📎 {att['attachment_name']}",
                            id={'type': 'et-chain-attachment', 'index': att['attachment_id']},
                            style={'color': '#38bdf8', 'cursor': 'pointer', 'textDecoration': 'underline', 'marginRight': '12px', 'fontWeight': '500'}
                        ) for att in initiator_atts
                    ]) if initiator_atts else html.Span("None", style={'color': '#64748b'})
                ], style={'fontSize': '12px', 'marginTop': '4px'})
            ], className='et-chain-box et-chain-box-root')
            
            elements.append(initiator_div)
            elements.append(html.Div("↓", className='et-chain-connector'))

            # 2. Render Delegation Levels (RM, ZM, SM, etc.)
            logged_in_email = session.get('email', '').lower().strip()
            logged_in_role = get_role_from_email(logged_in_email)
            
            for i, node in enumerate(chain):
                is_current = node['goal_id'] == goal_id
                
                assignee_email = node['assigned_to_employee_code'].lower().strip()
                user_atts = attachments_by_user.get(assignee_email, [])
                
                # Check visibility: logged-in user is ED/MD OR is the node's assignee
                can_see_details = (logged_in_role in ['ED', 'MD']) or (assignee_email == logged_in_email)
                
                # Check rating visibility: logged-in user is ED/MD, assignee, or assigner
                can_see_rating = (logged_in_role in ['ED', 'MD']) or (node['assigned_by_employee_code'].lower().strip() == logged_in_email) or (assignee_email == logged_in_email)
                
                rating_div = html.Div()
                if can_see_rating and node['status'] == 'Completed':
                    rating_val = calculate_goal_rating(node['created_at'], node['due_date'], node['status'], node['completed_at'])
                    if rating_val > 0:
                        rating_div = html.Div([
                            html.Strong("Rating: ", style={'color': '#94a3b8'}),
                            html.Span("⭐" * rating_val, style={'color': '#f59e0b', 'fontSize': '13px', 'fontWeight': 'bold'})
                        ], style={'fontSize': '12px', 'marginBottom': '6px'})
                
                if can_see_details:
                    details_row = dbc.Row([
                        dbc.Col([html.Strong("Status: ", style={'color': '#94a3b8'}), html.Span(node['status'], style={'fontWeight': '600'})], width=4),
                        dbc.Col([html.Strong("Progress: ", style={'color': '#94a3b8'}), html.Span(f"{node['progress_pct']}%", style={'fontWeight': '600'})], width=4),
                        dbc.Col([html.Strong("Updated: ", style={'color': '#94a3b8'}), html.Span(pd.to_datetime(node['updated_at']).strftime('%d-%b-%Y %H:%M'))], width=4),
                    ], className='mb-2', style={'fontSize': '12px'})
                    
                    remarks_div = html.Div([html.Strong("Remarks: ", style={'color': '#94a3b8'}), html.Span(node['reason_for_delay'] or "None", style={'color': '#cbd5e1'})], style={'fontSize': '12px', 'marginBottom': '6px'})
                else:
                    details_row = html.Div()
                    remarks_div = html.Div()
                    
                node_div = html.Div([
                    html.Div([
                        html.Span(f"Level {i+1} (Assignee): ", style={'color': '#3b82f6' if is_current else '#94a3b8', 'fontWeight': '600'}),
                        html.Span(node['assigned_to_name'], className='fw-bold text-light', style={'fontSize': '14px', 'marginLeft': '4px'}),
                        html.Span(f" ({node['assigned_to_role']}) - {assignee_email}", style={'color': '#64748b', 'fontSize': '11px', 'marginLeft': '6px'}),
                    ], className='mb-2'),
                    details_row,
                    remarks_div,
                    rating_div,
                    
                    html.Div([
                        html.Strong("Attachments: ", style={'color': '#94a3b8'}),
                        html.Span([
                            html.Span(
                                f"📎 {att['attachment_name']}",
                                id={'type': 'et-chain-attachment', 'index': att['attachment_id']},
                                style={'color': '#38bdf8', 'cursor': 'pointer', 'textDecoration': 'underline', 'marginRight': '12px', 'fontWeight': '500'}
                            ) for att in user_atts
                        ]) if user_atts else html.Span("None", style={'color': '#64748b'})
                    ], style={'fontSize': '12px', 'marginTop': '4px'})
                ], className='et-chain-box et-chain-box-current' if is_current else 'et-chain-box')
                
                elements.append(node_div)
                
                # Add downward arrow between chain items
                if i < len(chain) - 1:
                    elements.append(html.Div("↓", className='et-chain-connector'))
                    
            hierarchy_layout = html.Div(elements)
            
        return (
            False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update,
            no_update, no_update,  # New outputs
            no_update, {'display': 'none'}, None, no_update, no_update,
            True, hierarchy_layout,
            False, None, "", no_update
        )
        
    # ---------------------------------------------------
    # Path C: Clicked Delete Goal
    # ---------------------------------------------------
    elif col_id == 'btn_delete':
        title = row_data['title']
        assigner = row_data['assigned_by_employee_code']
        email = session.get('email', '')
        my_role = get_role_from_email(email)
        my_level = ROLE_HIERARCHY.get(my_role, 0)
        
        if assigner == email or my_level >= 4:
            confirm_text = f"Are you sure you want to delete the goal: \"{title}\"? This will also permanently delete all sub-assigned child goals in the hierarchy."
            return (
                False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update,
                no_update, no_update,  # New outputs
                no_update, no_update, no_update, no_update, no_update,
                False, "",
                True, goal_id, confirm_text, ""
            )
        else:
            alert = dbc.Alert("Permission Denied: You can only delete goals assigned by you.", color="danger", dismissable=True)
            return (
                False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update,
                no_update, no_update,  # New outputs
                no_update, no_update, no_update, no_update, no_update,
                False, "",
                False, None, "", alert
            )
        
    return (
        False, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update,
        no_update, no_update,  # New outputs
        {'display': 'none'}, None, no_update, no_update,
        False, "",
    )

# ---------------------------------------------------
# Callback 7: Cancel Update Modal
# ---------------------------------------------------
@callback(
    Output('et-update-modal', 'is_open', allow_duplicate=True),
    Input('et-update-cancel-btn', 'n_clicks'),
    prevent_initial_call=True
)
def cancel_update_modal(n_clicks):
    if n_clicks:
        return False
    return True

# ---------------------------------------------------
# Callback 8: Cancel Hierarchy Modal
# ---------------------------------------------------
@callback(
    Output('et-hierarchy-modal', 'is_open', allow_duplicate=True),
    Input('et-hierarchy-close-btn', 'n_clicks'),
    prevent_initial_call=True
)
def cancel_hierarchy_modal(n_clicks):
    if n_clicks:
        return False
    return True


# ---------------------------------------------------
# Callback 8a: Confirm Delete Goal
# ---------------------------------------------------
@callback(
    [
        Output('et-delete-confirm-modal', 'is_open', allow_duplicate=True),
        Output('et-alert-container', 'children', allow_duplicate=True)
    ],
    Input('et-delete-confirm-btn', 'n_clicks'),
    [
        State('et-delete-goal-id-store', 'data')
    ],
    prevent_initial_call=True
)
def confirm_delete_goal(n_clicks, goal_id):
    if not n_clicks or not goal_id:
        return no_update
        
    email = session.get('email')
    if not email:
        return no_update
        
    success = delete_goal(goal_id, email)
    if success:
        alert_msg = dbc.Alert("Goal deleted successfully!", color="success", dismissable=True)
    else:
        alert_msg = dbc.Alert("Error occurred while deleting goal.", color="danger", dismissable=True)
        
    return False, alert_msg


# ---------------------------------------------------
# Callback 8b: Cancel Delete Modal
# ---------------------------------------------------
@callback(
    Output('et-delete-confirm-modal', 'is_open', allow_duplicate=True),
    [
        Input('et-delete-cancel-btn', 'n_clicks')
    ],
    prevent_initial_call=True
)
def cancel_delete_modal(n_clicks):
    if n_clicks:
        return False
    return no_update


# ---------------------------------------------------
# Callback 9: Save Update Goal details & Delegation
# ---------------------------------------------------
@callback(
    [
        Output('et-update-modal', 'is_open', allow_duplicate=True),
        Output('et-update-error', 'children'),
        Output('et-update-upload', 'contents'),
        Output('et-update-upload-filename', 'children')
    ],
    Input('et-update-submit-btn', 'n_clicks'),
    [
        State('et-update-goal-id-store', 'data'),
        State('et-update-status', 'value'),
        State('et-update-progress', 'value'),
        State('et-update-delay-reason', 'value'),
        State('et-update-comment', 'value'),
        State('et-update-delegate-chk', 'value'),
        State('et-update-delegate-assignee', 'value'),
        State('et-update-due-date', 'date'),
        State('et-update-upload', 'contents'),
        State('et-update-upload', 'filename'),
        State('et-update-delegate-due-date', 'date'),
        State('et-update-delegate-remarks', 'value')
    ],
    prevent_initial_call=True
)
def save_goal_updates(n_clicks, goal_id, status, progress, delay_reason, comment, delegate_chk, delegate_assignee, due_date, upload_contents, upload_filename, delegate_due_date, delegate_remarks):
    email = session.get('email')
    if not email or not goal_id:
        return no_update
        
    if not status:
        return no_update, "Please select a Status.", no_update, no_update
        
    if progress is None:
        return no_update, "Please select a Progress percentage.", no_update, no_update
        
    # Check if delegation requested but assignee or due date omitted
    if delegate_chk:
        if not delegate_assignee:
            return no_update, "Please select a subordinate to delegate to.", no_update, no_update
        if not delegate_due_date:
            return no_update, "Delegated Due Date is required.", no_update, no_update
        
    attachments = []
    if upload_contents and upload_filename:
        import base64
        contents_list = upload_contents if isinstance(upload_contents, list) else [upload_contents]
        filenames_list = upload_filename if isinstance(upload_filename, list) else [upload_filename]
        for content, name in zip(contents_list, filenames_list):
            try:
                content_type, content_string = content.split(',')
                file_bytes = base64.b64decode(content_string)
                if len(file_bytes) > 10 * 1024 * 1024:
                    return no_update, f"File size exceeds the 10MB limit for {name}.", no_update, no_update
                attachments.append({"name": name, "data": file_bytes})
            except Exception as e:
                return no_update, f"Error parsing uploaded file {name}: {str(e)}", no_update, no_update
            
    try:
        # 1. Update parent goal details
        success = update_goal(
            goal_id=goal_id,
            email=email,
            status=status,
            progress=progress,
            delay_reason=delay_reason.strip() if delay_reason else "",
            comment=comment,
            due_date=due_date,
            attachments=attachments
        )
        
        if not success:
            return no_update, "Failed to update goal database.", no_update, no_update
            
        # 2. Handle delegation logic (create child goal)
        if delegate_chk and delegate_assignee:
            # Query parent details to inherit
            chain = get_goal_hierarchy(goal_id)
            parent_node = next((node for node in chain if node['goal_id'] == goal_id), None)
            
            if parent_node:
                assignees = delegate_assignee if isinstance(delegate_assignee, list) else [delegate_assignee]
                for email_to in assignees:
                    create_goal(
                        title=parent_node['title'],
                        description=delegate_remarks.strip() if (delegate_remarks and delegate_remarks.strip()) else parent_node['description'],
                        category=parent_node['goal_category'],
                        priority=parent_node['priority'],
                        assigned_by_email=email,
                        assigned_to_email=email_to,
                        due_date=delegate_due_date,
                        expected_outcome=parent_node['expected_outcome'],
                        parent_goal_id=goal_id
                    )
                
        return False, "", None, ""
    except Exception as e:
        return no_update, f"Error saving updates: {str(e)}", no_update, no_update


# ---------------------------------------------------
# Callback 10: Uploader Filename Displays
# ---------------------------------------------------
@callback(
    Output('et-create-upload-filename', 'children'),
    Input('et-create-upload', 'filename'),
    prevent_initial_call=True
)
def update_create_filename(filename):
    if filename:
        if isinstance(filename, list):
            return f"Selected files: {', '.join(filename)}"
        return f"Selected file: {filename}"
    return ""

@callback(
    Output('et-update-upload-filename', 'children'),
    Input('et-update-upload', 'filename'),
    prevent_initial_call=True
)
def update_update_filename(filename):
    if filename:
        if isinstance(filename, list):
            return f"Selected files: {', '.join(filename)}"
        return f"Selected file: {filename}"
    return ""


# ---------------------------------------------------
# Callback 11: Download Attachment
# ---------------------------------------------------
@callback(
    [
        Output('et-download-attachment', 'data'),
        Output('et-download-selection-modal', 'is_open'),
        Output('et-download-selection-list', 'children'),
        Output('goals-table', 'active_cell', allow_duplicate=True)
    ],
    Input('goals-table', 'active_cell'),
    State('goals-table', 'data'),
    prevent_initial_call=True
)
def download_attachment(active_cell, table_data):
    if not active_cell or not table_data:
        return no_update
        
    row_idx = active_cell['row']
    col_id = active_cell['column_id']
    
    if col_id == 'attachment_name':
        if row_idx < len(table_data):
            row_data = table_data[row_idx]
            goal_id = row_data['goal_id']
            email = session.get('email')
            if not email:
                return no_update, no_update, no_update, None
                
            # Fetch attachments uploaded by the currently logged-in user
            user_atts = get_goal_attachments_by_user(goal_id, email)
            if not user_atts:
                return no_update, no_update, no_update, None
                
            if len(user_atts) == 1:
                # Direct download
                att_id = user_atts[0]['attachment_id']
                att = get_attachment_by_id(att_id)
                if att and att.get('attachment_name') and att.get('attachment_data'):
                    filename = att['attachment_name']
                    file_data = att['attachment_data']
                    return dcc.send_bytes(file_data, filename), False, [], None
            else:
                # Open selection modal
                list_of_buttons = html.Div([
                    dbc.Button(
                        f"Download {att['attachment_name']}",
                        id={'type': 'et-chain-attachment', 'index': att['attachment_id']},
                        className='et-btn-glow-blue m-2 w-100'
                    ) for att in user_atts
                ])
                return no_update, True, list_of_buttons, None
                
    return no_update, no_update, no_update, no_update


# ---------------------------------------------------
# Callback 12: Download Attachment from Delegation Chain Box or Selection Modal
# ---------------------------------------------------
@callback(
    Output('et-download-attachment', 'data', allow_duplicate=True),
    Input({'type': 'et-chain-attachment', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def download_chain_attachment(n_clicks_list):
    ctx = callback_context
    if not ctx.triggered:
        return no_update
        
    trigger = ctx.triggered[0]
    prop_id = trigger['prop_id']
    
    val = trigger['value']
    if not val:
        return no_update
        
    import json
    try:
        id_str = prop_id.split('.n_clicks')[0]
        clicked_id = json.loads(id_str)
        attachment_id = clicked_id['index']
        
        # Fetch attachment from database
        att = get_attachment_by_id(attachment_id)
        if att and att.get('attachment_name') and att.get('attachment_data'):
            filename = att['attachment_name']
            file_data = att['attachment_data']
            return dcc.send_bytes(file_data, filename)
    except Exception as e:
        print(f"Error downloading attachment: {e}")
        
    return no_update


# ---------------------------------------------------
# Callback 13: Close Selection Modal
# ---------------------------------------------------
@callback(
    Output('et-download-selection-modal', 'is_open', allow_duplicate=True),
    Input('et-download-selection-close-btn', 'n_clicks'),
    prevent_initial_call=True
)
def close_selection_modal(n_clicks):
    if n_clicks:
        return False
    return no_update


@callback(
    Output('et-download-selection-modal', 'is_open', allow_duplicate=True),
    Input({'type': 'et-chain-attachment', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def close_selection_modal_on_download(n_clicks_list):
    ctx = callback_context
    if not ctx.triggered:
        return no_update
        
    trigger = ctx.triggered[0]
    val = trigger['value']
    if val:
        return False
    return no_update


# ---------------------------------------------------
# Callback 14: Centralized reset for goals-table active_cell selection
# ---------------------------------------------------
@callback(
    Output('goals-table', 'active_cell', allow_duplicate=True),
    [
        Input('et-update-modal', 'is_open'),
        Input('et-hierarchy-modal', 'is_open'),
        Input('et-delete-confirm-modal', 'is_open'),
        Input('et-download-selection-modal', 'is_open')
    ],
    prevent_initial_call=True
)
def reset_active_cell(modal_upd, modal_hier, modal_del, modal_dl):
    # If all modal popups are closed (False), reset the active cell to None
    if not modal_upd and not modal_hier and not modal_del and not modal_dl:
        return None
    return no_update
