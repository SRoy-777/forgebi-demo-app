import calendar

import pandas as pd

from backend.cache.data_cache import (
    merged_sales_df,
    branch_daily_aggregate_df,
    rm_zm_df,
)

from backend.services.rls import get_allowed_locations


# ---------------------------------------------------
# Safe Division
# ---------------------------------------------------

def safe_divide(numerator, denominator):

    if pd.isna(denominator) or denominator == 0:
        return 0

    try:
        return numerator / denominator
    except Exception:
        return 0


# ---------------------------------------------------
# Helpers
# ---------------------------------------------------

def _apply_rls_sales(df):

    allowed_locations = get_allowed_locations()

    if 'ALL' not in allowed_locations:
        df = df[df['Location Name'].isin(allowed_locations)]

    return df


def _apply_rls_branch(df):

    allowed_locations = get_allowed_locations()

    if 'ALL' not in allowed_locations:
        df = df[df['Location'].isin(allowed_locations)]

    return df


def _apply_rm_zm_location_filters(df, location_col, locations=None, rms=None, zms=None):

    rz = rm_zm_df.copy()

    rz['location'] = (
        rz['location']
        .astype(str)
        .str.strip()
        .str.upper()
    )

    rz['rm'] = (
        rz['rm']
        .astype(str)
        .str.strip()
        .str.upper()
    )

    rz['zm'] = (
        rz['zm']
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df[location_col] = (
        df[location_col]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    if rms:

        rms = [str(i).strip().upper() for i in rms]

        rm_locations = rz[rz['rm'].isin(rms)]['location'].unique()

        df = df[df[location_col].isin(rm_locations)]

    if zms:

        zms = [str(i).strip().upper() for i in zms]

        zm_locations = rz[rz['zm'].isin(zms)]['location'].unique()

        df = df[df[location_col].isin(zm_locations)]

    if locations:

        locations = [str(i).strip().upper() for i in locations]

        df = df[df[location_col].isin(locations)]

    return df


def _filter_sales_by_date(df, start_date, end_date):

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    return df[
        (df['Invoice Date'] >= start_date)
        & (df['Invoice Date'] <= end_date)
    ]


def _filter_branch_by_date(df, start_date, end_date):

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    return df[
        (df['Date'] >= start_date)
        & (df['Date'] <= end_date)
    ]


def _full_month_range_from_selection(start_date, end_date):

    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    month_start = start.replace(day=1)

    last_day = calendar.monthrange(end.year, end.month)[1]

    month_end = end.replace(day=last_day)

    return month_start, month_end


def _prepare_sales(start_date, end_date, locations=None, rms=None, zms=None):

    df = merged_sales_df.copy()

    df['Invoice Date'] = pd.to_datetime(df['Invoice Date'])

    df = _apply_rls_sales(df)

    df = _apply_rm_zm_location_filters(
        df,
        'Location Name',
        locations=locations,
        rms=rms,
        zms=zms,
    )

    df = _filter_sales_by_date(df, start_date, end_date)

    for col in [
        'Sales Type',
        'Bom UOM',
        'Bom Item Type',
        'Item Type Group',
        'Brand Id',
        'Bom Item',
        'Counter',
        'Document No.',
        'Customer Code',
        'Tag No',
        'Item Name',
        'Ornament Sub Category Code',
    ]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
            )

    for col in [
        'Payble Amount',
        'Bom Line Amount',
        'Bom Qty',
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df


def _prepare_footfall(start_date, end_date, locations=None, rms=None, zms=None):

    df = branch_daily_aggregate_df.copy()

    df = _apply_rls_branch(df)

    df = _apply_rm_zm_location_filters(
        df,
        'Location',
        locations=locations,
        rms=rms,
        zms=zms,
    )

    df = _filter_branch_by_date(df, start_date, end_date)

    return df


# ---------------------------------------------------
# Part 1 — Company KPIs
# ---------------------------------------------------

def get_part1_kpis(start_date, end_date, locations=None, rms=None, zms=None):

    df = _prepare_sales(start_date, end_date, locations, rms, zms)
    footfall_df = _prepare_footfall(start_date, end_date, locations, rms, zms)

    gross_sales = df['Payble Amount'].sum()
    net_sales = df['Bom Line Amount'].sum()

    sales_rows = df[df['Sales Type'] == 'Sales'].copy()

    invoice_docs = sales_rows[
        sales_rows['Document No.'].notna()
        & (sales_rows['Document No.'] != '')
        & (sales_rows['Document No.'] != 'nan')
    ]['Document No.'].nunique()

    footfall = footfall_df['Footfall'].sum() if not footfall_df.empty else 0

    unique_customers = (
        df['Customer Code']
        .replace('', pd.NA)
        .dropna()
        .nunique()
    )

    atv = safe_divide(net_sales, invoice_docs)
    conversion_pct = safe_divide(unique_customers, footfall) * 100

    gold_mask = (
        (df['Bom UOM'] == 'GMS')
        & (df['Bom Item Type'] == 'GOLD')
    )

    gold_gms = df.loc[gold_mask, 'Bom Qty'].sum()

    purity_map = {
        'GOLD-22K': '22K',
        'GOLD-18K': '18K',
        'GOLD-14K': '14K',
        'GOLD-24K-99.50': '24K',
        'RM-B-GOLD-24K-99.50': '24K',
    }

    purity_rows = df[gold_mask & df['Bom Item'].isin(purity_map.keys())].copy()
    purity_rows['purity_bucket'] = purity_rows['Bom Item'].map(purity_map)

    purity_breakdown = (
        purity_rows
        .groupby('purity_bucket', as_index=False)['Bom Qty']
        .sum()
    )

    purity_dict = {
        row['purity_bucket']: row['Bom Qty']
        for _, row in purity_breakdown.iterrows()
    }

    diamond_cts = df[
        (df['Bom UOM'] == 'CTS')
        & (df['Bom Item Type'] == 'DIAMOND')
    ]['Bom Qty'].sum()

    silver_gms = df[
        (df['Bom UOM'] == 'GMS')
        & (df['Bom Item Type'] == 'SILVER')
        & (df['Item Type Group'] == 'SILVER')
    ]['Bom Qty'].sum()

    mohor_df = df[df['Brand Id'] == 'MOHOR']
    mohor_gms = mohor_df['Bom Qty'].sum()
    mohor_nsv = mohor_df['Bom Line Amount'].sum()

    gemstone_nsv = df[
        (df['Bom Item Type'] == 'STONE_CT')
        & (df['Item Type Group'] == 'NONE')
    ]['Bom Line Amount'].sum()

    return {
        'gross_sales': gross_sales,
        'net_sales': net_sales,
        'invoices': invoice_docs,
        'atv': atv,
        'conversion_pct': conversion_pct,
        'footfall': footfall,
        'gold_gms': gold_gms,
        'purity_18k': purity_dict.get('18K', 0),
        'purity_22k': purity_dict.get('22K', 0),
        'purity_14k': purity_dict.get('14K', 0),
        'purity_24k': purity_dict.get('24K', 0),
        'diamond_cts': diamond_cts,
        'silver_gms': silver_gms,
        'mohor_gms': mohor_gms,
        'mohor_nsv': mohor_nsv,
        'gemstone_nsv': gemstone_nsv,
    }


# ---------------------------------------------------
# Part 2 — Metal contribution
# ---------------------------------------------------

def get_part2_metal_contribution(start_date, end_date, locations=None, rms=None, zms=None):

    df = _prepare_sales(start_date, end_date, locations, rms, zms)

    total_nsv = df['Bom Line Amount'].sum()

    gold_nsv = df[
        (df['Bom UOM'] == 'GMS')
        & (df['Bom Item Type'] == 'GOLD')
    ]['Bom Line Amount'].sum()

    gold_qty = df[
        (df['Bom UOM'] == 'GMS')
        & (df['Bom Item Type'] == 'GOLD')
    ]['Bom Qty'].sum()

    diamond_nsv = df[
        (df['Bom UOM'] == 'CTS')
        & (df['Bom Item Type'] == 'DIAMOND')
    ]['Bom Line Amount'].sum()

    diamond_qty = df[
        (df['Bom UOM'] == 'CTS')
        & (df['Bom Item Type'] == 'DIAMOND')
    ]['Bom Qty'].sum()

    silver_nsv = df[
        (df['Bom UOM'] == 'GMS')
        & (df['Bom Item Type'] == 'SILVER')
        & (df['Item Type Group'] == 'SILVER')
    ]['Bom Line Amount'].sum()

    silver_qty = df[
        (df['Bom UOM'] == 'GMS')
        & (df['Bom Item Type'] == 'SILVER')
        & (df['Item Type Group'] == 'SILVER')
    ]['Bom Qty'].sum()

    mohor_df = df[df['Brand Id'] == 'MOHOR']
    mohor_nsv = mohor_df['Bom Line Amount'].sum()
    mohor_qty = mohor_df['Bom Qty'].sum()

    gemstone_nsv = df[
        (df['Bom Item Type'] == 'STONE_CT')
        & (df['Item Type Group'] == 'NONE')
    ]['Bom Line Amount'].sum()

    others_nsv = (
        total_nsv
        - gold_nsv
        - diamond_nsv
        - silver_nsv
        - mohor_nsv
        - gemstone_nsv
    )

    qty_metals = ['Gold', 'Diamond', 'Silver', 'Mohor']

    rows = [
        ('Gold', gold_nsv, gold_qty),
        ('Diamond', diamond_nsv, diamond_qty),
        ('Silver', silver_nsv, silver_qty),
        ('Mohor', mohor_nsv, mohor_qty),
        ('Gemstone', gemstone_nsv, 0),
        ('Others', others_nsv, 0),
    ]

    result = []

    for metal, nsv, qty in rows:
        result.append({
            'Metal': metal,
            'NSV': round(nsv, 0),
            'Qty Sold': round(qty, 2) if metal in qty_metals else '',
            'Contribution %': round(safe_divide(nsv, total_nsv) * 100, 2),
        })

    return pd.DataFrame(result)


# ---------------------------------------------------
# Part 3 — Top products
# ---------------------------------------------------

def _tag_qty_for_row(tag_df):

    counter = str(tag_df['Counter'].iloc[0])

    if counter.startswith('G-'):
        return tag_df[tag_df['Bom UOM'] == 'GMS']['Bom Qty'].sum()

    if counter == 'DIAMOND':
        return tag_df[tag_df['Bom UOM'] == 'CTS']['Bom Qty'].sum()

    return tag_df[tag_df['Bom UOM'].isin(['GMS', 'CTS'])]['Bom Qty'].sum()


def _build_top_products(start_date, end_date, locations=None, rms=None, zms=None):

    df = _prepare_sales(start_date, end_date, locations, rms, zms)
    df = df[df['Sales Type'] == 'Sales'].copy()

    empty = pd.DataFrame(
        columns=[
            'Product Name',
            'Sub Category',
            'Qty',
            'Revenue',
        ]
    )

    if df.empty:
        return empty

    df = df[
        df['Tag No'].notna()
        & (df['Tag No'] != '')
        & (df['Tag No'] != 'nan')
    ]

    if df.empty:
        return empty

    tag_records = []

    for _, tag_df in df.groupby('Tag No'):

        revenue = tag_df['Bom Line Amount'].sum()
        qty = _tag_qty_for_row(tag_df)

        tag_records.append({
            'Product Name': tag_df['Item Name'].iloc[0],
            'Sub Category': tag_df['Ornament Sub Category Code'].iloc[0],
            'Qty': qty,
            'Revenue': revenue,
        })

    tag_level = pd.DataFrame(tag_records)

    product_df = (
        tag_level
        .groupby(
            ['Product Name', 'Sub Category'],
            as_index=False
        )
        .agg({
            'Qty': 'sum',
            'Revenue': 'sum',
        })
    )

    product_df = (
        product_df
        .sort_values('Revenue', ascending=False)
        .head(5)
        .reset_index(drop=True)
    )

    product_df['Qty'] = product_df['Qty'].round(2)
    product_df['Revenue'] = product_df['Revenue'].round(0)

    return product_df


def get_part3_top_products(start_date, end_date, locations=None, rms=None, zms=None):

    full_month_start, full_month_end = _full_month_range_from_selection(
        start_date,
        end_date,
    )

    period_df = _build_top_products(
        start_date,
        end_date,
        locations,
        rms,
        zms,
    )

    full_months_df = _build_top_products(
        full_month_start,
        full_month_end,
        locations,
        rms,
        zms,
    )

    return {
        'period': period_df,
        'full_months': full_months_df,
        'full_month_start': full_month_start.strftime('%Y-%m-%d'),
        'full_month_end': full_month_end.strftime('%Y-%m-%d'),
    }


# ---------------------------------------------------
# Export
# ---------------------------------------------------

def generate_export_dataframe(
    start_date,
    end_date,
    locations=None,
    rms=None,
    zms=None,
):

    data = generate_company_snapshot_dashboard_data(
        start_date,
        end_date,
        locations=locations,
        rms=rms,
        zms=zms,
    )

    export_rows = []

    part1_labels = {
        'gross_sales': 'Gross Sales',
        'net_sales': 'Net Sales',
        'invoices': 'Invoices Generated',
        'atv': 'ATV',
        'conversion_pct': 'Conversion %',
        'footfall': 'Footfall',
        'gold_gms': 'Gold Gms Sold',
        'purity_18k': 'Gold 18K Gms',
        'purity_22k': 'Gold 22K Gms',
        'purity_14k': 'Gold 14K Gms',
        'purity_24k': 'Gold 24K Gms',
        'diamond_cts': 'Diamond Cts Sold',
        'silver_gms': 'Silver Gms Sold',
        'mohor_gms': 'Mohor Gms Sold',
        'mohor_nsv': 'Mohor NSV Sold',
        'gemstone_nsv': 'Gemstone NSV Sold',
    }

    for key, label in part1_labels.items():
        export_rows.append({
            'Section': 'Part 1 - KPIs',
            'Metric': label,
            'Value': data['part1'][key],
        })

    part2_df = data['part2'].copy()
    part2_df.insert(0, 'Section', 'Part 2 - Metal Contribution')

    part3_period = data['part3']['period'].copy()
    part3_period.insert(0, 'Section', 'Part 3 - Selected Period')

    part3_months = data['part3']['full_months'].copy()
    part3_months.insert(0, 'Section', 'Part 3 - Full Months')

    kpi_export = pd.DataFrame(export_rows)

    return pd.concat(
        [
            kpi_export,
            part2_df,
            part3_period,
            part3_months,
        ],
        ignore_index=True,
        sort=False,
    )


# ---------------------------------------------------
# Main Export
# ---------------------------------------------------

def generate_company_snapshot_dashboard_data(
    start_date,
    end_date,
    locations=None,
    rms=None,
    zms=None,
):

    return {
        'part1': get_part1_kpis(
            start_date,
            end_date,
            locations,
            rms,
            zms,
        ),
        'part2': get_part2_metal_contribution(
            start_date,
            end_date,
            locations,
            rms,
            zms,
        ),
        'part3': get_part3_top_products(
            start_date,
            end_date,
            locations,
            rms,
            zms,
        ),
        'start_date': pd.to_datetime(start_date).strftime('%Y-%m-%d'),
        'end_date': pd.to_datetime(end_date).strftime('%Y-%m-%d'),
    }
