# backend/services/sales/geo_analytics_service.py

import os
import base64
import pandas as pd
import numpy as np
from io import BytesIO
from scipy.ndimage import gaussian_filter

# ---------------------------------------------------
# Module Level Caching of Data
# ---------------------------------------------------

# Paths
HEATMAP_PARQUET_PATH = "snapshot/heatmap.parquet"
RM_ZM_PARQUET_PATH = "snapshot/rm_zm.parquet"

# Global dataframes
_raw_heatmap_df = None
_branch_coords_df = None
_primary_branch_dict = None

def init_service():
    """Initializes and caches the geospatial data, generating required assets."""
    global _raw_heatmap_df, _branch_coords_df, _primary_branch_dict
    
    if _raw_heatmap_df is not None:
        return
        
    print("Initializing Geo Analytics Service and loading Parquet data...")
    
    # 1. Auto-generate glowing gold-white branch beacon image asset if it doesn't exist
    beacon_path = "app/assets/branch_beacon.png"
    if not os.path.exists(beacon_path):
        try:
            os.makedirs(os.path.dirname(beacon_path), exist_ok=True)
            from PIL import Image, ImageDraw
            # Create a 32x32 transparent image
            img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Gold color with transparency: RGBA(229, 193, 88, alpha)
            # Outer ring: bounding box (2, 2, 29, 29)
            draw.ellipse([2, 2, 29, 29], outline=(229, 193, 88, 100), width=3)
            # Inner circle
            draw.ellipse([8, 8, 23, 23], fill=(229, 193, 88, 255))
            # Core white circle
            draw.ellipse([11, 11, 20, 20], fill=(255, 255, 255, 255))
            img.save(beacon_path, "PNG")
            print("Successfully generated custom store marker at:", beacon_path)
        except Exception as e:
            print("Warning: Failed to generate branch beacon marker image:", e)
    
    # 2. Load primary heatmap data
    if not os.path.exists(HEATMAP_PARQUET_PATH):
        raise FileNotFoundError(f"Could not find primary data source: {HEATMAP_PARQUET_PATH}")
    
    df = pd.read_parquet(HEATMAP_PARQUET_PATH)
    
    # Standardize columns
    df['Location Name'] = df['Location Name'].astype(str).str.strip().str.upper()
    df['Location Code'] = df['Location Code'].astype(str).str.strip().str.upper()
    df['Date'] = pd.to_datetime(df['Date'])
    
    # 3. Join with RM-ZM mapping
    if os.path.exists(RM_ZM_PARQUET_PATH):
        rm_zm_df = pd.read_parquet(RM_ZM_PARQUET_PATH)
        rm_zm_df['location'] = rm_zm_df['location'].astype(str).str.strip().str.upper()
        rm_zm_df['rm'] = rm_zm_df['rm'].astype(str).str.strip().str.upper()
        rm_zm_df['zm'] = rm_zm_df['zm'].astype(str).str.strip().str.upper()
        
        # Merge to attach RM and ZM to each record
        df = df.merge(
            rm_zm_df[['location', 'rm', 'zm']],
            left_on='Location Name',
            right_on='location',
            how='left'
        )
        # Drop redundant column
        if 'location' in df.columns:
            df.drop(columns=['location'], inplace=True)
    else:
        df['rm'] = "UNKNOWN"
        df['zm'] = "UNKNOWN"
        
    df['rm'] = df['rm'].fillna("UNKNOWN")
    df['zm'] = df['zm'].fillna("UNKNOWN")
    
    # 4. Pre-calculate Primary Branch for each Pincode
    pincode_branch = df.groupby(['Pincode', 'Location Name'])['Revenue'].sum().reset_index()
    pincode_branch = pincode_branch.sort_values('Revenue', ascending=False).drop_duplicates('Pincode')
    _primary_branch_dict = dict(zip(pincode_branch['Pincode'], pincode_branch['Location Name']))
    
    # 5. Extract store coordinates dynamically based on the mode of coordinates per branch
    branch_coords = []
    for name, group in df.groupby('Location Name'):
        code = group['Location Code'].iloc[0]
        try:
            most_common = group.groupby(['Store Pincode', 'Store Lat', 'Store Long']).size().idxmax()
            store_pin = most_common[0]
            store_lat = most_common[1]
            store_long = most_common[2]
        except Exception:
            store_pin = group['Store Pincode'].iloc[0] if 'Store Pincode' in group.columns else 0
            store_lat = group['Store Lat'].mean() if 'Store Lat' in group.columns else 26.5
            store_long = group['Store Long'].mean() if 'Store Long' in group.columns else 88.5
            
        branch_coords.append({
            'Location Name': name,
            'Location Code': code,
            'Store Pincode': int(store_pin),
            'Store Lat': float(store_lat),
            'Store Long': float(store_long)
        })
    
    _branch_coords_df = pd.DataFrame(branch_coords)
    _raw_heatmap_df = df
    print("Geo Analytics Service loaded successfully!")

# Auto-initialize on import
init_service()

# ---------------------------------------------------
# Core Queries & Aggregations
# ---------------------------------------------------

def get_branch_coords():
    """Returns a list of dictionaries with branch markers."""
    global _branch_coords_df
    return _branch_coords_df.to_dict(orient='records')

def get_filter_options():
    """Returns list of unique values for dropdown filters."""
    global _raw_heatmap_df
    return {
        'locations': sorted(_raw_heatmap_df['Location Name'].unique().tolist()),
        'rms': sorted(_raw_heatmap_df['rm'].unique().tolist()),
        'zms': sorted(_raw_heatmap_df['zm'].unique().tolist()),
        'min_date': _raw_heatmap_df['Date'].min(),
        'max_date': _raw_heatmap_df['Date'].max()
    }

def generate_heatmap_image_url(points, lat_min, lat_max, lon_min, lon_max, radius_selection):
    """
    Generates a base64 encoded transparent PNG overlay of the continuous Gaussian heatmap.
    """
    # Padding to ensure heatmap is not cut off at the edge bounds
    padding = 0.25
    lat_min -= padding
    lat_max += padding
    lon_min -= padding
    lon_max += padding
    
    # Leaflet bounds: [[lat_min, lon_min], [lat_max, lon_max]]
    overlay_bounds = [[float(lat_min), float(lon_min)], [float(lat_max), float(lon_max)]]
    
    from PIL import Image
    
    if not points:
        # Return empty transparent PNG
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        buf = BytesIO()
        img.save(buf, format="PNG")
        url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')
        return url, overlay_bounds

    # Grid size (400x400 balances speed and smoothness)
    grid_size = 400
    grid = np.zeros((grid_size, grid_size), dtype=np.float32)
    
    # Extract coordinates
    lats = [p['Latitude'] for p in points]
    lons = [p['Longitude'] for p in points]
    vals = [p['heat_value'] for p in points]
    
    lat_range = lat_max - lat_min
    lon_range = lon_max - lon_min
    
    # Map points to grid cells
    for lat, lon, val in zip(lats, lons, vals):
        if lat_range == 0 or lon_range == 0:
            continue
        y = int((lat - lat_min) / lat_range * (grid_size - 1))
        x = int((lon - lon_min) / lon_range * (grid_size - 1))
        if 0 <= y < grid_size and 0 <= x < grid_size:
            grid[y, x] += val
            
    # Apply Gaussian filter based on user-selected blur radius
    radius_map = {
        'small': 7.0,
        'medium': 15.0,
        'large': 28.0
    }
    sigma = radius_map.get(radius_selection, 15.0)
    blurred = gaussian_filter(grid, sigma=sigma)
    
    # Normalize to 0..1
    max_val = blurred.max()
    normalized = blurred / max_val if max_val > 0 else blurred
    
    # Create RGBA array mapping intensities to colours
    # Transparent -> Green -> Yellow -> Orange -> Red
    rgba_image = np.zeros((grid_size, grid_size, 4), dtype=np.uint8)
    
    for y in range(grid_size):
        for x in range(grid_size):
            t = normalized[y, x]
            if t < 0.04:
                rgba_image[y, x] = [0, 0, 0, 0]
            elif t < 0.3:
                # Green transition
                factor = (t - 0.04) / 0.26
                rgba_image[y, x] = [0, 220, 80, int(150 * factor)]
            elif t < 0.6:
                # Green -> Yellow transition
                factor = (t - 0.3) / 0.3
                rgba_image[y, x] = [int(255 * factor), 220 + int(15 * factor), 80 - int(21 * factor), int(150 + 50 * factor)]
            elif t < 0.85:
                # Yellow -> Orange transition
                factor = (t - 0.6) / 0.25
                rgba_image[y, x] = [255, 235 - int(83 * factor), int(59 * (1 - factor)), int(200 + 40 * factor)]
            else:
                # Orange -> Red transition
                factor = (t - 0.85) / 0.15
                rgba_image[y, x] = [255 - int(11 * factor), 152 - int(85 * factor), int(54 * factor), int(240 + 15 * factor)]
                
    # Flip array vertically (numpy origin bottom-left vs Image origin top-left)
    rgba_image = np.flipud(rgba_image)
    
    # Convert array to PNG base64 URL
    img = Image.fromarray(rgba_image, mode="RGBA")
    buf = BytesIO()
    img.save(buf, format="PNG")
    url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return url, overlay_bounds

def get_filtered_dashboard_data(
    start_date,
    end_date,
    locations=None,
    rms=None,
    zms=None,
    category=None,
    radius_selection='medium'
):
    """
    Applies filters, computes KPIs, resolves spatial bounds, and triggers
    the server-side Gaussian heatmap image generation.
    """
    global _raw_heatmap_df, _primary_branch_dict
    
    # 1. Filter dataset
    df = _raw_heatmap_df.copy()
    
    if start_date:
        df = df[df['Date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['Date'] <= pd.to_datetime(end_date)]
        
    if locations:
        df = df[df['Location Name'].isin(locations)]
    if rms:
        df = df[df['rm'].isin(rms)]
    if zms:
        df = df[df['zm'].isin(zms)]
        
    # 2. Resolve target heat metric
    if category == 'Gold':
        heat_col = 'Gold_w'
        metric_label = 'Gold Weight (g)'
    elif category == 'Diamond':
        heat_col = 'Diamond_cts'
        metric_label = 'Diamond Carats (cts)'
    else:
        heat_col = 'Revenue'
        metric_label = 'Revenue (₹)'
        
    # 3. Calculate KPIs
    if not df.empty:
        kpis = {
            'total_revenue': float(df['Revenue'].sum()),
            'unique_customers': int(df['Customers'].sum()),
            'invoices': int(df['Invoices'].sum()),
            'gold_weight': float(df['Gold_w'].sum()),
            'diamond_carats': float(df['Diamond_cts'].sum()),
            'unique_pincodes': int(df['Pincode'].nunique())
        }
    else:
        kpis = {
            'total_revenue': 0.0,
            'unique_customers': 0,
            'invoices': 0,
            'gold_weight': 0.0,
            'diamond_carats': 0.0,
            'unique_pincodes': 0
        }
        
    # 4. Aggregate customer coordinates server-side
    if not df.empty:
        # Drop rows with invalid coordinates
        df_valid = df.dropna(subset=['Latitude', 'Longitude'])
        
        # Calculate bounds using percentiles to discard outliers (only in standard heatmap mode)
        lats = df_valid['Latitude']
        lons = df_valid['Longitude']
        if not locations and len(lats) > 10:
            lat_min, lat_max = np.percentile(lats, [5, 95])
            lon_min, lon_max = np.percentile(lons, [5, 95])
            df_bounded = df_valid[
                (df_valid['Latitude'] >= lat_min) & (df_valid['Latitude'] <= lat_max) &
                (df_valid['Longitude'] >= lon_min) & (df_valid['Longitude'] <= lon_max)
            ]
        else:
            lat_min, lat_max = lats.min() if not lats.empty else 25.0, lats.max() if not lats.empty else 27.0
            lon_min, lon_max = lons.min() if not lons.empty else 87.0, lons.max() if not lons.empty else 89.0
            df_bounded = df_valid
            
        # Guarantee non-flat range
        if lat_min == lat_max:
            lat_min -= 0.15
            lat_max += 0.15
        if lon_min == lon_max:
            lon_min -= 0.15
            lon_max += 0.15
        
        agg_df = df_bounded.groupby(['Latitude', 'Longitude', 'Pincode']).agg({
            'Revenue': 'sum',
            'Customers': 'sum',
            'Invoices': 'sum',
            'Gold_w': 'sum',
            'Diamond_cts': 'sum'
        }).reset_index()
        
        agg_df['Primary Branch'] = agg_df['Pincode'].map(_primary_branch_dict).fillna("Unknown")
        agg_df['heat_value'] = agg_df[heat_col]
        agg_df = agg_df[agg_df['heat_value'] > 0]
        
        heatmap_points = agg_df.to_dict(orient='records')
    else:
        heatmap_points = []
        lat_min, lat_max = 25.0, 27.0
        lon_min, lon_max = 87.0, 89.0
        
    # 5. Generate server-side heatmap PNG url and boundaries
    heatmap_url, heatmap_bounds = generate_heatmap_image_url(
        heatmap_points, lat_min, lat_max, lon_min, lon_max, radius_selection
    )
    
    # 6. Calculate center and zoom
    center, zoom = calculate_camera_view(df, locations)
    
    # Format Leaflet center coordinates list [lat, lon]
    leaflet_center = [center['lat'], center['lon']]
    
    return {
        'heatmap_url': heatmap_url,
        'heatmap_bounds': heatmap_bounds,
        'heatmap_points': heatmap_points,
        'kpis': kpis,
        'center': leaflet_center,
        'zoom': zoom,
        'metric_label': metric_label,
        'filtered_row_count': len(df)
    }

def calculate_camera_view(df, selected_locations=None):
    """Calculates map focus center and zoom, filtering coordinates percentiles to ignore outliers."""
    default_center = {'lat': 26.3, 'lon': 88.8}
    default_zoom = 7.8
    
    if df.empty:
        return default_center, default_zoom
        
    lats = df['Latitude'].dropna()
    lons = df['Longitude'].dropna()
    
    if len(lats) == 0:
        return default_center, default_zoom
        
    if len(lats) > 10:
        lat_min, lat_max = np.percentile(lats, [10, 90])
        lon_min, lon_max = np.percentile(lons, [10, 90])
    else:
        lat_min, lat_max = lats.min(), lats.max()
        lon_min, lon_max = lons.min(), lons.max()
        
    lat_span = lat_max - lat_min
    lon_span = lon_max - lon_min
    max_span = max(lat_span, lon_span)
    
    center_lat = (lat_min + lat_max) / 2.0
    center_lon = (lon_min + lon_max) / 2.0
    
    # Zoom level mapping
    if max_span < 0.02:
        zoom = 12.0
    elif max_span < 0.1:
        zoom = 10.5
    elif max_span < 0.3:
        zoom = 9.5
    elif max_span < 0.8:
        zoom = 8.5
    elif max_span < 1.5:
        zoom = 7.8
    elif max_span < 3.0:
        zoom = 7.0
    else:
        zoom = 6.0
        
    # Override: Zoom into specific store if only one branch filtered
    if selected_locations and len(selected_locations) == 1:
        global _branch_coords_df
        store_match = _branch_coords_df[_branch_coords_df['Location Name'] == selected_locations[0]]
        if not store_match.empty:
            center_lat = float(store_match['Store Lat'].iloc[0])
            center_lon = float(store_match['Store Long'].iloc[0])
            if max_span < 0.4:
                zoom = 9.5
            else:
                zoom = 8.2
                
    return {'lat': float(center_lat), 'lon': float(center_lon)}, float(zoom)
