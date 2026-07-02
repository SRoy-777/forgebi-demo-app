import sys
import os
import io
from datetime import datetime, date
import pandas as pd
import numpy as np

import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table, callback, Input, Output, State, no_update

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.cache.data_cache import (
    merged_sales_df,
    rm_zm_df,
    employee_performance_df
)
from backend.services.sales.employee_performance import get_employee_performance_data

# ---------------------------------------------------
# Indian Number Formatting
# ---------------------------------------------------
def indian_format(value, decimals=0):
    try:
        value = float(value)
    except Exception:
        return value

    negative = value < 0
    value = abs(value)
    integer_part = int(value)
    decimal_part = round(value - integer_part, decimals)

    integer_str = str(integer_part)
    if len(integer_str) > 3:
        last_three = integer_str[-3:]
        remaining = integer_str[:-3]
        parts = []
        while len(remaining) > 2:
            parts.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            parts.insert(0, remaining)
        integer_str = ",".join(parts) + "," + last_three

    if decimals > 0:
        decimal_str = f"{decimal_part:.{decimals}f}"[1:]
    else:
        decimal_str = ""

    formatted = integer_str + decimal_str
    if negative:
        formatted = "-" + formatted
    return formatted

# ---------------------------------------------------
# Default Date Bounds (YTD: April 1st of latest invoice year to latest invoice date)
# ---------------------------------------------------
latest_invoice_dt = pd.to_datetime(merged_sales_df['Invoice Date'].max())
if latest_invoice_dt.month >= 4:
    start_year = latest_invoice_dt.year
else:
    start_year = latest_invoice_dt.year - 1

default_start_date = date(start_year, 4, 1)
default_end_date = latest_invoice_dt.date()
last_updated_str = latest_invoice_dt.strftime('%d-%b-%Y')

# ---------------------------------------------------
# Dynamic Filter Dropdowns Setup
# ---------------------------------------------------
def get_dropdown_options():
    locs = sorted(employee_performance_df['location_name'].dropna().unique().tolist())
    rms = sorted(rm_zm_df['rm'].dropna().unique().tolist())
    zms = sorted(rm_zm_df['zm'].dropna().unique().tolist())
    
    employees = []
    # Drop duplicates by employee_code
    unique_emps = employee_performance_df.drop_duplicates('employee_code').sort_values('employee_name')
    for _, r in unique_emps.iterrows():
        employees.append({
            'label': f"{r['employee_code']} - {r['employee_name']}",
            'value': r['employee_code']
        })
        
    return locs, rms, zms, employees

location_list, rm_list, zm_list, employee_list = get_dropdown_options()

# ---------------------------------------------------
# UI Styles
# ---------------------------------------------------
TABLE_STYLE = {
    'page_action': 'none',
    'fill_width': True,
    'fixed_rows': {'headers': True},
    'fixed_columns': {'headers': True, 'data': 8},
    'style_table': {
        'overflowX': 'auto',
        'overflowY': 'auto',
        'maxHeight': '500px',
        'width': '100%',
        'minWidth': '100%',
        'border': '1px solid #CBD5E1',
        'borderRadius': '6px'
    },
    'style_cell': {
        'fontSize': '11px',
        'fontFamily': "'Outfit', 'Inter', 'Segoe UI', Arial, sans-serif",
        'padding': '6px',
        'textAlign': 'center',
        'whiteSpace': 'normal',
        'minWidth': '80px',
        'width': '80px',
        'maxWidth': '120px',
        'border': '1px solid #E2E8F0',
        'color': '#334155'
    },
    'style_header': {
        'backgroundColor': '#1E293B',
        'color': '#F8FAFC',
        'fontWeight': 'bold',
        'fontSize': '11px',
        'textAlign': 'center',
        'border': '1px solid #CBD5E1',
        'height': '40px',
        'minHeight': '40px',
        'maxHeight': '40px',
        'lineHeight': '14px',
        'fontFamily': "'Outfit', sans-serif"
    },
    'style_data': {
        'backgroundColor': 'white',
        'color': '#334155'
    },
    'style_data_conditional': [
        # Bold and grey out for first 8 frozen columns
        {'if': {'column_id': 'location_code'}, 'fontWeight': 'bold', 'backgroundColor': '#F8FAFC'},
        {'if': {'column_id': 'location_name'}, 'fontWeight': 'bold', 'backgroundColor': '#F8FAFC'},
        {'if': {'column_id': 'employee_code'}, 'fontWeight': 'bold', 'backgroundColor': '#F8FAFC'},
        {'if': {'column_id': 'employee_name'}, 'fontWeight': 'bold', 'backgroundColor': '#F8FAFC'},
        {'if': {'column_id': 'job_title'}, 'fontWeight': 'bold', 'backgroundColor': '#F8FAFC'},
        {'if': {'column_id': 'date_joined'}, 'fontWeight': 'bold', 'backgroundColor': '#F8FAFC'},
        {'if': {'column_id': 'employment_status'}, 'fontWeight': 'bold', 'backgroundColor': '#F8FAFC'},
        {'if': {'column_id': 'final_rank'}, 'fontWeight': 'bold', 'backgroundColor': '#F8FAFC'},
        
        # NSV Rank (points)
        {'if': {'column_id': 'nsv_rank'}, 'fontWeight': 'bold'},
        {'if': {'column_id': 'gold_rank'}, 'fontWeight': 'bold'},
        {'if': {'column_id': 'diamond_rank'}, 'fontWeight': 'bold'},
        {'if': {'column_id': 'silver_rank'}, 'fontWeight': 'bold'},
        {'if': {'column_id': 'mohor_rank'}, 'fontWeight': 'bold'},
        {'if': {'column_id': 'gemstone_rank'}, 'fontWeight': 'bold'},
        {'if': {'column_id': 'ss_count_rank'}, 'fontWeight': 'bold'},
        {'if': {'column_id': 'ss_value_rank'}, 'fontWeight': 'bold'},

        # NSV % Diff heat mapping
        {'if': {'column_id': 'nsv_pct', 'filter_query': '{nsv_rank} = 5'}, 'backgroundColor': '#A7F3D0', 'color': '#064E3B'},
        {'if': {'column_id': 'nsv_pct', 'filter_query': '{nsv_rank} = 4'}, 'backgroundColor': '#D1FAE5', 'color': '#065F46'},
        {'if': {'column_id': 'nsv_pct', 'filter_query': '{nsv_rank} = 3'}, 'backgroundColor': '#FEF3C7', 'color': '#92400E'},
        {'if': {'column_id': 'nsv_pct', 'filter_query': '{nsv_rank} = 2'}, 'backgroundColor': '#FFEDD5', 'color': '#9A3412'},
        {'if': {'column_id': 'nsv_pct', 'filter_query': '{nsv_rank} = 1'}, 'backgroundColor': '#FEE2E2', 'color': '#991B1B'},

        # Gold % Diff heat mapping
        {'if': {'column_id': 'gold_pct', 'filter_query': '{gold_rank} = 5'}, 'backgroundColor': '#A7F3D0', 'color': '#064E3B'},
        {'if': {'column_id': 'gold_pct', 'filter_query': '{gold_rank} = 4'}, 'backgroundColor': '#D1FAE5', 'color': '#065F46'},
        {'if': {'column_id': 'gold_pct', 'filter_query': '{gold_rank} = 3'}, 'backgroundColor': '#FEF3C7', 'color': '#92400E'},
        {'if': {'column_id': 'gold_pct', 'filter_query': '{gold_rank} = 2'}, 'backgroundColor': '#FFEDD5', 'color': '#9A3412'},
        {'if': {'column_id': 'gold_pct', 'filter_query': '{gold_rank} = 1'}, 'backgroundColor': '#FEE2E2', 'color': '#991B1B'},

        # Diamond % Diff heat mapping
        {'if': {'column_id': 'diamond_pct', 'filter_query': '{diamond_rank} = 5'}, 'backgroundColor': '#A7F3D0', 'color': '#064E3B'},
        {'if': {'column_id': 'diamond_pct', 'filter_query': '{diamond_rank} = 4'}, 'backgroundColor': '#D1FAE5', 'color': '#065F46'},
        {'if': {'column_id': 'diamond_pct', 'filter_query': '{diamond_rank} = 3'}, 'backgroundColor': '#FEF3C7', 'color': '#92400E'},
        {'if': {'column_id': 'diamond_pct', 'filter_query': '{diamond_rank} = 2'}, 'backgroundColor': '#FFEDD5', 'color': '#9A3412'},
        {'if': {'column_id': 'diamond_pct', 'filter_query': '{diamond_rank} = 1'}, 'backgroundColor': '#FEE2E2', 'color': '#991B1B'},

        # Silver % Diff heat mapping
        {'if': {'column_id': 'silver_pct', 'filter_query': '{silver_rank} = 5'}, 'backgroundColor': '#A7F3D0', 'color': '#064E3B'},
        {'if': {'column_id': 'silver_pct', 'filter_query': '{silver_rank} = 4'}, 'backgroundColor': '#D1FAE5', 'color': '#065F46'},
        {'if': {'column_id': 'silver_pct', 'filter_query': '{silver_rank} = 3'}, 'backgroundColor': '#FEF3C7', 'color': '#92400E'},
        {'if': {'column_id': 'silver_pct', 'filter_query': '{silver_rank} = 2'}, 'backgroundColor': '#FFEDD5', 'color': '#9A3412'},
        {'if': {'column_id': 'silver_pct', 'filter_query': '{silver_rank} = 1'}, 'backgroundColor': '#FEE2E2', 'color': '#991B1B'},

        # Mohor % Diff heat mapping
        {'if': {'column_id': 'mohor_pct', 'filter_query': '{mohor_rank} = 5'}, 'backgroundColor': '#A7F3D0', 'color': '#064E3B'},
        {'if': {'column_id': 'mohor_pct', 'filter_query': '{mohor_rank} = 4'}, 'backgroundColor': '#D1FAE5', 'color': '#065F46'},
        {'if': {'column_id': 'mohor_pct', 'filter_query': '{mohor_rank} = 3'}, 'backgroundColor': '#FEF3C7', 'color': '#92400E'},
        {'if': {'column_id': 'mohor_pct', 'filter_query': '{mohor_rank} = 2'}, 'backgroundColor': '#FFEDD5', 'color': '#9A3412'},
        {'if': {'column_id': 'mohor_pct', 'filter_query': '{mohor_rank} = 1'}, 'backgroundColor': '#FEE2E2', 'color': '#991B1B'},

        # Gemstone % Diff heat mapping
        {'if': {'column_id': 'gemstone_pct', 'filter_query': '{gemstone_rank} = 5'}, 'backgroundColor': '#A7F3D0', 'color': '#064E3B'},
        {'if': {'column_id': 'gemstone_pct', 'filter_query': '{gemstone_rank} = 4'}, 'backgroundColor': '#D1FAE5', 'color': '#065F46'},
        {'if': {'column_id': 'gemstone_pct', 'filter_query': '{gemstone_rank} = 3'}, 'backgroundColor': '#FEF3C7', 'color': '#92400E'},
        {'if': {'column_id': 'gemstone_pct', 'filter_query': '{gemstone_rank} = 2'}, 'backgroundColor': '#FFEDD5', 'color': '#9A3412'},
        {'if': {'column_id': 'gemstone_pct', 'filter_query': '{gemstone_rank} = 1'}, 'backgroundColor': '#FEE2E2', 'color': '#991B1B'},

        # SS Count % Diff heat mapping
        {'if': {'column_id': 'ss_count_pct', 'filter_query': '{ss_count_rank} = 5'}, 'backgroundColor': '#A7F3D0', 'color': '#064E3B'},
        {'if': {'column_id': 'ss_count_pct', 'filter_query': '{ss_count_rank} = 4'}, 'backgroundColor': '#D1FAE5', 'color': '#065F46'},
        {'if': {'column_id': 'ss_count_pct', 'filter_query': '{ss_count_rank} = 3'}, 'backgroundColor': '#FEF3C7', 'color': '#92400E'},
        {'if': {'column_id': 'ss_count_pct', 'filter_query': '{ss_count_rank} = 2'}, 'backgroundColor': '#FFEDD5', 'color': '#9A3412'},
        {'if': {'column_id': 'ss_count_pct', 'filter_query': '{ss_count_rank} = 1'}, 'backgroundColor': '#FEE2E2', 'color': '#991B1B'},

        # SS Value % Diff heat mapping
        {'if': {'column_id': 'ss_value_pct', 'filter_query': '{ss_value_rank} = 5'}, 'backgroundColor': '#A7F3D0', 'color': '#064E3B'},
        {'if': {'column_id': 'ss_value_pct', 'filter_query': '{ss_value_rank} = 4'}, 'backgroundColor': '#D1FAE5', 'color': '#065F46'},
        {'if': {'column_id': 'ss_value_pct', 'filter_query': '{ss_value_rank} = 3'}, 'backgroundColor': '#FEF3C7', 'color': '#92400E'},
        {'if': {'column_id': 'ss_value_pct', 'filter_query': '{ss_value_rank} = 2'}, 'backgroundColor': '#FFEDD5', 'color': '#9A3412'},
        {'if': {'column_id': 'ss_value_pct', 'filter_query': '{ss_value_rank} = 1'}, 'backgroundColor': '#FEE2E2', 'color': '#991B1B'},
    ]
}

# ---------------------------------------------------
# Layout Elements Builder
# ---------------------------------------------------
def build_kpi1_card(title, value, unit="", style=None):
    try:
        val_f = indian_format(value, 0)
        if unit:
            val_f = f"{val_f} {unit}"
    except Exception:
        val_f = str(value)
        
    return dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.Div(title, style={'fontSize': '10px', 'fontWeight': '600', 'textAlign': 'center', 'color': '#1E40AF', 'fontFamily': "'Outfit', sans-serif"}),
                html.Div(val_f, style={'fontSize': '13px', 'fontWeight': 'bold', 'textAlign': 'center', 'marginTop': '4px', 'color': '#1E3A8A', 'fontFamily': "'Outfit', sans-serif"})
            ], style={'padding': '6px'})
        ], style={'backgroundColor': '#EFF6FF', 'borderRadius': '8px', 'border': '1px solid #BFDBFE', 'height': '58px', 'justifyContent': 'center', 'boxShadow': '0px 1px 3px rgba(0,0,0,0.05)'})
    ], xs=6, sm=4, md=1, lg=1, className='mb-2', style=style)

def build_kpi2_card(title, ach_pct, variance, unit_type='value'):
    # Dynamic Color based on achievement
    bg_color = '#FEE2E2' # Soft Red (< 75%)
    text_color = '#991B1B'
    border_color = '#FCA5A5'
    if ach_pct >= 90.0:
        bg_color = '#D1FAE5' # Soft Green (>= 90%)
        text_color = '#065F46'
        border_color = '#6EE7B7'
    elif ach_pct >= 75.0:
        bg_color = '#FEF3C7' # Soft Yellow (75% - 90%)
        text_color = '#92400E'
        border_color = '#FCD34D'
        
    sign = "+" if variance >= 0 else ""
    
    if unit_type == 'weight':
        var_f = f"{sign}{indian_format(variance, 3)} g"
    elif unit_type == 'ct':
        var_f = f"{sign}{indian_format(variance, 3)} ct"
    elif unit_type == 'count':
        var_f = f"{sign}{indian_format(variance, 0)} Count"
    else: # value / currency
        var_f = f"{sign}{indian_format(variance, 0)}"
    
    return dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.Div(title, style={'fontSize': '10px', 'fontWeight': '600', 'textAlign': 'center', 'color': text_color, 'fontFamily': "'Outfit', sans-serif"}),
                html.Div(f"{ach_pct:.2f}%", style={'fontSize': '14px', 'fontWeight': 'bold', 'textAlign': 'center', 'marginTop': '2px', 'color': text_color, 'fontFamily': "'Outfit', sans-serif"}),
                html.Div(var_f, style={'fontSize': '9px', 'textAlign': 'center', 'color': text_color, 'opacity': 0.85, 'fontFamily': "'Outfit', sans-serif"})
            ], style={'padding': '4px'})
        ], style={'backgroundColor': bg_color, 'borderRadius': '8px', 'border': f'1px solid {border_color}', 'height': '62px', 'justifyContent': 'center', 'boxShadow': '0px 1px 3px rgba(0,0,0,0.05)'})
    ], xs=6, sm=4, md=1, lg=1, className='mb-2')

def build_top_employee_row(label, name, score, metrics_dict):
    metrics_cols = []
    
    # NSV
    metrics_cols.append(dbc.Col([
        html.Div("NSV", style={'fontSize': '9px', 'color': 'gray'}),
        html.Div(indian_format(metrics_dict.get('nsv', 0), 0), style={'fontSize': '11px', 'fontWeight': 'bold'})
    ], width=1, style={'textAlign': 'center'}))
    
    # Gold
    metrics_cols.append(dbc.Col([
        html.Div("Gold (g)", style={'fontSize': '9px', 'color': 'gray'}),
        html.Div(indian_format(metrics_dict.get('gold', 0), 3), style={'fontSize': '11px', 'fontWeight': 'bold'})
    ], width=1, style={'textAlign': 'center'}))
    
    # Diamond
    metrics_cols.append(dbc.Col([
        html.Div("Diamond (ct)", style={'fontSize': '9px', 'color': 'gray'}),
        html.Div(indian_format(metrics_dict.get('diamond', 0), 3), style={'fontSize': '11px', 'fontWeight': 'bold'})
    ], width=1, style={'textAlign': 'center'}))
    
    # Silver
    metrics_cols.append(dbc.Col([
        html.Div("Silver (g)", style={'fontSize': '9px', 'color': 'gray'}),
        html.Div(indian_format(metrics_dict.get('silver', 0), 3), style={'fontSize': '11px', 'fontWeight': 'bold'})
    ], width=1, style={'textAlign': 'center'}))
    
    # Mohor
    metrics_cols.append(dbc.Col([
        html.Div("Mohor NSV", style={'fontSize': '9px', 'color': 'gray'}),
        html.Div(indian_format(metrics_dict.get('mohor', 0), 0), style={'fontSize': '11px', 'fontWeight': 'bold'})
    ], width=1, style={'textAlign': 'center'}))
    
    # Gemstone
    metrics_cols.append(dbc.Col([
        html.Div("Gemstone NSV", style={'fontSize': '9px', 'color': 'gray'}),
        html.Div(indian_format(metrics_dict.get('gemstone', 0), 0), style={'fontSize': '11px', 'fontWeight': 'bold'})
    ], width=1, style={'textAlign': 'center'}))
    
    # SS Count
    metrics_cols.append(dbc.Col([
        html.Div("SS Count", style={'fontSize': '9px', 'color': 'gray'}),
        html.Div(indian_format(metrics_dict.get('ss_count', 0), 0), style={'fontSize': '11px', 'fontWeight': 'bold'})
    ], width=1, style={'textAlign': 'center'}))
    
    # SS Value
    metrics_cols.append(dbc.Col([
        html.Div("SS Value", style={'fontSize': '9px', 'color': 'gray'}),
        html.Div(indian_format(metrics_dict.get('ss_value', 0), 0), style={'fontSize': '11px', 'fontWeight': 'bold'})
    ], width=1, style={'textAlign': 'center'}))

    return dbc.Row([
        dbc.Col([
            html.Div(label, style={'fontWeight': 'bold', 'color': '#1E40AF', 'fontSize': '12px', 'fontFamily': "'Outfit', sans-serif"}),
        ], width=1),
        dbc.Col([
            html.Div(name, style={'fontWeight': 'bold', 'fontSize': '12px', 'fontFamily': "'Outfit', sans-serif"}),
        ], width=2),
        dbc.Col([
            html.Span("Final Score: ", style={'fontSize': '10px', 'color': '#64748B', 'fontFamily': "'Outfit', sans-serif"}),
            html.Span(f"{score:.2f}", style={'fontWeight': 'bold', 'color': '#2563EB', 'fontSize': '12px', 'fontFamily': "'Outfit', sans-serif"})
        ], width=1),
        *metrics_cols
    ], className='py-2 border-bottom align-items-center', style={'backgroundColor': '#FFFFFF', 'margin': '0px', 'borderRadius': '4px'})

# ---------------------------------------------------
# Layout
# ---------------------------------------------------
layout = html.Div(
    className='inv-premium-page-blue',
    children=dbc.Container([
        # ---------------------------------------------------
        # Header
        # ---------------------------------------------------
        dbc.Row([
            dbc.Col([
                html.A(
                    dbc.Button(
                        "← Sales Department",
                        className='inv-btn-blue-dark px-3 py-1',
                        size='sm'
                    ),
                    href="/sales",
                    style={'textDecoration': 'none'}
                ),
                html.H2(
                    'Employee Performance Analysis',
                    className='fw-bold mt-3 mb-1',
                    style={'fontFamily': 'Outfit', 'color': '#0F172A'}
                ),
            ], width=8),
            dbc.Col([
                html.Div(
                    f"Last Updated : {last_updated_str}",
                    className='text-end fw-bold mb-2',
                    style={'color': '#1E3A8A', 'fontFamily': 'Outfit'},
                ),
                html.Div([
                    dbc.Button("Export Data", id='employee-performance-export-btn', className='inv-btn-blue-dark px-3 py-1 me-2 shadow-sm', size='sm'),
                    dbc.Button("Enter", id='employee-performance-enter-btn', className='inv-btn-blue px-4 py-1 shadow-sm', size='sm')
                ], className='text-end')
            ], width=4)
        ], className='mb-4 mt-2 align-items-end'),
        
        dcc.Download(id='employee-performance-download'),
        
        # ---------------------------------------------------
        # Filter Panel
        # ---------------------------------------------------
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Date Range", className="fw-bold mb-1 small text-muted"),
                        dcc.DatePickerRange(
                            id='employee-performance-date-filter',
                            display_format='DD-MMM-YYYY',
                            start_date=default_start_date,
                            end_date=default_end_date
                        )
                    ], width=3),
                    dbc.Col([
                        html.Label("Location", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='employee-performance-location-filter',
                            options=[{'label': l, 'value': l} for l in location_list],
                            multi=True,
                            placeholder='Select Location'
                        )
                    ], width=2),
                    dbc.Col([
                        html.Label("RM", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='employee-performance-rm-filter',
                            options=[{'label': r, 'value': r} for r in rm_list],
                            multi=True,
                            placeholder='Select RM'
                        )
                    ], width=2),
                    dbc.Col([
                        html.Label("ZM", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='employee-performance-zm-filter',
                            options=[{'label': z, 'value': z} for z in zm_list],
                            multi=True,
                            placeholder='Select ZM'
                        )
                    ], width=2),
                    dbc.Col([
                        html.Label("Find Employee", className="fw-bold mb-1 small text-muted"),
                        dcc.Dropdown(
                            id='employee-performance-emp-filter',
                            options=employee_list,
                            placeholder='Search Code/Name',
                            searchable=True
                        )
                    ], width=3)
                ])
            ])
        ], className='inv-blue-card mb-4'),
        
        # ---------------------------------------------------
        # KPIs Container
        # ---------------------------------------------------
        dcc.Loading(
            html.Div(id='employee-performance-kpis-container'),
            type='circle'
        ),
        
        # ---------------------------------------------------
        # Master Table Container
        # ---------------------------------------------------
        dcc.Loading(
            html.Div(id='employee-performance-table-container'),
            type='circle'
        )
    ], fluid=True, style={'padding': '0px'})
)

# ---------------------------------------------------
# Callback 1: Render Dashboard (Triggered by Enter Button)
# ---------------------------------------------------
@callback(
    [
        Output('employee-performance-kpis-container', 'children'),
        Output('employee-performance-table-container', 'children')
    ],
    [
        Input('employee-performance-enter-btn', 'n_clicks'),
        Input('url', 'pathname') # Trigger load on initial mount
    ],
    [
        State('employee-performance-date-filter', 'start_date'),
        State('employee-performance-date-filter', 'end_date'),
        State('employee-performance-location-filter', 'value'),
        State('employee-performance-rm-filter', 'value'),
        State('employee-performance-zm-filter', 'value'),
        State('employee-performance-emp-filter', 'value')
    ]
)
def render_dashboard(n_clicks, pathname, start_date, end_date, locations, rms, zms, employee):
    if not start_date or not end_date:
        return html.Div(), html.Div()
        
    # Query Data
    data = get_employee_performance_data(
        start_date=start_date,
        end_date=end_date,
        locations=locations,
        rms=rms,
        zms=zms,
        employee_search=employee
    )
    
    master_df = data['master_table']
    kpis_1 = data['kpis_layer1']
    kpis_2 = data['kpis_layer2']
    top_3 = data['top_3_employees']
    
    if master_df.empty:
        empty_msg = html.Div(
            "No active employees found matching the selection filters.",
            style={'color': 'white', 'textAlign': 'center', 'padding': '50px', 'fontWeight': 'bold'}
        )
        return empty_msg, html.Div()
        
    # --- Build KPI Layer 1 (Achievements) ---
    kpi1_row = dbc.Row([
        build_kpi1_card("Total Manpower", kpis_1['total_manpower']),
        build_kpi1_card("NSV", kpis_1['nsv'], style={'minWidth': '115px'}),
        build_kpi1_card("Gold", kpis_1['gold'], "g"),
        build_kpi1_card("Diamond", kpis_1['diamond'], "ct"),
        build_kpi1_card("Silver", kpis_1['silver'], "g"),
        build_kpi1_card("Mohor NSV", kpis_1['mohor']),
        build_kpi1_card("Gemstone NSV", kpis_1['gemstone']),
        build_kpi1_card("SS Count", kpis_1['ss_count']),
        build_kpi1_card("SS Value", kpis_1['ss_value'])
    ], className='g-2')
    
    # --- Build KPI Layer 2 (Completion % & Variance) ---
    kpi2_row = dbc.Row([
        # Dummy card for spacing/matching size of manpower card
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div("Target Achievement", style={'fontSize': '9px', 'textAlign': 'center', 'fontWeight': 'bold', 'color': 'white', 'fontFamily': "'Outfit', sans-serif"}),
                    html.Div("Summary Layer", style={'fontSize': '11px', 'textAlign': 'center', 'fontWeight': 'bold', 'color': 'white', 'fontFamily': "'Outfit', sans-serif"})
                ], style={'padding': '4px'})
            ], style={'backgroundColor': '#1E293B', 'border': 'none', 'height': '62px', 'justifyContent': 'center'})
        ], xs=6, sm=4, md=1, lg=1, className='mb-2'),
        
        build_kpi2_card("NSV % Diff", kpis_2['nsv']['pct'], kpis_2['nsv']['diff'], 'value'),
        build_kpi2_card("Gold % Diff", kpis_2['gold']['pct'], kpis_2['gold']['diff'], 'weight'),
        build_kpi2_card("Diamond % Diff", kpis_2['diamond']['pct'], kpis_2['diamond']['diff'], 'ct'),
        build_kpi2_card("Silver % Diff", kpis_2['silver']['pct'], kpis_2['silver']['diff'], 'weight'),
        build_kpi2_card("Mohor % Diff", kpis_2['mohor']['pct'], kpis_2['mohor']['diff'], 'value'),
        build_kpi2_card("Gemstone % Diff", kpis_2['gemstone']['pct'], kpis_2['gemstone']['diff'], 'value'),
        build_kpi2_card("SS Count % Diff", kpis_2['ss_count']['pct'], kpis_2['ss_count']['diff'], 'count'),
        build_kpi2_card("SS Value % Diff", kpis_2['ss_value']['pct'], kpis_2['ss_value']['diff'], 'value')
    ], className='g-2')

    # --- Build KPI Layer 3 (Top 3 Performers) ---
    top_3_rows = []
    labels = ["1st Employee", "2nd Employee", "3rd Employee"]
    for i, emp in enumerate(top_3):
        top_3_rows.append(
            build_top_employee_row(
                labels[i],
                emp['name'],
                emp['final_rank'],
                emp
            )
        )
        
    top_3_section = dbc.Card([
        dbc.CardHeader(
            html.H5("Top 3 Performing Employees", className='fw-bold mb-0', style={'color': '#0F172A', 'fontFamily': 'Outfit'}),
            style={'backgroundColor': '#F8FAFC', 'borderBottom': '1px solid #E2E8F0'}
        ),
        dbc.CardBody(top_3_rows, style={'padding': '10px', 'backgroundColor': '#FFFFFF'})
    ], className='inv-blue-card mb-4')

    kpi_layout = html.Div([
        html.H5("Performance Highlights", className='fw-bold mb-2 mt-4', style={'color': '#0F172A', 'fontFamily': 'Outfit'}),
        kpi1_row,
        kpi2_row,
        html.Br(),
        top_3_section
    ])
    
    # --- Format Master Table Data for Display ---
    disp_df = master_df.copy()
    
    # Formats lists
    currency_cols = ['location_nsv_target', 'location_ly_nsv', 'location_ty_nsv', 'nsv_target', 'nsv_achieved', 'nsv_lytd', 'mohor_nsv_target', 'mohor_achieved', 'stone_nsv_target', 'gemstone_achieved', 'ss_value_target', 'ss_value_achieved', 'platinum_achieved_nsv']
    weight_cols = ['gold_g_target', 'gold_achieved', 'diamond_ct_target', 'diamond_achieved', 'silver_g_target', 'silver_achieved', 'platinum_achieved_gms']
    count_cols = ['ss_count_target', 'ss_count_achieved']
    pct_cols = ['nsv_pct', 'nsv_contrib', 'gold_pct', 'diamond_pct', 'silver_pct', 'mohor_pct', 'gemstone_pct', 'ss_count_pct', 'ss_value_pct']
    score_cols = ['nsv_rank', 'gold_rank', 'diamond_rank', 'silver_rank', 'mohor_rank', 'gemstone_rank', 'ss_count_rank', 'ss_value_rank']
    
    for col in currency_cols:
        disp_df[col] = disp_df[col].apply(lambda x: indian_format(x, 0))
    for col in weight_cols:
        disp_df[col] = disp_df[col].apply(lambda x: indian_format(x, 3))
    for col in count_cols:
        disp_df[col] = disp_df[col].apply(lambda x: indian_format(x, 0))
    for col in pct_cols:
        disp_df[col] = disp_df[col].apply(lambda x: f"{x:.2f}%")
    for col in score_cols:
        disp_df[col] = disp_df[col].apply(lambda x: int(x))
        
    disp_df['final_rank'] = disp_df['final_rank'].apply(lambda x: f"{x:.2f}")
    
    # Format new metadata fields
    disp_df['date_joined'] = disp_df['date_joined'].apply(lambda x: pd.to_datetime(x).strftime('%d-%b-%Y') if pd.notna(x) and str(x).strip() != "" else "")
    disp_df['job_title'] = disp_df['job_title'].fillna("")
    disp_df['employment_status'] = disp_df['employment_status'].fillna("")

    # Build Merged Columns Headers List
    columns = [
        # Location Info
        {'name': ['Location', 'Code'], 'id': 'location_code'},
        {'name': ['Location', 'Name'], 'id': 'location_name'},
        # Employee Info
        {'name': ['Employee', 'Code'], 'id': 'employee_code'},
        {'name': ['Employee', 'Name'], 'id': 'employee_name'},
        {'name': ['Employee', 'Job Title'], 'id': 'job_title'},
        {'name': ['Employee', 'Date Joined'], 'id': 'date_joined'},
        {'name': ['Employee', 'Status'], 'id': 'employment_status'},
        {'name': ['Employee', 'Final Score'], 'id': 'final_rank'},
        
        # Location Totals
        {'name': ['Location', 'NSV Target'], 'id': 'location_nsv_target'},
        {'name': ['Location', 'LY NSV achieved'], 'id': 'location_ly_nsv'},
        {'name': ['Location', 'TY NSV Achieved'], 'id': 'location_ty_nsv'},
        
        # NSV
        {'name': ['NSV', 'Target'], 'id': 'nsv_target'},
        {'name': ['NSV', 'Achieved'], 'id': 'nsv_achieved'},
        {'name': ['NSV', 'LYTD'], 'id': 'nsv_lytd'},
        {'name': ['NSV', '% Difference'], 'id': 'nsv_pct'},
        {'name': ['NSV', 'Contribution %'], 'id': 'nsv_contrib'},
        {'name': ['NSV', 'Score'], 'id': 'nsv_rank'},
        
        # Gold
        {'name': ['Gold', 'Target'], 'id': 'gold_g_target'},
        {'name': ['Gold', 'Achieved'], 'id': 'gold_achieved'},
        {'name': ['Gold', '% Difference'], 'id': 'gold_pct'},
        {'name': ['Gold', 'Score'], 'id': 'gold_rank'},
        
        # Diamond
        {'name': ['Diamond', 'Target'], 'id': 'diamond_ct_target'},
        {'name': ['Diamond', 'Achieved'], 'id': 'diamond_achieved'},
        {'name': ['Diamond', '% Difference'], 'id': 'diamond_pct'},
        {'name': ['Diamond', 'Score'], 'id': 'diamond_rank'},
        
        # Silver
        {'name': ['Silver', 'Target'], 'id': 'silver_g_target'},
        {'name': ['Silver', 'Achieved'], 'id': 'silver_achieved'},
        {'name': ['Silver', '% Difference'], 'id': 'silver_pct'},
        {'name': ['Silver', 'Score'], 'id': 'silver_rank'},
        
        # Mohor
        {'name': ['Mohor', 'Target'], 'id': 'mohor_nsv_target'},
        {'name': ['Mohor', 'Achieved'], 'id': 'mohor_achieved'},
        {'name': ['Mohor', '% Difference'], 'id': 'mohor_pct'},
        {'name': ['Mohor', 'Score'], 'id': 'mohor_rank'},
        
        # Gemstone
        {'name': ['Gemstone', 'Target'], 'id': 'stone_nsv_target'},
        {'name': ['Gemstone', 'Achieved'], 'id': 'gemstone_achieved'},
        {'name': ['Gemstone', '% Difference'], 'id': 'gemstone_pct'},
        {'name': ['Gemstone', 'Score'], 'id': 'gemstone_rank'},
        
        # SS Count
        {'name': ['SS Count', 'Target'], 'id': 'ss_count_target'},
        {'name': ['SS Count', 'Achieved'], 'id': 'ss_count_achieved'},
        {'name': ['SS Count', '% Difference'], 'id': 'ss_count_pct'},
        {'name': ['SS Count', 'Score'], 'id': 'ss_count_rank'},
        
        # SS Value
        {'name': ['SS Value', 'Target'], 'id': 'ss_value_target'},
        {'name': ['SS Value', 'Achieved'], 'id': 'ss_value_achieved'},
        {'name': ['SS Value', '% Difference'], 'id': 'ss_value_pct'},
        {'name': ['SS Value', 'Score'], 'id': 'ss_value_rank'},
        
        # Platinum
        {'name': ['Platinum', 'Achieved Gms'], 'id': 'platinum_achieved_gms'},
        {'name': ['Platinum', 'Achieved NSV'], 'id': 'platinum_achieved_nsv'},
    ]

    table_card = dbc.Card([
        dbc.CardHeader(
            html.H5("Employee Performance Matrix", className='fw-bold mb-0', style={'color': '#0F172A', 'fontFamily': 'Outfit'}),
            style={'backgroundColor': '#F8FAFC', 'borderBottom': '1px solid #E2E8F0'}
        ),
        dbc.CardBody([
            dash_table.DataTable(
                id='employee-performance-table',
                data=disp_df.to_dict('records'),
                columns=columns,
                merge_duplicate_headers=True,
                sort_action='custom',
                sort_by=[{'column_id': 'final_rank', 'direction': 'desc'}],
                **TABLE_STYLE
            )
        ], style={'padding': '6px'})
    ], className='inv-blue-card mb-4')

    return kpi_layout, table_card

# ---------------------------------------------------
# Callback 2: Export Data Workbook (Excel)
# ---------------------------------------------------
@callback(
    Output('employee-performance-download', 'data'),
    Input('employee-performance-export-btn', 'n_clicks'),
    [
        State('employee-performance-date-filter', 'start_date'),
        State('employee-performance-date-filter', 'end_date'),
        State('employee-performance-location-filter', 'value'),
        State('employee-performance-rm-filter', 'value'),
        State('employee-performance-zm-filter', 'value'),
        State('employee-performance-emp-filter', 'value')
    ],
    prevent_initial_call=True
)
def export_data(n_clicks, start_date, end_date, locations, rms, zms, employee):

    # Log Export Activity
    from backend.services.activity_logger import log_activity
    from flask import session
    log_activity(
        session.get('email'),
        "Employee Performance Analysis Dashboard",
        action="Export Data",
        filters={"start_date": start_date, "end_date": end_date, "locations": locations, "rms": rms, "zms": zms, "employee": employee}
    )

    if not start_date or not end_date:
        return no_update
        
    data = get_employee_performance_data(
        start_date=start_date,
        end_date=end_date,
        locations=locations,
        rms=rms,
        zms=zms,
        employee_search=employee
    )
    
    master_df = data['master_table']
    kpis_1 = data['kpis_layer1']
    kpis_2 = data['kpis_layer2']
    
    if master_df.empty:
        return no_update
        
    # Prepare Cover / Summary sheet
    summary_data = {
        'Metric': ['Total Manpower', 'NSV', 'Gold (g)', 'Diamond (ct)', 'Silver (g)', 'Mohor NSV', 'Gemstone NSV', 'SS Count', 'SS Value'],
        'Achieved': [
            kpis_1['total_manpower'],
            kpis_1['nsv'],
            kpis_1['gold'],
            kpis_1['diamond'],
            kpis_1['silver'],
            kpis_1['mohor'],
            kpis_1['gemstone'],
            kpis_1['ss_count'],
            kpis_1['ss_value']
        ],
        'Target': [
            "-",
            kpis_2['nsv']['target'],
            kpis_2['gold']['target'],
            kpis_2['diamond']['target'],
            kpis_2['silver']['target'],
            kpis_2['mohor']['target'],
            kpis_2['gemstone']['target'],
            kpis_2['ss_count']['target'],
            kpis_2['ss_value']['target']
        ],
        'Variance (Achieved - Target)': [
            "-",
            kpis_2['nsv']['diff'],
            kpis_2['gold']['diff'],
            kpis_2['diamond']['diff'],
            kpis_2['silver']['diff'],
            kpis_2['mohor']['diff'],
            kpis_2['gemstone']['diff'],
            kpis_2['ss_count']['diff'],
            kpis_2['ss_value']['diff']
        ],
        'Achievement %': [
            "-",
            f"{kpis_2['nsv']['pct']:.2f}%",
            f"{kpis_2['gold']['pct']:.2f}%",
            f"{kpis_2['diamond']['pct']:.2f}%",
            f"{kpis_2['silver']['pct']:.2f}%",
            f"{kpis_2['mohor']['pct']:.2f}%",
            f"{kpis_2['gemstone']['pct']:.2f}%",
            f"{kpis_2['ss_count']['pct']:.2f}%",
            f"{kpis_2['ss_value']['pct']:.2f}%"
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    
    # Clean master columns headers for excel export
    clean_master = master_df.copy()
    clean_master.rename(columns={
        'location_code': 'Location Code',
        'location_name': 'Location Name',
        'employee_code': 'Employee Code',
        'employee_name': 'Employee Name',
        'job_title': 'Employee Job Title',
        'date_joined': 'Employee Date Joined',
        'employment_status': 'Employment Status',
        'final_rank': 'Employee Final Score',
        'location_nsv_target': 'Location NSV Target',
        'location_ly_nsv': 'Location LY NSV achieved',
        'location_ty_nsv': 'Location TY NSV Achieved',
        'nsv_target': 'NSV Target',
        'nsv_achieved': 'NSV Achieved',
        'nsv_lytd': 'NSV LYTD',
        'nsv_pct': 'NSV % Difference',
        'nsv_contrib': 'NSV Contribution %',
        'nsv_rank': 'NSV Score',
        'platinum_achieved_gms': 'Platinum Achieved Gms',
        'platinum_achieved_nsv': 'Platinum Achieved NSV',
        'gold_g_target': 'Gold Target',
        'gold_achieved': 'Gold Achieved',
        'gold_pct': 'Gold % Difference',
        'gold_rank': 'Gold Score',
        'diamond_ct_target': 'Diamond Target',
        'diamond_achieved': 'Diamond Achieved',
        'diamond_pct': 'Diamond % Difference',
        'diamond_rank': 'Diamond Score',
        'silver_g_target': 'Silver Target',
        'silver_achieved': 'Silver Achieved',
        'silver_pct': 'Silver % Difference',
        'silver_rank': 'Silver Score',
        'mohor_nsv_target': 'Mohor Target',
        'mohor_achieved': 'Mohor Achieved',
        'mohor_pct': 'Mohor % Difference',
        'mohor_rank': 'Mohor Score',
        'stone_nsv_target': 'Gemstone Target',
        'gemstone_achieved': 'Gemstone Achieved',
        'gemstone_pct': 'Gemstone % Difference',
        'gemstone_rank': 'Gemstone Score',
        'ss_count_target': 'SS Count Target',
        'ss_count_achieved': 'SS Count Achieved',
        'ss_count_pct': 'SS Count % Difference',
        'ss_count_rank': 'SS Count Score',
        'ss_value_target': 'SS Value Target',
        'ss_value_achieved': 'SS Value Achieved',
        'ss_value_pct': 'SS Value % Difference',
        'ss_value_rank': 'SS Value Score'
    }, inplace=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Summary KPIs
        summary_df.to_excel(writer, sheet_name='Summary KPIs', index=False)
        # Sheet 2: Master Performance Matrix
        clean_master.to_excel(writer, sheet_name='Performance Matrix', index=False)
        
    output.seek(0)
    filename = f"employee_performance_{start_date}_to_{end_date}.xlsx"
    return dcc.send_bytes(output.getvalue(), filename)


# ---------------------------------------------------
# Helper and Callback: Custom Sorting
# ---------------------------------------------------
def parse_formatted_value(val):
    if val is None or val == "":
        return -999999999.0
    val_str = str(val).strip()
    val_str = val_str.replace(",", "").replace(" g", "").replace(" ct", "").replace("%", "")
    try:
        return float(val_str)
    except ValueError:
        return val_str.lower()

@callback(
    Output('employee-performance-table', 'data'),
    Input('employee-performance-table', 'sort_by'),
    State('employee-performance-table', 'data'),
    prevent_initial_call=True
)
def sort_table(sort_by, data):
    if not data or not sort_by:
        return no_update
        
    df = pd.DataFrame(data)
    
    # We will create temporary columns to sort on
    temp_cols = []
    asc_list = []
    
    for sort_col in sort_by:
        col_id = sort_col['column_id']
        ascending = sort_col['direction'] == 'asc'
        
        temp_col = f"_sort_{col_id}"
        df[temp_col] = df[col_id].apply(parse_formatted_value)
        temp_cols.append(temp_col)
        asc_list.append(ascending)
        
    # Perform stable sort
    df = df.sort_values(by=temp_cols, ascending=asc_list, kind='stable')
    
    # Drop the temporary columns
    df = df.drop(columns=temp_cols)
    
    return df.to_dict('records')


# ---------------------------------------------------
# Dynamic Location Dropdown Options RLS
# ---------------------------------------------------
from dash import callback, Output, Input

@callback(
    Output('employee-performance-location-filter', 'options'),
    Input('employee-performance-location-filter', 'id')
)
def populate_employee_performance_location_filter_options(_):
    from flask import session
    from backend.cache.data_cache import rm_zm_df
    allowed_locations = session.get('locations', [])
    if not allowed_locations:
        return []
    if 'ALL' in allowed_locations:
        locs = sorted(rm_zm_df['location'].dropna().unique().tolist())
    else:
        locs = sorted(allowed_locations)
    return [{'label': i, 'value': i} for i in locs]
