# app/pages/sales/geo_analytics_dash.py

import os
import json
import pandas as pd
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import dash_leaflet as dl

from backend.services.sales.geo_analytics_service import (
    get_branch_coords,
    get_filter_options,
    get_filtered_dashboard_data
)

# ---------------------------------------------------
# Load District Boundaries GeoJSON
# ---------------------------------------------------
GEOJSON_PATH = "app/assets/WestBengal.geojson"
geojson_data = None
try:
    if os.path.exists(GEOJSON_PATH):
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)
    else:
        print(f"Warning: West Bengal GeoJSON not found at {GEOJSON_PATH}")
except Exception as e:
    print(f"Error loading GeoJSON file: {e}")

# ---------------------------------------------------
# Fetch Filter Bounds & Lists
# ---------------------------------------------------
filter_meta = get_filter_options()

default_start_date = filter_meta['min_date'].date()
default_end_date = filter_meta['max_date'].date()

# ---------------------------------------------------
# Helper Formatting Functions
# ---------------------------------------------------
def format_inr(number):
    if number is None:
        return "₹ 0.00"
    negative = number < 0
    number = abs(number)
    if number >= 10000000:
        val = number / 10000000.0
        s = f"₹ {val:.2f} Cr"
    elif number >= 100000:
        val = number / 100000.0
        s = f"₹ {val:.2f} L"
    else:
        s = f"₹ {number:,.2f}"
    if negative:
        s = "-" + s
    return s

def format_number(val, decimals=0):
    if val is None:
        return "0"
    try:
        if decimals == 0:
            return f"{int(round(val)):,}"
        else:
            return f"{val:,.{decimals}f}"
    except Exception:
        return str(val)

# ---------------------------------------------------
# Helper functions to build Leaflet Markers
# ---------------------------------------------------
def make_branch_markers(branches):
    """Generates custom golden glowing marker beacons for physical stores."""
    markers = []
    custom_icon = dict(
        iconUrl="/assets/branch_beacon.png",
        iconSize=[24, 24],
        iconAnchor=[12, 12],
        popupAnchor=[0, -12]
    )
    
    for idx, b in enumerate(branches):
        lat = float(b['Store Lat'])
        lon = float(b['Store Long'])
        name = str(b['Location Name'])
        code = str(b['Location Code'])
        pincode = int(b['Store Pincode'])
        
        # Leaflet custom tooltip html content
        tooltip_content = html.Div([
            html.Div("ForgeBI Branch Beacon", style={'color': '#a0a0a0', 'fontSize': '9px', 'textTransform': 'uppercase', 'letterSpacing': '0.5px'}),
            html.Div(name, className="fw-bold", style={'color': '#e5c158', 'fontSize': '13px'}),
            html.Div(f"Location Code: {code}", style={'color': '#ffffff', 'fontSize': '11px'}),
            html.Div(f"Store Pincode: {pincode}", style={'color': '#a0a0a0', 'fontSize': '10px'})
        ], style={'fontFamily': "'Outfit', sans-serif"})
        
        markers.append(
            dl.Marker(
                position=[lat, lon],
                icon=custom_icon,
                id=f"geo-branch-marker-{idx}",
                children=[
                    dl.Tooltip(
                        tooltip_content,
                        className="branch-tooltip-card",
                        direction="top",
                        sticky=False
                    )
                ]
            )
        )
    return markers

def make_hover_markers(points, radius_selection, is_drilldown=False):
    """Generates visible or transparent circle markers containing glassmorphic HUD tooltips."""
    markers = []
    
    # Custom hover radius mapping (matches heat radiuses roughly)
    radius_map = {
        'small': 14,
        'medium': 24,
        'large': 36
    }
    hover_radius = radius_map.get(radius_selection, 24)
    
    # If in branch drill-down mode, calculate the min and max revenue of these points to build the color scale
    min_rev, max_rev = 0, 0
    if is_drilldown and points:
        revenues = [p['Revenue'] for p in points]
        if revenues:
            min_rev = min(revenues)
            max_rev = max(revenues)
            
    for idx, p in enumerate(points):
        lat = float(p['Latitude'])
        lon = float(p['Longitude'])
        pin = int(p['Pincode'])
        revenue = float(p['Revenue'])
        customers = int(p['Customers'])
        invoices = int(p['Invoices'])
        gold = float(p['Gold_w'])
        diamond = float(p['Diamond_cts'])
        branch = str(p['Primary Branch'])
        
        # Add deterministic jitter based on Pincode to scatter overlapping points around stores
        # This keeps the layout clean, prevents stacking, and makes overlapping circles visible
        import math
        angle = (pin * 45) % 360
        # Radius between 0.005 and 0.012 degrees (~500m to 1.2km) to clear the store icon
        radius = 0.005 + ((pin * 17) % 70) / 10000.0
        lat += radius * math.sin(math.radians(angle))
        lon += radius * math.cos(math.radians(angle))
        
        gold_str = f"{gold/1000.0:.2f} kg" if gold >= 1000 else f"{gold:.1f} g"
        
        # Color-coding relative to active branch's min/max revenue
        if is_drilldown:
            if max_rev > min_rev:
                norm = (revenue - min_rev) / (max_rev - min_rev)
            else:
                norm = 1.0
            
            # Map norm (0..1) to White -> Yellow -> Red
            if norm <= 0.5:
                # White (255, 255, 255) to Yellow (255, 235, 59)
                factor = norm / 0.5
                r = 255
                g = 255 - int((255 - 235) * factor)
                b = 255 - int((255 - 59) * factor)
            else:
                # Yellow (255, 235, 59) to Red (244, 67, 54)
                factor = (norm - 0.5) / 0.5
                r = 255 - int((255 - 244) * factor)
                g = 235 - int((235 - 67) * factor)
                b = 59 - int((59 - 54) * factor)
                
            marker_color = f"rgb({r}, {g}, {b})"
            marker_radius = 1200 # 1.2 km radius (visible catchment)
            fill_opacity = 0.85
            stroke_val = True
            border_color = "#ffffff"
            border_opacity = 0.4
            weight_val = 1
        else:
            marker_color = "transparent"
            marker_radius = hover_radius * 100 # meters (e.g. 2.4 km)
            fill_opacity = 0.01
            stroke_val = False
            border_color = "transparent"
            border_opacity = 0.0
            weight_val = 0
            
        # Styled HUD Inspector overlay popup (exact fields in order: PIN, Revenue, Gold Weight, Diamond Carats, Unique Customers, Invoices, Location Name)
        tooltip_content = html.Div(
            style={'fontFamily': "'Outfit', sans-serif", 'minWidth': '220px'},
            children=[
                html.Div([
                    html.Span("Area Detail: ", style={'color': '#a0a0a0', 'fontSize': '9px'}),
                    html.Span(f"PIN Code {pin}", className="fw-bold text-info", style={'fontSize': '11px'})
                ], className="mb-2", style={'borderBottom': '1px solid rgba(255,255,255,0.15)', 'paddingBottom': '4px'}),
                
                # Location Name (Associated Branch)
                html.Div([
                    html.Div("Location Name", style={'color': '#a0a0a0', 'fontSize': '9px', 'textTransform': 'uppercase'}),
                    html.Div(branch, className="fw-bold", style={'color': '#e5c158', 'fontSize': '12px'})
                ], className="mb-2"),
                
                # Metrics grid
                html.Div([
                    html.Div([
                        html.Div("Revenue", style={'color': '#a0a0a0', 'fontSize': '9px', 'textTransform': 'uppercase'}),
                        html.Div(format_inr(revenue), className="fw-bold", style={'color': '#ffffff', 'fontSize': '12px'})
                    ], style={'flex': '1'}),
                    html.Div([
                        html.Div("Invoices", style={'color': '#a0a0a0', 'fontSize': '9px', 'textTransform': 'uppercase'}),
                        html.Div(format_number(invoices), className="fw-bold", style={'color': '#ffffff', 'fontSize': '12px'})
                    ], style={'flex': '1'})
                ], style={'display': 'flex', 'gap': '10px'}, className="mb-2"),
                
                html.Div([
                    html.Div([
                        html.Div("Unique Customers", style={'color': '#a0a0a0', 'fontSize': '9px', 'textTransform': 'uppercase'}),
                        html.Div(format_number(customers), className="fw-bold", style={'color': '#ffffff', 'fontSize': '12px'})
                    ], style={'flex': '1'}),
                    html.Div([
                        html.Div("Gold Weight", style={'color': '#a0a0a0', 'fontSize': '9px', 'textTransform': 'uppercase'}),
                        html.Div(gold_str, className="fw-bold", style={'color': '#e5c158', 'fontSize': '12px'})
                    ], style={'flex': '1'})
                ], style={'display': 'flex', 'gap': '10px'}, className="mb-2"),
                
                html.Div([
                    html.Div([
                        html.Div("Diamond Carats", style={'color': '#a0a0a0', 'fontSize': '9px', 'textTransform': 'uppercase'}),
                        html.Div(f"{diamond:.2f} cts", className="fw-bold", style={'color': '#64b5f6', 'fontSize': '12px'})
                    ], style={'flex': '1'})
                ], style={'display': 'flex', 'gap': '10px'})
            ]
        )
        
        markers.append(
            dl.Circle(
                center=[lat, lon],
                radius=marker_radius,
                stroke=stroke_val,
                color=border_color,
                opacity=border_opacity,
                weight=weight_val,
                fillColor=marker_color,
                fillOpacity=fill_opacity,
                interactive=True,
                children=[
                    dl.Tooltip(
                        tooltip_content,
                        className="hud-tooltip-card",
                        direction="top",
                        sticky=True
                    )
                ]
            )
        )
    return markers

# ---------------------------------------------------
# Layout
# ---------------------------------------------------
layout = html.Div(
    style={
        'backgroundColor': '#0b0b0b',
        'minHeight': '100vh',
        'color': '#ffffff',
        'fontFamily': "'Outfit', 'Segoe UI', sans-serif",
        'padding': '15px'
    },
    children=[
        dcc.Download(id='geo-export-download'),

        dbc.Container(
            fluid=True,
            children=[
                # Header Row
                dbc.Row(
                    className="mb-4 align-items-center",
                    children=[
                        dbc.Col(
                            xs=12, md=8,
                            children=[
                                html.A(
                                    dbc.Button(
                                        "← Sales Department",
                                        color="secondary",
                                        size="sm",
                                        className="mb-2 px-3 py-1 text-uppercase fw-bold",
                                        style={'fontSize': '10px', 'backgroundColor': '#1e1e1e', 'border': '1px solid rgba(255,255,255,0.1)'}
                                    ),
                                    href="/sales",
                                    style={'textDecoration': 'none'}
                                ),
                                html.H1(
                                    "GEO ANALYTICS PLATFORM",
                                    className="fw-bold tracking-tight mb-0",
                                    style={'fontSize': '32px', 'letterSpacing': '0.5px', 'color': '#ffffff'}
                                ),
                                html.Div(
                                    "Phase 1: Geographic Reach & Customer Concentration Mapping (GIS Leaflet)",
                                    style={'color': '#a0a0a0', 'fontSize': '13px', 'fontStyle': 'italic'}
                                )
                            ]
                        ),
                        dbc.Col(
                            xs=12, md=4,
                            className="text-md-end mt-2 mt-md-0",
                            children=[
                                html.Div(
                                    f"GIS Engine Active",
                                    className="d-inline-flex align-items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 me-3",
                                    style={
                                        'color': '#00ff66',
                                        'fontSize': '11px',
                                        'textTransform': 'uppercase',
                                        'fontWeight': 'bold',
                                        'letterSpacing': '1px',
                                        'border': '1px solid rgba(0, 255, 102, 0.2)',
                                        'padding': '4px 10px',
                                        'borderRadius': '20px',
                                        'backgroundColor': 'rgba(0, 255, 102, 0.05)'
                                    }
                                ),
                                dbc.Button(
                                    "Export Data",
                                    id="geo-export-btn",
                                    className="px-3 py-1.5 fw-bold",
                                    style={
                                        'backgroundColor': '#ffffff',
                                        'color': '#0b0b0b',
                                        'border': 'none',
                                        'fontSize': '12px',
                                        'borderRadius': '6px'
                                    }
                                )
                            ]
                        )
                    ]
                ),

                # Main Grid (Leaflet Map + Sidebar Panels)
                dbc.Row(
                    children=[
                        # Left Column: Map Window (75-80% Screen Space)
                        dbc.Col(
                            xs=12, lg=9,
                            className="mb-4 position-relative",
                            style={'height': '80vh', 'minHeight': '600px'},
                            children=[
                                # GIS Map Wrapper
                                html.Div(
                                    style={'position': 'relative', 'height': '100%', 'borderRadius': '12px', 'overflow': 'hidden', 'border': '1px solid rgba(255,255,255,0.08)'},
                                    children=[
                                        # The Leaflet map element (Fills the parent container)
                                        dl.Map(
                                            id='geo-gis-map',
                                            center=[26.3, 88.8],
                                            zoom=7.8,
                                            style={'height': '100%', 'width': '100%', 'backgroundColor': '#0b0b0b'},
                                            children=[
                                                # Base dark map tiles
                                                dl.TileLayer(
                                                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
                                                    attribution="&copy; OpenStreetMap contributors &copy; CARTO"
                                                ),
                                                
                                                # Container for dynamic ImageOverlay (bypasses Leaflet bounds immutability)
                                                dl.LayerGroup(id='geo-heatmap-container'),
                                                
                                                # GeoJSON West Bengal district boundary vectors
                                                dl.GeoJSON(
                                                    data=geojson_data,
                                                    id="geo-geojson-boundaries",
                                                    options=dict(
                                                        style=dict(
                                                            color="#ffffff",
                                                            opacity=0.3,
                                                            weight=1.5,
                                                            fillColor="transparent",
                                                            fillOpacity=0
                                                        )
                                                    )
                                                ),
                                                
                                                # Placeholders populated dynamically via callbacks using valid Leaflet LayerGroup elements
                                                dl.LayerGroup(id='geo-branch-markers'),
                                                dl.LayerGroup(id='geo-hover-markers')
                                            ]
                                        ),

                                        # Map HUD Instructions
                                        html.Div(
                                            className="glass-card",
                                            style={
                                                'position': 'absolute',
                                                'bottom': '20px',
                                                'left': '20px',
                                                'zIndex': '1000',
                                                'backgroundColor': 'rgba(11, 11, 11, 0.85)',
                                                'backdropFilter': 'blur(10px)',
                                                'border': '1px solid rgba(255,255,255,0.1)',
                                                'borderRadius': '6px',
                                                'padding': '8px 12px',
                                                'pointerEvents': 'none'
                                            },
                                            children=[
                                                html.Div(
                                                    "GIS overlay: Hover over highlights and store markers to inspect.",
                                                    style={'fontSize': '11px', 'color': '#a0a0a0', 'fontStyle': 'italic'}
                                                )
                                            ]
                                        ),
                                        
                                        # Custom Map Focus Controller Panel (Top Left, positioned below Zoom controls)
                                        html.Div(
                                            style={
                                                'position': 'absolute',
                                                'top': '95px',
                                                'left': '10px',
                                                'zIndex': '1000'
                                            },
                                            children=[
                                                dbc.Button(
                                                    "Reset View",
                                                    id="geo-map-reset-btn",
                                                    size="sm",
                                                    className="fw-bold px-2 py-1.5",
                                                    style={
                                                        'backgroundColor': 'rgba(20, 20, 20, 0.9)',
                                                        'color': '#ffffff',
                                                        'border': '1px solid rgba(255,255,255,0.15)',
                                                        'borderRadius': '4px',
                                                        'backdropFilter': 'blur(10px)',
                                                        'fontSize': '10px',
                                                        'boxShadow': '0 1px 5px rgba(0,0,0,0.65)'
                                                    }
                                                )
                                            ]
                                        )
                                    ]
                                )
                            ]
                        ),

                        # Right Column: Side Control Center & KPIs (20-25% Screen Space)
                        dbc.Col(
                            xs=12, lg=3,
                            className="mb-4",
                            style={'position': 'relative', 'zIndex': '1050'},
                            children=[
                                # 1. Category Segment Toggle (Revenue, Gold, Diamond)
                                html.Div(
                                    className="glass-card mb-3",
                                    children=[
                                        html.Label("Analysis Segment", className="kpi-title d-block mb-2"),
                                        dbc.RadioItems(
                                            id="geo-category-toggle",
                                            className="segmented-btn-group d-flex w-100",
                                            options=[
                                                {"label": "Total Revenue", "value": "Revenue"},
                                                {"label": "Gold", "value": "Gold"},
                                                {"label": "Diamond", "value": "Diamond"}
                                            ],
                                            value="Revenue",
                                            style={'gap': '2px'},
                                            inputClassName="btn-check",
                                            labelClassName="btn btn-outline-primary flex-fill mb-0 text-center"
                                        )
                                    ]
                                ),

                                # 2. Dropdown Filters
                                html.Div(
                                    className="glass-card mb-3",
                                    children=[
                                        html.Div("Filters & Map Settings", className="fw-bold mb-3 text-uppercase", style={'fontSize': '12px', 'letterSpacing': '1px', 'color': '#e5c158'}),
                                        
                                        # Date Picker Range
                                        html.Div(
                                            className="mb-3",
                                            children=[
                                                html.Label("Date Range", className="kpi-title"),
                                                dcc.DatePickerRange(
                                                    id='geo-date-picker',
                                                    min_date_allowed=filter_meta['min_date'],
                                                    max_date_allowed=filter_meta['max_date'],
                                                    start_date=default_start_date,
                                                    end_date=default_end_date,
                                                    display_format='DD-MMM-YYYY',
                                                    style={'width': '100%'}
                                                )
                                            ]
                                        ),
                                        
                                        # Location Dropdown
                                        html.Div(
                                            className="mb-3",
                                            children=[
                                                html.Label("Branch / Location", className="kpi-title"),
                                                dcc.Dropdown(
                                                    id='geo-location-dropdown',
                                                    options=[{'label': loc, 'value': loc} for loc in filter_meta['locations']],
                                                    multi=True,
                                                    placeholder="All Branches"
                                                )
                                            ]
                                        ),
                                        
                                        # RM Dropdown
                                        html.Div(
                                            className="mb-3",
                                            children=[
                                                html.Label("Regional Manager (RM)", className="kpi-title"),
                                                dcc.Dropdown(
                                                    id='geo-rm-dropdown',
                                                    options=[{'label': rm, 'value': rm} for rm in filter_meta['rms']],
                                                    multi=True,
                                                    placeholder="All RMs"
                                                )
                                            ]
                                        ),
                                        
                                        # ZM Dropdown
                                        html.Div(
                                            className="mb-3",
                                            children=[
                                                html.Label("Zone Manager (ZM)", className="kpi-title"),
                                                dcc.Dropdown(
                                                    id='geo-zm-dropdown',
                                                    options=[{'label': zm, 'value': zm} for zm in filter_meta['zms']],
                                                    multi=True,
                                                    placeholder="All ZMs"
                                                )
                                            ]
                                        ),

                                        # Heat Radius Selector
                                        html.Div(
                                            className="mb-3",
                                            children=[
                                                html.Label("Heat Blur Radius", className="kpi-title"),
                                                dcc.Dropdown(
                                                    id='geo-radius-dropdown',
                                                    options=[
                                                        {'label': 'Localized Hotspots (Small)', 'value': 'small'},
                                                        {'label': 'Standard Influence (Medium)', 'value': 'medium'},
                                                        {'label': 'Regional Overlay (Large)', 'value': 'large'}
                                                    ],
                                                    value='medium',
                                                    clearable=False
                                                )
                                            ]
                                        ),
                                        
                                        # Enter Apply Filters Button
                                        dbc.Button(
                                            "Apply Filters (Enter)",
                                            id="geo-enter-btn",
                                            className="w-100 gis-btn-gold py-2 fw-bold text-uppercase",
                                            style={'letterSpacing': '1px'}
                                        )
                                    ]
                                ),

                                # 3. Dynamic KPIs Panel (Glow cards)
                                html.Div(
                                    className="glass-card",
                                    style={'maxHeight': '320px', 'overflowY': 'auto'},
                                    children=[
                                        html.Div("Operational Snapshot", className="fw-bold mb-3 text-uppercase", style={'fontSize': '12px', 'letterSpacing': '1px', 'color': '#e5c158'}),
                                        
                                        # KPI Row 1
                                        dbc.Row(
                                            className="g-2 mb-2",
                                            children=[
                                                dbc.Col(
                                                    xs=6,
                                                    children=html.Div(
                                                        style={'border': '1px solid rgba(255,255,255,0.05)', 'borderRadius': '6px', 'padding': '8px', 'backgroundColor': 'rgba(255,255,255,0.02)'},
                                                        children=[
                                                            html.Div("Total Revenue", className="kpi-title"),
                                                            html.Div(id="kpi-revenue", className="kpi-value kpi-value-gold", style={'fontSize': '15px'})
                                                        ]
                                                    )
                                                ),
                                                dbc.Col(
                                                    xs=6,
                                                    children=html.Div(
                                                        style={'border': '1px solid rgba(255,255,255,0.05)', 'borderRadius': '6px', 'padding': '8px', 'backgroundColor': 'rgba(255,255,255,0.02)'},
                                                        children=[
                                                            html.Div("Customers", className="kpi-title"),
                                                            html.Div(id="kpi-customers", className="kpi-value", style={'fontSize': '15px'})
                                                        ]
                                                    )
                                                )
                                            ]
                                        ),

                                        # KPI Row 2
                                        dbc.Row(
                                            className="g-2 mb-2",
                                            children=[
                                                dbc.Col(
                                                    xs=6,
                                                    children=html.Div(
                                                        style={'border': '1px solid rgba(255,255,255,0.05)', 'borderRadius': '6px', 'padding': '8px', 'backgroundColor': 'rgba(255,255,255,0.02)'},
                                                        children=[
                                                            html.Div("Invoices Issued", className="kpi-title"),
                                                            html.Div(id="kpi-invoices", className="kpi-value", style={'fontSize': '15px'})
                                                        ]
                                                    )
                                                ),
                                                dbc.Col(
                                                    xs=6,
                                                    children=html.Div(
                                                        style={'border': '1px solid rgba(255,255,255,0.05)', 'borderRadius': '6px', 'padding': '8px', 'backgroundColor': 'rgba(255,255,255,0.02)'},
                                                        children=[
                                                            html.Div("Pincodes Covered", className="kpi-title"),
                                                            html.Div(id="kpi-pincodes", className="kpi-value", style={'fontSize': '15px'})
                                                        ]
                                                    )
                                                )
                                            ]
                                        ),

                                        # KPI Row 3
                                        dbc.Row(
                                            className="g-2",
                                            children=[
                                                dbc.Col(
                                                    xs=6,
                                                    children=html.Div(
                                                        style={'border': '1px solid rgba(255,255,255,0.05)', 'borderRadius': '6px', 'padding': '8px', 'backgroundColor': 'rgba(255,255,255,0.02)'},
                                                        children=[
                                                            html.Div("Gold Weight", className="kpi-title"),
                                                            html.Div(id="kpi-gold", className="kpi-value kpi-value-gold", style={'fontSize': '15px'})
                                                        ]
                                                    )
                                                ),
                                                dbc.Col(
                                                    xs=6,
                                                    children=html.Div(
                                                        style={'border': '1px solid rgba(255,255,255,0.05)', 'borderRadius': '6px', 'padding': '8px', 'backgroundColor': 'rgba(255,255,255,0.02)'},
                                                        children=[
                                                            html.Div("Diamond Carats", className="kpi-title"),
                                                            html.Div(id="kpi-diamond", className="kpi-value kpi-value-diamond", style={'fontSize': '15px'})
                                                        ]
                                                    )
                                                )
                                            ]
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    ]
)

# ---------------------------------------------------
# Callbacks
# ---------------------------------------------------

@callback(
    [
        Output('geo-heatmap-container', 'children'),
        Output('geo-branch-markers', 'children'),
        Output('geo-hover-markers', 'children'),
        Output('geo-gis-map', 'viewport'),
        Output('kpi-revenue', 'children'),
        Output('kpi-customers', 'children'),
        Output('kpi-invoices', 'children'),
        Output('kpi-pincodes', 'children'),
        Output('kpi-gold', 'children'),
        Output('kpi-diamond', 'children')
    ],
    [
        Input('geo-enter-btn', 'n_clicks'),
        Input('geo-map-reset-btn', 'n_clicks'),
        Input('geo-category-toggle', 'value'),
        Input('geo-radius-dropdown', 'value')
    ],
    [
        State('geo-date-picker', 'start_date'),
        State('geo-date-picker', 'end_date'),
        State('geo-location-dropdown', 'value'),
        State('geo-rm-dropdown', 'value'),
        State('geo-zm-dropdown', 'value')
    ]
)
def update_gis_dashboard(
    enter_clicks,
    reset_clicks,
    category,
    radius_selection,
    start_date,
    end_date,
    locations,
    rms,
    zms
):
    # Determine the trigger source
    from dash import callback_context
    ctx = callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else ""
    
    # Check if a branch filter is selected for drill-down mode
    is_drilldown = locations is not None and len(locations) > 0
    
    # Fetch data
    data_pack = get_filtered_dashboard_data(
        start_date=start_date,
        end_date=end_date,
        locations=locations,
        rms=rms,
        zms=zms,
        category=category,
        radius_selection=radius_selection
    )
    
    kpis = data_pack['kpis']
    heatmap_url = data_pack['heatmap_url']
    heatmap_bounds = data_pack['heatmap_bounds']
    heatmap_points = data_pack['heatmap_points']
    
    # Camera Center & Zoom viewport setup
    if triggered_id == 'geo-map-reset-btn':
        viewport = dict(center=[26.3, 88.8], zoom=7.8, transition="flyTo")
    else:
        viewport = dict(center=data_pack['center'], zoom=data_pack['zoom'], transition="flyTo")
        
    # Render customized Golden glowing branch markers
    branches = get_branch_coords()
    if is_drilldown:
        # Hide other branch markers: only show markers for selected locations
        branches = [b for b in branches if b['Location Name'] in locations]
    branch_markers = make_branch_markers(branches)
    
    # Render visible relative colored circle markers (drill-down) or invisible hover helpers (heatmap)
    hover_markers = make_hover_markers(heatmap_points, radius_selection, is_drilldown=is_drilldown)
    
    # Build dynamic ImageOverlay for heatmap if not in drill-down mode
    if is_drilldown:
        heatmap_element = None
    else:
        heatmap_element = dl.ImageOverlay(
            url=heatmap_url,
            bounds=heatmap_bounds,
            opacity=0.75
        )
        
    # Format KPIs for display
    revenue_formatted = format_inr(kpis['total_revenue'])
    customers_formatted = format_number(kpis['unique_customers'])
    invoices_formatted = format_number(kpis['invoices'])
    pincodes_formatted = format_number(kpis['unique_pincodes'])
    
    # Format weights
    if kpis['gold_weight'] >= 1000:
        gold_formatted = f"{format_number(kpis['gold_weight'] / 1000.0, 2)} kg"
    else:
        gold_formatted = f"{format_number(kpis['gold_weight'], 1)} g"
        
    diamond_formatted = f"{format_number(kpis['diamond_carats'], 2)} cts"
    
    return (
        heatmap_element,
        branch_markers,
        hover_markers,
        viewport,
        revenue_formatted,
        customers_formatted,
        invoices_formatted,
        pincodes_formatted,
        gold_formatted,
        diamond_formatted
    )

# ---------------------------------------------------
# Export Callback (Downloads Filtered Dataset)
# ---------------------------------------------------
@callback(
    Output('geo-export-download', 'data'),
    [Input('geo-export-btn', 'n_clicks')],
    [
        State('geo-date-picker', 'start_date'),
        State('geo-date-picker', 'end_date'),
        State('geo-location-dropdown', 'value'),
        State('geo-rm-dropdown', 'value'),
        State('geo-zm-dropdown', 'value'),
        State('geo-category-toggle', 'value')
    ],
    prevent_initial_call=True
)
def export_filtered_data(
    n_clicks,
    start_date,
    end_date,
    locations,
    rms,
    zms,
    category
):
    if not n_clicks:
        return no_update
        
    data_pack = get_filtered_dashboard_data(
        start_date=start_date,
        end_date=end_date,
        locations=locations,
        rms=rms,
        zms=zms,
        category=category
    )
    
    points = data_pack['heatmap_points']
    if not points:
        return no_update
        
    df_export = pd.DataFrame(points)
    
    columns_rename = {
        'Pincode': 'PIN Code',
        'Latitude': 'Latitude',
        'Longitude': 'Longitude',
        'Revenue': 'Total Revenue (INR)',
        'Customers': 'Unique Customers',
        'Invoices': 'Total Invoices',
        'Gold_w': 'Gold Weight (g)',
        'Diamond_cts': 'Diamond Carats (cts)',
        'Primary Branch': 'Associated Primary Store'
    }
    
    df_export = df_export[list(columns_rename.keys())].rename(columns=columns_rename)
    
    return dcc.send_data_frame(df_export.to_csv, "geo_analytics_filtered_export.csv", index=False)
