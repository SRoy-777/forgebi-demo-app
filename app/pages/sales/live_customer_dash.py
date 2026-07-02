from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime, timezone, timedelta
import pandas as pd
from backend.services.directors_hub.live_customer_service import get_live_customer_data

# ---------------------------------------------------
# Indian Number Formatting Helper
# ---------------------------------------------------
def indian_number_format(value):
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
    return formatted

# ---------------------------------------------------
# Layout
# ---------------------------------------------------
layout = html.Div(
    className='odometer-page-container',
    children=[
        # Include custom stylesheet directly in layout for reliability
        html.Link(rel="stylesheet", href="/assets/live_customer.css"),
        
        # Interval components (1 second ticks for live polling & clock updates)
        dcc.Interval(
            id='live-customer-interval',
            interval=1000,  # 1,000ms = 1s
            n_intervals=0
        ),
        
        # Top Left Minimal Back Navigation (Modified to point to Sales)
        html.A(
            "← Sales Department",
            href="/sales",
            className='odometer-back-btn text-muted text-decoration-none small font-weight-bold',
            style={'position': 'absolute', 'top': '25px', 'left': '25px'}
        ),
        
        # Header Section - Clock and Label
        html.Div(
            className='odometer-header-clock',
            children=[
                html.Div("Orient Organization Time", className='odometer-clock-label'),
                html.Div(id='live-customer-clock', className='odometer-clock-time', children="00:00:00")
            ]
        ),
        
        # Main Display Section
        html.Div(
            className='odometer-main-content',
            children=[
                html.Div("LIVE REGISTERED CUSTOMERS", className='odometer-main-label'),
                html.Div(id='live-customer-digits', className='odometer-counter-wrapper')
            ]
        ),
        
        # Footer Section
        html.Div(
            className='odometer-info-footer',
            children=[
                html.Div(id='live-customer-footer-msg', className='odometer-footer-msg', children="Live Counter Active"),
                html.Div(id='live-customer-sub-footer', className='odometer-latest-date', children="Last Sync: --:--:--")
            ]
        )
    ]
)

# ---------------------------------------------------
# Callback: Tick Clock, Fetch Live Data and Update Odometer
# ---------------------------------------------------
@callback(
    Output('live-customer-clock', 'children'),
    Output('live-customer-digits', 'children'),
    Output('live-customer-sub-footer', 'children'),
    Input('live-customer-interval', 'n_intervals')
)
def update_live_customer_display(n_intervals):
    # 1. Update clock using India Standard Time (IST)
    IST = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(IST)
    clock_time = now.strftime("%H:%M:%S")
    
    # 2. Fetch live data from R2 (cached in-memory for TTL duration)
    df = get_live_customer_data()
    total_customers = len(df)
    
    # 3. Format customer count for odometer (e.g. 4,43,932)
    formatted_count = indian_number_format(total_customers)
    
    # 4. Build odometer digit strips
    digit_cards = []
    for idx, char in enumerate(formatted_count):
        if char == ',':
            # Comma separator
            digit_cards.append(
                html.Div(
                    ",",
                    className='odometer-separator',
                    key=f"sep-{idx}"
                )
            )
        else:
            # Digit roll wheel
            digit_val = int(char)
            digit_cards.append(
                html.Div(
                    className='odometer-digit-container',
                    key=f"wheel-{idx}-{digit_val}",
                    children=[
                        html.Div(
                            className='odometer-digit-strip',
                            style={'transform': f'translateY(-{digit_val * 10}%)'},
                            children=[
                                html.Div(str(d), className='odometer-digit', key=f"d-{idx}-{d}") for d in range(10)
                            ]
                        )
                    ]
                )
            )
            
    # 5. Last sync timestamp in India Standard Time (IST)
    from backend.services.directors_hub.live_customer_service import _last_fetch_time
    if _last_fetch_time > 0:
        sync_time = datetime.fromtimestamp(_last_fetch_time, tz=IST).strftime("%I:%M:%S %p")
    else:
        sync_time = now.strftime("%I:%M:%S %p")
    last_sync_text = f"Last Sync: {sync_time}"
    
    return clock_time, digit_cards, last_sync_text
