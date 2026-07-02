import pandas as pd
from database.connections.postgres_connection import engine


# ------------------
# 0. Get Locations
# ------------------

def get_locations():

    query = """

    SELECT DISTINCT "Location Name"

    FROM merged_sales

    ORDER BY "Location Name"

"""

    df = pd.read_sql(query, con=engine)

    return df


# ------------------
# 1. Total Sales
# ------------------

def get_total_sales():

    query = """

    SELECT
        SUM("Bom Line Amount") AS total_sales
    FROM merged_sales

    """

    df = pd.read_sql(query, con=engine)

    return df



# ------------------
# 2 Sales By Location
# ------------------

def get_sales_by_location(start_date, end_date, location=None):

    location_filter = ""

    if location: 
        location_filter = f"""
        AND "Location Name" = '{location}'
        """


    query = f"""

    SELECT
        "Location Name",
        SUM("Bom Line Amount") AS total_sales
    FROM merged_sales
    WHERE "Invoice Date" 
        BETWEEN '{start_date}' AND '{end_date}'

        {location_filter}

    GROUP BY "Location Name"
    ORDER BY total_sales DESC

    """

    df = pd.read_sql(query, con=engine)

    return df



# ------------------
# 3. Sales By date
# ------------------

def get_sales_by_date(start_date, end_date, location=None):

    location_filter = ""

    if location:
        location_filter = f"""
        AND "Location Name" = '{location}'
        """


    query = f"""

    SELECT 
        SUM("Bom Line Amount") AS total_sales
    FROM merged_sales
    WHERE "Invoice Date" 
            BETWEEN '{start_date}' AND '{end_date}'
            {location_filter}
"""

    df = pd.read_sql(query, con=engine)

    return df

# ------------------
# 4. Gold Sale By Date
# ------------------

def gold_sale_by_date(start_date, end_date, location=None):

    location_filter = ""
    
    if location:
        location_filter = f"""
        AND "Location Name" = '{location}'
        """

    query = f"""
    SELECT 
        SUM("Bom Qty") AS Gold_w
    FROM merged_sales
    WHERE "Invoice Date" 
            BETWEEN '{start_date}' AND '{end_date}'
        AND "Bom UOM" = 'GMS'
        AND "Bom Item Type" = 'GOLD'
        {location_filter}

"""

    df = pd.read_sql(query, con=engine)

    return df

# ------------------
# 5. Silver Sale By Date
# ------------------


def silver_sale_by_date(start_date, end_date, location=None):

    location_filter = ""
    
    if location:
        location_filter = f"""
        AND "Location Name" = '{location}'
        """

    query = f"""
    SELECT 
        SUM("Bom Qty") AS Silver_w
    FROM merged_sales
    WHERE "Invoice Date" 
            BETWEEN '{start_date}' AND '{end_date}'
        AND "Bom UOM" = 'GMS'
        AND "Bom Item Type" = 'SILVER'
        AND "Item Type Group" = 'SILVER'
        {location_filter}

"""

    df = pd.read_sql(query, con=engine)

    return df

# ------------------
# 6. Diamond Sale By Date
# ------------------


def diamond_sale_by_date(start_date, end_date, location=None):

    location_filter = ""
    
    if location:
        location_filter = f"""
        AND "Location Name" = '{location}'
        """

    query = f"""
    SELECT 
        SUM("Bom Qty") AS diamond_w
    FROM merged_sales
    WHERE "Invoice Date" 
            BETWEEN '{start_date}' AND '{end_date}'
        AND "Bom UOM" = 'CTS'
        AND "Bom Item Type" = 'DIAMOND'
        {location_filter}

"""

    df = pd.read_sql(query, con=engine)

    return df

# ------------------
# 7. Gemstone Sale By Date
# ------------------


def gemstone_sale_by_date(start_date, end_date, location=None):

    location_filter = ""
    
    if location:
        location_filter = f"""
        AND "Location Name" = '{location}'
        """

    query = f"""
    SELECT 
        SUM("Bom Line Amount") AS gem_nsv
    FROM merged_sales
    WHERE "Invoice Date" 
            BETWEEN '{start_date}' AND '{end_date}'
        AND "Bom Item Type" = 'STONE_CT'
        AND "Item Type Group" = 'NONE'
        {location_filter}

"""

    df = pd.read_sql(query, con=engine)

    return df

# ------------------
# 8. Mohor Sale By Date
# ------------------


def mohor_nsv_sale_by_date(start_date, end_date, location=None):

    location_filter = ""
    
    if location:
        location_filter = f"""
        AND "Location Name" = '{location}'
        """

    query = f"""
    SELECT 
        SUM("Bom Line Amount") AS mohor_nsv
    FROM merged_sales
    WHERE "Invoice Date" 
            BETWEEN '{start_date}' AND '{end_date}'
        AND "Brand Id" = 'MOHOR'
        {location_filter}

"""

    df = pd.read_sql(query, con=engine)

    return df

# ------------------
# 9. Mohor Weight Sale By Date
# ------------------


def mohor_w_sale_by_date(start_date, end_date, location=None):

    location_filter = ""
    
    if location:
        location_filter = f"""
        AND "Location Name" = '{location}'
        """

    query = f"""
    SELECT 
        SUM("Bom Qty") AS mohor_w
    FROM merged_sales
    WHERE "Invoice Date" 
            BETWEEN '{start_date}' AND '{end_date}'
        AND "Brand Id" = 'MOHOR'
        {location_filter}

"""

    df = pd.read_sql(query, con=engine)

    return df

# ------------------
# 10. MC collected By Date
# ------------------

def making_collected_by_date(start_date, end_date, location=None):

    location_filter = ""
    
    if location:

        location_filter = f"""
        AND "Location Name" = '{location}'
        """

    query = f"""

    SELECT 
        SUM("Bom Line Amount") AS mc_collected

    FROM merged_sales
    WHERE "Invoice Date" 
            BETWEEN '{start_date}' AND '{end_date}'
        AND "Bom Item" LIKE 'MK%%'
        {location_filter}

"""

    df = pd.read_sql(query, con=engine)

    return df
