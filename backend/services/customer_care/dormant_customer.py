from backend.cache.data_cache import (
    merged_sales_df,
    customer_list_df,
    rm_zm_df,
    global_dormant_customer_df
)
import pandas as pd
import numpy as np
from backend.services.rls import get_allowed_locations

def get_dormant_customer_data(
    evaluation_date=None,
    days_filter=365,
    locations=None,
    rms=None,
    zms=None,
    search_query=None,
    nsv_more=None,
    p_count=None
):
    try:
        allowed_locations = get_allowed_locations()
    except Exception:
        allowed_locations = ['ALL']

    latest_invoice_dt = pd.to_datetime(merged_sales_df['Invoice Date'].max())
    if not evaluation_date:
        evaluation_date = latest_invoice_dt
    evaluation_date_dt = pd.to_datetime(evaluation_date)

    is_search_active = search_query and str(search_query).strip() != ""
    is_default_date = evaluation_date_dt == latest_invoice_dt

    # ---------------------------------------------------
    # FAST PATH: Pre-calculated global aggregates
    # ---------------------------------------------------
    if (is_search_active or is_default_date) and not global_dormant_customer_df.empty:
        merged = global_dormant_customer_df.copy()
        
        # Apply RLS
        if 'ALL' not in allowed_locations:
            merged = merged[merged['Location Name'].isin(allowed_locations)]
            
        if is_search_active:
            q = str(search_query).strip().upper()
            merged = merged[
                merged['Customer Code'].astype(str).str.upper().str.contains(q, na=False) |
                merged['Customer Phone'].astype(str).str.upper().str.contains(q, na=False)
            ]
            merged['days_inactive'] = (latest_invoice_dt - pd.to_datetime(merged['Last Purchase Date'])).dt.days
        else:
            # Filter by Location, RM, ZM
            rm_zm = rm_zm_df.copy()
            if 'ALL' not in allowed_locations:
                rm_zm = rm_zm[rm_zm['location'].isin(allowed_locations)]
                
            if rms:
                rm_locs = rm_zm[rm_zm['rm'].isin(rms)]['location'].unique()
                merged = merged[merged['Location Name'].isin(rm_locs)]
                
            if zms:
                zm_locs = rm_zm[rm_zm['zm'].isin(zms)]['location'].unique()
                merged = merged[merged['Location Name'].isin(zm_locs)]
                
            if locations:
                merged = merged[merged['Location Name'].isin(locations)]
                
            # Filter by Inactivity Days
            merged['days_inactive'] = (evaluation_date_dt - pd.to_datetime(merged['Last Purchase Date'])).dt.days
            if days_filter is not None and str(days_filter).strip() != "":
                merged = merged[merged['days_inactive'] >= int(days_filter)]
                
            # Filter by NSV generated minimum
            if nsv_more is not None and str(nsv_more).strip() != "":
                merged = merged[merged['nsv_generated'] >= float(nsv_more)]
                
            # Filter by Purchase count minimum
            if p_count is not None and str(p_count).strip() != "":
                merged = merged[merged['times_purchased'] >= int(p_count)]

        # Cleanup final formatting
        merged['Customer Code'] = merged['Customer Code'].fillna("").astype(str).replace(['nan', 'None'], '')
        merged['Customer Phone'] = merged['Customer Phone'].fillna("").astype(str).replace(['nan', 'None'], '')
        merged['Customer Name'] = merged['Customer Name'].fillna("").astype(str).replace(['nan', 'None'], '')
        merged['Sales Person Name'] = merged['Sales Person Name'].fillna("").astype(str).replace(['nan', 'None'], '')
        merged['Last Purchased Item'] = merged['Last Purchased Item'].fillna("").astype(str).replace(['nan', 'None'], '')
        merged['last_purchase_value'] = pd.to_numeric(merged['last_purchase_value'], errors='coerce').fillna(0.0).round(2)
        merged['nsv_generated'] = pd.to_numeric(merged['nsv_generated'], errors='coerce').fillna(0.0).round(2)
        
        # Sort by NSV generated largest to lowest by default
        merged = merged.sort_values(by='nsv_generated', ascending=False)
        
        final_cols = [
            'Location Code', 'Location Name', 'Customer Code', 'Customer Name', 'Customer Phone',
            'nsv_generated', 'times_purchased', 'Last Purchase Date', 'last_purchase_value',
            'Last Purchased Item', 'Sales Person Name', 'days_inactive'
        ]
        return merged[final_cols].copy()

    # ---------------------------------------------------
    # DYNAMIC FALLBACK PATH: (e.g. historical evaluation_date)
    # ---------------------------------------------------
    df = merged_sales_df.copy()
    if 'ALL' not in allowed_locations:
        df = df[df['Location Name'].isin(allowed_locations)]

    # Standard filter path
    # Filter transactions by Evaluation Date (Invoice Date <= evaluation_date)
    df = df[df['Invoice Date'] <= evaluation_date_dt]
    
    # Location, RM, ZM Filters
    rm_zm = rm_zm_df.copy()
    if 'ALL' not in allowed_locations:
        rm_zm = rm_zm[rm_zm['location'].isin(allowed_locations)]
        
    if rms:
        rm_locs = rm_zm[rm_zm['rm'].isin(rms)]['location'].unique()
        df = df[df['Location Name'].isin(rm_locs)]
        
    if zms:
        zm_locs = rm_zm[rm_zm['zm'].isin(zms)]['location'].unique()
        df = df[df['Location Name'].isin(zm_locs)]
        
    if locations:
        df = df[df['Location Name'].isin(locations)]

    # Clean Transaction Fields
    df['Bom Line Amount'] = pd.to_numeric(df['Bom Line Amount'], errors='coerce').fillna(0.0)
    df['Invoice Date'] = pd.to_datetime(df['Invoice Date'])
    df['Customer Code'] = df['Customer Code'].fillna("").astype(str).str.strip().str.upper()
    df = df[df['Customer Code'] != ""]

    if df.empty:
        return pd.DataFrame(columns=[
            'Location Code', 'Location Name', 'Customer Code', 'Customer Name', 'Customer Phone',
            'nsv_generated', 'times_purchased', 'Last Purchase Date', 'last_purchase_value',
            'Last Purchased Item', 'Sales Person Name', 'days_inactive'
        ])

    df = df.sort_values(by=['Invoice Date', 'Document No.'])
    
    latest_tx = df.groupby('Customer Code').last().reset_index()
    sums = df.groupby('Customer Code', as_index=False)['Bom Line Amount'].sum().rename(
        columns={'Bom Line Amount': 'nsv_generated'}
    )
    dates = df[['Customer Code', 'Invoice Date']].copy()
    dates['Invoice Date Only'] = dates['Invoice Date'].dt.date
    dates_unique = dates.groupby('Customer Code')['Invoice Date Only'].nunique().reset_index().rename(
        columns={'Invoice Date Only': 'times_purchased'}
    )
    
    merged = latest_tx.merge(sums, on='Customer Code').merge(dates_unique, on='Customer Code')

    # Map phone number from Quick Customer List
    cust_list = customer_list_df.copy()
    cust_list['customer_no.'] = cust_list['customer_no.'].astype(str).str.strip().str.upper()
    cust_list['phone_no.'] = cust_list['phone_no.'].astype(str).str.strip().str.replace('.0', '', regex=False)
    code_to_phone = cust_list[['customer_no.', 'phone_no.']].drop_duplicates(subset=['customer_no.'])
    
    merged = merged.merge(code_to_phone, left_on='Customer Code', right_on='customer_no.', how='left')
    merged['Customer Phone'] = merged['phone_no.'].fillna("").astype(str).str.strip().replace(['nan', 'None'], '')
    merged.drop(columns=['customer_no.', 'phone_no.'], inplace=True, errors='ignore')

    merged['Last Purchase Date'] = pd.to_datetime(merged['Invoice Date'])
    merged['last_purchase_value'] = pd.to_numeric(merged['Bom Line Amount'], errors='coerce').fillna(0.0).round(2)
    merged['nsv_generated'] = pd.to_numeric(merged['nsv_generated'], errors='coerce').fillna(0.0).round(2)
    
    # Inactivity Filter
    merged['days_inactive'] = (evaluation_date_dt - merged['Last Purchase Date']).dt.days
    if days_filter is not None and str(days_filter).strip() != "":
        merged = merged[merged['days_inactive'] >= int(days_filter)]

    # Filter by NSV generated minimum
    if nsv_more is not None and str(nsv_more).strip() != "":
        merged = merged[merged['nsv_generated'] >= float(nsv_more)]
        
    # Filter by Purchase count minimum
    if p_count is not None and str(p_count).strip() != "":
        merged = merged[merged['times_purchased'] >= int(p_count)]

    # Formatting
    merged['Customer Code'] = merged['Customer Code'].fillna("").astype(str).replace(['nan', 'None'], '')
    merged['Customer Phone'] = merged['Customer Phone'].fillna("").astype(str).replace(['nan', 'None'], '')
    merged['Customer Name'] = merged['Customer Name'].fillna("").astype(str).replace(['nan', 'None'], '')
    merged['Sales Person Name'] = merged['Sales Person Name'].fillna("").astype(str).replace(['nan', 'None'], '')
    merged['Item Name'] = merged['Item Name'].fillna("").astype(str).replace(['nan', 'None'], '')
    
    final_cols = [
        'Location Code', 'Location Name', 'Customer Code', 'Customer Name', 'Customer Phone',
        'nsv_generated', 'times_purchased', 'Last Purchase Date', 'last_purchase_value',
        'Item Name', 'Sales Person Name', 'days_inactive'
    ]
    
    for col in final_cols:
        if col not in merged.columns:
            merged[col] = ""
            
    res = merged[final_cols].rename(columns={'Item Name': 'Last Purchased Item'}).copy()
    res = res.sort_values(by='nsv_generated', ascending=False)
    return res
