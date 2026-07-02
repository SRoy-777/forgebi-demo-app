import pandas as pd
import numpy as np

# Counter order definition
COUNTER_ORDER = [
    'G-BANGLE',
    'G-NECKLACE',
    'G-CHAIN',
    'G-PR',
    'G-MISC',
    'G-COIN'
]

def prepare_inventory_data(
    opt_gold_df,
    sold_df,
    received_df,
    tag_list_df,
    start_date,
    end_date,
    locations=None,
    categories=None,
    sub_categories=None
):
    # Standardize date inputs
    sold_df = sold_df.copy()
    sold_df['invoice_date'] = pd.to_datetime(sold_df['invoice_date'], errors='coerce')
    
    received_df = received_df.copy()
    received_df['tag_received_date'] = pd.to_datetime(received_df['tag_received_date'], errors='coerce')
    
    # Filter datasets by Date
    filtered_sold_df = sold_df[
        (sold_df['invoice_date'] >= pd.to_datetime(start_date)) &
        (sold_df['invoice_date'] <= pd.to_datetime(end_date))
    ].copy()
    
    filtered_received_df = received_df[
        (received_df['tag_received_date'] >= pd.to_datetime(start_date)) &
        (received_df['tag_received_date'] <= pd.to_datetime(end_date))
    ].copy()
    
    existing_received_df = tag_list_df.copy() # Current inventory has no date filter

    # Apply Row-Level Security (RLS)
    from backend.services.rls import get_allowed_locations
    allowed_locations = get_allowed_locations()

    if 'ALL' not in allowed_locations:
        allowed_locs_upper = [loc.strip().upper() for loc in allowed_locations]
        
        opt_gold_df = opt_gold_df[opt_gold_df['location_name'].astype(str).str.strip().str.upper().isin(allowed_locs_upper)]
        filtered_sold_df = filtered_sold_df[filtered_sold_df['location_name'].astype(str).str.strip().str.upper().isin(allowed_locs_upper)]
        filtered_received_df = filtered_received_df[filtered_received_df['location_name'].astype(str).str.strip().str.upper().isin(allowed_locs_upper)]
        existing_received_df = existing_received_df[existing_received_df['location_name'].astype(str).str.strip().str.upper().isin(allowed_locs_upper)]

    # Apply Common Dropdown Filters
    def apply_dropdown_filters(df, is_opt=False):
        loc_col = 'location_name'
        cat_col = 'ornament_category' if is_opt else 'ornament_category_code'
        sub_col = 'ornament_sub_category' if is_opt else 'ornament_sub_category_code'
        
        # Clean text columns to make comparison robust
        df[loc_col] = df[loc_col].astype(str).str.strip().str.upper()
        df[cat_col] = df[cat_col].astype(str).str.strip().str.upper()
        df[sub_col] = df[sub_col].astype(str).str.strip().str.upper()
        
        if locations:
            upper_locs = [l.strip().upper() for l in locations]
            df = df[df[loc_col].isin(upper_locs)]
        if categories:
            upper_cats = [c.strip().upper() for c in categories]
            df = df[df[cat_col].isin(upper_cats)]
        if sub_categories:
            upper_subs = [s.strip().upper() for s in sub_categories]
            df = df[df[sub_col].isin(upper_subs)]
            
        return df

    opt_gold_df = apply_dropdown_filters(opt_gold_df, is_opt=True)
    filtered_sold_df = apply_dropdown_filters(filtered_sold_df)
    filtered_received_df = apply_dropdown_filters(filtered_received_df)
    existing_received_df = apply_dropdown_filters(existing_received_df)
    
    return opt_gold_df, filtered_sold_df, filtered_received_df, existing_received_df


def map_tags_to_weight_ranges(tag_df, opt_df, weight_col):
    """
    Maps tags to their correct weight ranges in opt_gold.
    If weight_range_code is already present, we use it directly for instant performance.
    Otherwise, we fall back to dynamic boundary matching.
    """
    if tag_df.empty or opt_df.empty:
        res_cols = [c for c in tag_df.columns.tolist() if c not in ['weight_range_code', 'weight_range']] + ['weight_range_code', 'weight_range']
        return pd.DataFrame(columns=res_cols)

    # Standardize column casing
    tag_df_clean = tag_df.copy()
    
    # Check if weight_range_code already exists (case-insensitive)
    has_range_code = False
    existing_code_col = None
    existing_desc_col = None
    for c in tag_df_clean.columns:
        c_clean = str(c).lower().strip().replace('_', '').replace('.', '')
        if c_clean == 'weightrangecode':
            existing_code_col = c
            has_range_code = True
        elif c_clean == 'weightrange':
            existing_desc_col = c

    if has_range_code:
        # Standardize names to 'weight_range_code' and 'weight_range'
        tag_df_clean.rename(columns={existing_code_col: 'weight_range_code'}, inplace=True)
        if existing_desc_col:
            tag_df_clean.rename(columns={existing_desc_col: 'weight_range'}, inplace=True)
            
        # Ensure weight_range is present (if only code is there, join from opt_df to fetch weight_range name)
        if 'weight_range' not in tag_df_clean.columns:
            opt_subset = opt_df[['weight_range_code', 'weight_range']].drop_duplicates(subset=['weight_range_code'])
            tag_df_clean = pd.merge(tag_df_clean, opt_subset, on='weight_range_code', how='left')
            
        return tag_df_clean

    # Clean input tag_df of existing weight range columns to avoid name collisions in inner join
    for col in ['weight_range_code', 'weight_range']:
        if col in tag_df_clean.columns:
            tag_df_clean.drop(columns=[col], inplace=True)

    # Join tag_df_clean and opt_df on category, subcategory and location
    merged = pd.merge(
        tag_df_clean,
        opt_df[['location_name', 'ornament_category', 'ornament_sub_category', 'weight_range_code', 'weight_range', 'from_weight', 'to_weight']],
        left_on=['location_name', 'ornament_category_code', 'ornament_sub_category_code'],
        right_on=['location_name', 'ornament_category', 'ornament_sub_category'],
        how='inner'
    )
    
    # Ensure numerical types for comparison
    merged[weight_col] = pd.to_numeric(merged[weight_col], errors='coerce').fillna(0.0)
    merged['from_weight'] = pd.to_numeric(merged['from_weight'], errors='coerce').fillna(0.0)
    merged['to_weight'] = pd.to_numeric(merged['to_weight'], errors='coerce').fillna(0.0)
    
    # Filter by weight range
    matched = merged[
        (merged[weight_col] >= merged['from_weight']) &
        (merged[weight_col] <= merged['to_weight'])
    ]
    
    return matched


def generate_inventory_table(
    opt_gold_df,
    sold_grouped,
    received_grouped,
    existing_grouped,
    counter_name,
    cat_to_counter
):
    # 1. Clean and merge with opt_gold_df as our master table
    opt_master = opt_gold_df.copy()
    
    # Add Counter mapping to opt_master
    opt_master['Counter'] = opt_master['ornament_category'].apply(lambda x: cat_to_counter.get(x, 'G-MISC'))
    
    # Filter opt_master by counter_name
    opt_master = opt_master[opt_master['Counter'] == counter_name]
    
    if opt_master.empty:
        return pd.DataFrame()
        
    # Left join the pre-aggregated metrics onto the filtered opt_gold master table
    merged_df = pd.merge(
        opt_master,
        sold_grouped,
        left_on=['location_name', 'ornament_category', 'ornament_sub_category', 'weight_range_code'],
        right_on=['location_name', 'ornament_category_code', 'ornament_sub_category_code', 'weight_range_code'],
        how='left'
    )
    
    merged_df = pd.merge(
        merged_df,
        received_grouped,
        left_on=['location_name', 'ornament_category', 'ornament_sub_category', 'weight_range_code'],
        right_on=['location_name', 'ornament_category_code', 'ornament_sub_category_code', 'weight_range_code'],
        how='left'
    )
    
    merged_df = pd.merge(
        merged_df,
        existing_grouped,
        left_on=['location_name', 'ornament_category', 'ornament_sub_category', 'weight_range_code'],
        right_on=['location_name', 'ornament_category_code', 'ornament_sub_category_code', 'weight_range_code'],
        how='left'
    )
    
    # 2. Format columns and clean final dataframe
    final_cols = {
        'location_name': 'Location',
        'Counter': 'Counter',
        'ornament_category': 'Category',
        'ornament_sub_category': 'Subcategory',
        'weight_range_code': 'weight_range_code',
        'weight_range': 'weight_range',
        'Pcs Rcv': 'Pcs Rcv',
        'Weight Rcv': 'Weight Rcv',
        'Pcs Sold': 'Pcs Sold',
        'Weight Sold': 'Weight Sold',
        'Existing Pcs': 'Existing Pcs',
        'Existing Weight': 'Existing Weight',
        'min_pieces': 'min_pcs',
        'min_qty': 'min_qty'
    }
    
    # Fill empty columns if missing
    for col in ['Pcs Rcv', 'Weight Rcv', 'Pcs Sold', 'Weight Sold', 'Existing Pcs', 'Existing Weight']:
        if col not in merged_df.columns:
            merged_df[col] = 0.0
            
    merged_df = merged_df[list(final_cols.keys())].rename(columns=final_cols)
    
    # Fill Nulls
    numeric_cols = ['Pcs Rcv', 'Weight Rcv', 'Pcs Sold', 'Weight Sold', 'Existing Pcs', 'Existing Weight', 'min_pcs', 'min_qty']
    for col in numeric_cols:
        merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce').fillna(0.0)
        
    # Calculate Diff columns
    merged_df['Diff_pieces'] = merged_df['Existing Pcs'] - merged_df['min_pcs']
    merged_df['Diff_weight'] = merged_df['Existing Weight'] - merged_df['min_qty']
    
    # Round decimal fields
    round_cols = ['Weight Rcv', 'Weight Sold', 'Existing Weight', 'min_qty', 'Diff_weight']
    for col in round_cols:
        merged_df[col] = merged_df[col].round(2)
        
    # Integer conversions
    int_cols = ['Pcs Rcv', 'Pcs Sold', 'Existing Pcs', 'min_pcs', 'Diff_pieces']
    for col in int_cols:
        merged_df[col] = merged_df[col].astype(int)
        
    # Sort by Weight Sold (descending) and Pcs Sold (descending) as primary keys
    merged_df.sort_values(
        by=['Weight Sold', 'Pcs Sold', 'Location', 'Category', 'Subcategory'],
        ascending=[False, False, True, True, True],
        inplace=True
    )
    
    # 3. Append Total Row
    total_row = {
        'Location': 'TOTAL',
        'Counter': '',
        'Category': '',
        'Subcategory': '',
        'weight_range_code': '',
        'weight_range': '',
        'Pcs Rcv': merged_df['Pcs Rcv'].sum(),
        'Weight Rcv': round(merged_df['Weight Rcv'].sum(), 2),
        'Pcs Sold': merged_df['Pcs Sold'].sum(),
        'Weight Sold': round(merged_df['Weight Sold'].sum(), 2),
        'Existing Pcs': merged_df['Existing Pcs'].sum(),
        'Existing Weight': round(merged_df['Existing Weight'].sum(), 2),
        'min_pcs': merged_df['min_pcs'].sum(),
        'min_qty': round(merged_df['min_qty'].sum(), 2),
        'Diff_pieces': merged_df['Diff_pieces'].sum(),
        'Diff_weight': round(merged_df['Diff_weight'].sum(), 2)
    }
    
    merged_df = pd.concat([merged_df, pd.DataFrame([total_row])], ignore_index=True)
    merged_df.reset_index(drop=True, inplace=True)
    
    return merged_df


def generate_all_inventory_tables(
    opt_gold_df,
    sold_df,
    received_df,
    existing_received_df
):
    # Dynamically build category to counter mapping dictionary from transactions
    cat_to_counter = {}
    
    if not received_df.empty:
        for _, row in received_df.iterrows():
            cat = str(row.get('ornament_category_code', '')).strip().upper()
            cnt = str(row.get('counter_code', '')).strip().upper()
            if cat and cnt:
                cat_to_counter[cat] = cnt
                
    if not sold_df.empty:
        for _, row in sold_df.iterrows():
            cat = str(row.get('ornament_category_code', '')).strip().upper()
            cnt = str(row.get('counter', '')).strip().upper()
            if cat and cnt:
                cat_to_counter[cat] = cnt

    # 1. Map transaction datasets to weight ranges in opt_gold ONCE globally
    sold_mapped = map_tags_to_weight_ranges(sold_df, opt_gold_df, 'bom_qty')
    received_mapped = map_tags_to_weight_ranges(received_df, opt_gold_df, 'net_weight')
    existing_mapped = map_tags_to_weight_ranges(existing_received_df, opt_gold_df, 'net_weight')
    
    # 2. Independently aggregate datasets by location, category, subcategory and weight range ONCE globally
    group_cols = ['location_name', 'ornament_category_code', 'ornament_sub_category_code', 'weight_range_code']
    
    sold_grouped = pd.DataFrame(columns=group_cols + ['Pcs Sold', 'Weight Sold'])
    if not sold_mapped.empty:
        sold_grouped = (
            sold_mapped.groupby(group_cols, as_index=False, observed=True)
            .agg({'tag_no': 'count', 'bom_qty': 'sum'})
            .rename(columns={'tag_no': 'Pcs Sold', 'bom_qty': 'Weight Sold'})
        )
        
    received_grouped = pd.DataFrame(columns=group_cols + ['Pcs Rcv', 'Weight Rcv'])
    if not received_mapped.empty:
        received_grouped = (
            received_mapped.groupby(group_cols, as_index=False, observed=True)
            .agg({'tag_no.': 'count', 'net_weight': 'sum'})
            .rename(columns={'tag_no.': 'Pcs Rcv', 'net_weight': 'Weight Rcv'})
        )
        
    existing_grouped = pd.DataFrame(columns=group_cols + ['Existing Pcs', 'Existing Weight'])
    if not existing_mapped.empty:
        existing_grouped = (
            existing_mapped.groupby(group_cols, as_index=False, observed=True)
            .agg({'tag_no.': 'count', 'net_weight': 'sum'})
            .rename(columns={'tag_no.': 'Existing Pcs', 'net_weight': 'Existing Weight'})
        )

    all_tables = {}
    for counter in COUNTER_ORDER:
        try:
            tbl = generate_inventory_table(
                opt_gold_df=opt_gold_df,
                sold_grouped=sold_grouped,
                received_grouped=received_grouped,
                existing_grouped=existing_grouped,
                counter_name=counter,
                cat_to_counter=cat_to_counter
            )
            if not tbl.empty:
                all_tables[counter] = tbl
        except Exception as e:
            print(f"Error generating inventory table for {counter}: {e}")
            
    return all_tables
