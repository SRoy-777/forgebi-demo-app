from dash import html, dcc, callback, clientside_callback, Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime, timezone, timedelta
import pandas as pd
from backend.services.directors_hub.live_sales_service import get_today_live_sales_data

# ---------------------------------------------------
# Indian Formatting Helper for UI
# ---------------------------------------------------
def indian_format(value):
    try:
        value = int(round(float(value)))
    except Exception:
        return str(value)
        
    negative = value < 0
    value = abs(value)
    integer_str = str(value)
    
    if len(integer_str) > 3:
        last_three = integer_str[-3:]
        remaining = integer_str[:-3]
        parts = []
        while len(remaining) > 2:
            parts.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            parts.insert(0, remaining)
        integer_str = ','.join(parts) + ',' + last_three
        
    formatted = integer_str
    if negative:
        formatted = '-' + formatted
    return "₹ " + formatted

# ---------------------------------------------------
# Daily Target Helper for UI & Celebrations
# ---------------------------------------------------
def get_today_daily_target(rm=None, zm=None):
    try:
        from backend.services.sales.performance import get_nsv_performance
        
        # Get today's date in IST
        IST = timezone(timedelta(hours=5, minutes=30))
        today_ist = datetime.now(IST).date()
        
        # Start of current month
        start_date = today_ist.replace(day=1)
        
        # Yesterday
        yesterday_ist = today_ist - timedelta(days=1)
        
        # Handle first day of the month boundary
        if yesterday_ist.month != today_ist.month:
            yesterday_ist = today_ist
            
        df_perf = get_nsv_performance(start_date, yesterday_ist, rm=rm, zm=zm)
        if df_perf is None or df_perf.empty:
            return 0.0
            
        return float(df_perf['required_run_rate'].sum())
    except Exception as e:
        print(f"[Live Target Error] {e}")
        return 0.0

# ---------------------------------------------------
# Yesterday Sales Helper
# ---------------------------------------------------
def get_yesterday_sales_up_to_now(rm=None, zm=None):
    try:
        import os
        from backend.services.rls import get_allowed_locations
        
        path = os.path.join("data", "processed", "1_live", "live_posted_estimate.parquet")
        if not os.path.exists(path):
            return 0.0
            
        df = pd.read_parquet(path)
        if df.empty:
            return 0.0
            
        # Get dates
        IST = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(IST)
        today_ist = now_ist.date()
        yesterday_ist = today_ist - timedelta(days=1)
        current_time_of_day = now_ist.time()
        
        # Convert Date column to check yesterday's sales
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        df_yesterday = df[df['Date'] == yesterday_ist].copy()
        
        if df_yesterday.empty:
            return 0.0
            
        # Apply RLS allowed locations filter (same as today's sales)
        allowed_locations = get_allowed_locations()
        if 'ALL' not in allowed_locations:
            df_yesterday['Location_Name'] = df_yesterday['Location_Name'].fillna("UNKNOWN").astype(str).str.strip().str.upper()
            allowed_clean = [loc.upper().strip() for loc in allowed_locations]
            df_yesterday = df_yesterday[df_yesterday['Location_Name'].isin(allowed_clean)]
            
        if df_yesterday.empty:
            return 0.0
            
        # Apply RM/ZM location filters
        if rm or zm:
            allowed_locs = get_locations_for_rm_zm(rm, zm)
            df_yesterday['Location_Name_Upper'] = df_yesterday['Location_Name'].fillna("").astype(str).str.strip().str.upper()
            df_yesterday = df_yesterday[df_yesterday['Location_Name_Upper'].isin(allowed_locs)]
            
        if df_yesterday.empty:
            return 0.0
            
        # Parse SystemCreatedAt to filter by time
        df_yesterday['SystemCreatedAt_IST'] = pd.to_datetime(df_yesterday['SystemCreatedAt'], format='ISO8601').dt.tz_convert('Asia/Kolkata')
        df_yesterday = df_yesterday[df_yesterday['SystemCreatedAt_IST'].dt.time <= current_time_of_day]
        
        total_yesterday_sales = df_yesterday['Final_Amount_to_Customer'].sum()
        return float(total_yesterday_sales)
    except Exception as e:
        print(f"[Yesterday Sales Error] {e}")
        return 0.0

# ---------------------------------------------------
# RM ZM Helper for Location Mapping
# ---------------------------------------------------
def get_locations_for_rm_zm(rm=None, zm=None):
    try:
        from backend.cache.data_cache import rm_zm_df
        df_loc = rm_zm_df.copy()
        if rm:
            df_loc = df_loc[df_loc['rm'] == rm]
        if zm:
            df_loc = df_loc[df_loc['zm'] == zm]
        return set(df_loc['location'].str.upper().str.strip().unique())
    except Exception as e:
        print(f"[RM ZM Helper Error] {e}")
        return set()

def get_rm_zm_options():
    try:
        from backend.cache.data_cache import rm_zm_df
        from backend.services.rls import get_allowed_locations
        
        df_loc = rm_zm_df.copy()
        allowed = get_allowed_locations()
        if 'ALL' not in allowed:
            df_loc['location_upper'] = df_loc['location'].fillna("").astype(str).str.strip().str.upper()
            allowed_clean = [loc.upper().strip() for loc in allowed]
            df_loc = df_loc[df_loc['location_upper'].isin(allowed_clean)]
            
        rms = sorted([x for x in df_loc['rm'].dropna().unique() if x != ''])
        zms = sorted([x for x in df_loc['zm'].dropna().unique() if x != ''])
        
        rm_options = [{'label': x, 'value': x} for x in rms]
        zm_options = [{'label': x, 'value': x} for x in zms]
        return rm_options, zm_options
    except Exception as e:
        print(f"[RM ZM Options Error] {e}")
        return [], []

# ---------------------------------------------------
# Layout
# ---------------------------------------------------
layout = html.Div(
    className='countdown-page-container',
    children=[
        # Include custom stylesheet directly in layout with a cache-busting query parameter
        html.Link(rel="stylesheet", href=f"/assets/countdown.css?v={int(datetime.now().timestamp())}"),
        
        # Hidden inputs/stores for JS processing
        dcc.Store(id='live-sales-store', data=None),
        html.Div(id='clientside-trigger-output', style={'display': 'none'}),
        
        # Interval for clientside clock ticking (1 second)
        dcc.Interval(
            id='clock-interval',
            interval=1000,  # 1000ms = 1s
            n_intervals=0
        ),
        
        # Interval for live data polling (15 seconds)
        dcc.Interval(
            id='data-interval',
            interval=15000,  # 15000ms = 15s
            n_intervals=0
        ),
        
        # ---------------------------------------------------
        # HERO SCREEN: Time & Accumulated Sales (100vh)
        # ---------------------------------------------------
        html.Div(
            className='countdown-hero-screen',
            children=[
                # Top Header Row (Back navigation & filters on left, audio toggle on right)
                html.Div(
                    className='countdown-top-bar',
                    children=[
                        html.Div(
                            className='countdown-top-left-group',
                            children=[
                                html.Div(
                                    className='countdown-filter-row',
                                    children=[
                                        dcc.Dropdown(
                                            id='countdown-rm-dropdown',
                                            placeholder='Filter RM',
                                            options=[],
                                            clearable=True,
                                            searchable=True,
                                            className='countdown-dropdown'
                                        ),
                                        dcc.Dropdown(
                                            id='countdown-zm-dropdown',
                                            placeholder='Filter ZM',
                                            options=[],
                                            clearable=True,
                                            searchable=True,
                                            className='countdown-dropdown'
                                        )
                                    ]
                                )
                            ]
                        ),
                        # Top Right Audio Toggle Button (Mute/Unmute)
                        html.Button(
                            id='audio-toggle-btn',
                            className='audio-toggle-btn',
                            children=[
                                html.Span("🔊", id='audio-toggle-icon')
                            ]
                        )
                    ]
                ),
                
                # Header Section - Clock and Label
                html.Div(
                    className='countdown-header-clock',
                    children=[
                        html.Div("Orient Organization Time", className='countdown-clock-label'),
                        html.Div(id='countdown-clock', className='countdown-clock-time', children="00:00:00")
                    ]
                ),
                
                # Main Display Section
                html.Div(
                    className='countdown-main-content',
                    children=[
                        html.Div(
                            id='sales-card',
                            className='sales-card',
                            children=[
                                html.Div(id='countdown-main-label', className='countdown-main-label', children="TODAY'S ACCUMULATED SALES"),
                                html.Div(id='countdown-digits', className='flip-counter-wrapper')
                            ]
                        ),
                        
                        # Yesterday comparison text block (visually smaller, sitting above scroll indicator)
                        html.Div(
                            id='yesterday-comparison-container',
                            className='yesterday-comparison-container',
                            children=[
                                html.Span("Yesterday this time:", className='comparison-label'),
                                html.Span(id='yesterday-sales-val', className='comparison-value', children="₹ 0")
                            ]
                        )
                    ]
                ),
                
                # Scroll Indicator
                html.Div(
                    className='countdown-scroll-indicator',
                    children=[
                        html.Div("Scroll Down for Branch Charts", className='countdown-scroll-text'),
                        html.Div("▼", className='countdown-scroll-arrow')
                    ]
                )
            ]
        ),
        
        # ---------------------------------------------------
        # CHARTS SCREEN: Live Bar Charts & Footer (Pushed below fold)
        # ---------------------------------------------------
        html.Div(
            className='countdown-charts-screen',
            children=[
                # Dynamic Bar Charts Section
                html.Div(
                    className='live-bar-charts-section',
                    children=[
                        # Sales by Branch Card
                        html.Div(
                            className='live-chart-container',
                            children=[
                                html.Div("Sales by Branch (Live)", className='live-chart-title'),
                                html.Div(id='live-branch-sales-chart')
                            ]
                        ),
                        # Count of Customers by Branch Card
                        html.Div(
                            className='live-chart-container',
                            children=[
                                html.Div("Customers by Branch (Live)", className='live-chart-title'),
                                html.Div(id='live-branch-customers-chart')
                            ]
                        )
                    ]
                ),
                
                # Footer Section
                html.Div(
                    className='countdown-info-footer',
                    children=[
                        html.Div(id='countdown-footer-msg', className='countdown-footer-msg', children="Live Counter Active"),
                        html.Div(id='countdown-sub-footer', className='countdown-latest-date', children="Last Sync: --:--:--")
                    ]
                )
            ]
        )
    ]
)

# ---------------------------------------------------
# Clientside Callback: Tick Clock (Lag-Free & Zero Server Cost)
# ---------------------------------------------------
clientside_callback(
    """
    function(n_intervals) {
        const options = { 
            timeZone: 'Asia/Kolkata', 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit', 
            hour12: false 
        };
        return new Date().toLocaleTimeString('en-US', options);
    }
    """,
    Output('countdown-clock', 'children'),
    Input('clock-interval', 'n_intervals')
)

# Clientside Callback: Delegate Sales Display Updates to JS
clientside_callback(
    """
    function(data) {
        if (!data) return "";
        if (window.updateSalesVisuals) {
            window.updateSalesVisuals(data.total_sales, data.daily_target);
        }
        return "";
    }
    """,
    Output('clientside-trigger-output', 'children'),
    Input('live-sales-store', 'data')
)

# ---------------------------------------------------
# Callback: Fetch Live Data and Update Sales Counter & Charts
# ---------------------------------------------------
@callback(
    Output('live-sales-store', 'data'),
    Output('yesterday-sales-val', 'children'),
    Output('live-branch-sales-chart', 'children'),
    Output('live-branch-customers-chart', 'children'),
    Output('countdown-sub-footer', 'children'),
    Output('countdown-rm-dropdown', 'options'),
    Output('countdown-zm-dropdown', 'options'),
    Input('data-interval', 'n_intervals'),
    Input('countdown-rm-dropdown', 'value'),
    Input('countdown-zm-dropdown', 'value')
)
def update_live_data(n_intervals, rm_val, zm_val):
    # 1. Fetch live today's sales data (non-blocking in service layer)
    df_today = get_today_live_sales_data()
    
    # Apply RM/ZM location filters
    if rm_val or zm_val:
        allowed_locs = get_locations_for_rm_zm(rm_val, zm_val)
        df_today['Location_Name_Upper'] = df_today['Location_Name'].fillna("").astype(str).str.strip().str.upper()
        df_today = df_today[df_today['Location_Name_Upper'].isin(allowed_locs)]
        
    # 2. Sum total sales
    total_sales = 0.0
    if not df_today.empty and 'Final_Amount_to_Customer' in df_today.columns:
        total_sales = df_today['Final_Amount_to_Customer'].sum()
        
    # 3. Fetch daily target and yesterday's sales with RM/ZM context
    daily_target = get_today_daily_target(rm=rm_val, zm=zm_val)
    sales_data = {'total_sales': float(total_sales), 'daily_target': float(daily_target)}
    
    yesterday_sales = get_yesterday_sales_up_to_now(rm=rm_val, zm=zm_val)
    formatted_yesterday_sales = indian_format(yesterday_sales)
    
    # 4. Build Branch Sales Horizontal Bar List (Sorted highest to lowest)
    sales_rows = []
    sales_height = '3.8rem'
    if not df_today.empty and 'Final_Amount_to_Customer' in df_today.columns:
        # Group, sum, and sort
        sales_by_branch = df_today.groupby('Location_Name')['Final_Amount_to_Customer'].sum().reset_index()
        sales_by_branch.columns = ['Location', 'Sales']
        sales_by_branch = sales_by_branch.sort_values(by='Sales', ascending=False)
        
        max_sales = sales_by_branch['Sales'].max() if sales_by_branch['Sales'].max() > 0 else 1
        
        for idx, row in enumerate(sales_by_branch.itertuples(index=False)):
            loc = row.Location
            val = row.Sales
            ratio = (val / max_sales) * 100
            val_str = indian_format(val)
            
            if ratio < 18:
                track_children = [
                    html.Div(
                        className='live-bar-fill-sales',
                        style={'width': f'{ratio}%', 'flexShrink': 0}
                    ),
                    html.Span(val_str, className='live-bar-value outside-bar')
                ]
            else:
                track_children = [
                    html.Div(
                        className='live-bar-fill-sales',
                        style={'width': f'{ratio}%', 'flexShrink': 0},
                        children=[
                            html.Span(val_str, className='live-bar-value')
                        ]
                    )
                ]
                
            sales_rows.append(
                html.Div(
                    className='live-bar-row',
                    key=f"sales-row-{loc}",
                    style={'top': f'{idx * 3.8}rem'},
                    children=[
                        html.Div(loc, className='live-bar-label'),
                        html.Div(
                            className='live-bar-track',
                            children=track_children
                        )
                    ]
                )
            )
        sales_height = f'{len(sales_by_branch) * 3.8}rem'
    else:
        sales_rows = [html.Div("No sales recorded today", className='text-muted text-center py-3', style={'color': '#a89375'})]
        
    sales_chart_wrapper = html.Div(
        sales_rows, 
        className='live-bar-list-wrapper', 
        style={'height': sales_height}
    )
    
    # 6. Build Branch Customer Count Horizontal Bar List (Sorted highest to lowest)
    cust_rows = []
    cust_height = '3.8rem'
    if not df_today.empty and 'Customer_Code' in df_today.columns:
        # Group, count unique, and sort
        cust_by_branch = df_today.groupby('Location_Name')['Customer_Code'].nunique().reset_index()
        cust_by_branch.columns = ['Location', 'Customers']
        cust_by_branch = cust_by_branch.sort_values(by='Customers', ascending=False)
        
        max_cust = cust_by_branch['Customers'].max() if cust_by_branch['Customers'].max() > 0 else 1
        
        for idx, row in enumerate(cust_by_branch.itertuples(index=False)):
            loc = row.Location
            val = row.Customers
            ratio = (val / max_cust) * 100
            val_str = f"{val:,} Customers"
            
            if ratio < 18:
                track_children = [
                    html.Div(
                        className='live-bar-fill-customers',
                        style={'width': f'{ratio}%', 'flexShrink': 0}
                    ),
                    html.Span(val_str, className='live-bar-value outside-bar')
                ]
            else:
                track_children = [
                    html.Div(
                        className='live-bar-fill-customers',
                        style={'width': f'{ratio}%', 'flexShrink': 0},
                        children=[
                            html.Span(val_str, className='live-bar-value')
                        ]
                    )
                ]
                
            cust_rows.append(
                html.Div(
                    className='live-bar-row',
                    key=f"cust-row-{loc}",
                    style={'top': f'{idx * 3.8}rem'},
                    children=[
                        html.Div(loc, className='live-bar-label'),
                        html.Div(
                            className='live-bar-track',
                            children=track_children
                        )
                    ]
                )
            )
        cust_height = f'{len(cust_by_branch) * 3.8}rem'
    else:
        cust_rows = [html.Div("No customers recorded today", className='text-muted text-center py-3', style={'color': '#a89375'})]
        
    cust_chart_wrapper = html.Div(
        cust_rows, 
        className='live-bar-list-wrapper', 
        style={'height': cust_height}
    )
    
    # 7. Last Sync Timestamp of R2 file (in IST)
    from backend.services.directors_hub.live_sales_service import get_last_sync_time
    sync_time = get_last_sync_time()
    sub_footer_text = f"Last Sync: {sync_time}"
    
    rm_opts, zm_opts = get_rm_zm_options()
    return sales_data, formatted_yesterday_sales, sales_chart_wrapper, cust_chart_wrapper, sub_footer_text, rm_opts, zm_opts

