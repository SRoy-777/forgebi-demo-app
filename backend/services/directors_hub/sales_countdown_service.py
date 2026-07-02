import random
from datetime import datetime
import pandas as pd

from backend.cache.data_cache import merged_sales_df
from backend.services.rls import get_allowed_locations

# Global cache to store the pre-calculated simulation curve for the day
# Key: (session_seed, target_sales) -> list of sales values of length 34201
_SIMULATION_CACHE = {}

def get_target_sales_data():
    """
    Returns the most recent invoice date and the total sales (SUM of Bom Line Amount)
    for that date, respecting RLS logic.
    """
    df = merged_sales_df.copy()
    allowed_locations = get_allowed_locations()
    if 'ALL' not in allowed_locations:
        df = df[df['Location Name'].isin(allowed_locations)]
        
    df['Invoice Date'] = pd.to_datetime(df['Invoice Date'])
    latest_invoice_date = df['Invoice Date'].max()
    
    if pd.isna(latest_invoice_date):
        return None, 0.0
        
    latest_sales_df = df[df['Invoice Date'] == latest_invoice_date]
    target_sales = latest_sales_df['Bom Line Amount'].sum()
    
    return latest_invoice_date, float(target_sales)

def get_simulated_sales_array(session_seed, target_sales):
    """
    Generates a deterministic in-memory array of simulated sales values for each second
    between 11:00 AM and 8:30 PM (34200 seconds total).
    The path is seeded by the session_seed.
    
    Sales increments mimic real jewelry sales (transactions of ₹3,000 to ₹5,00,000)
    happening occasionally, meaning the sales figure does not change every second.
    """
    cache_key = (session_seed, target_sales)
    if cache_key in _SIMULATION_CACHE:
        return _SIMULATION_CACHE[cache_key]
        
    rng = random.Random(session_seed)
    
    # Starting sales value between 25k and 100k
    start_sales = rng.uniform(25000, 100000)
    if target_sales <= start_sales:
        start_sales = max(0.0, target_sales * 0.1)
        
    total_seconds = 34200
    remaining_sales = target_sales - start_sales
    
    # Generate discrete transactions between 3,000 and 5,000
    transactions = []
    R = remaining_sales
    
    if R < 3000:
        if R > 0:
            transactions.append(R)
    else:
        while R > 5000:
            x = rng.uniform(3000, 5000)
            transactions.append(x)
            R -= x
            
        if R >= 3000:
            transactions.append(R)
        elif R > 0:
            if transactions:
                transactions[-1] += R
            else:
                transactions.append(R)
                
    # Randomly distribute the transaction indices across the business day
    # We choose len(transactions) distinct second indices in [0, total_seconds - 1]
    if transactions:
        num_txs = len(transactions)
        # Avoid sample size exceeding range
        num_txs = min(num_txs, total_seconds)
        indices = sorted(rng.sample(range(total_seconds), num_txs))
        # Map indices to transactions
        tx_map = {idx: transactions[i] for i, idx in enumerate(indices[:num_txs])}
    else:
        tx_map = {}
        
    sales_array = [round(start_sales, 2)]
    current_sales = start_sales
    
    for s in range(total_seconds):
        if s in tx_map:
            current_sales += tx_map[s]
        sales_array.append(round(current_sales, 2))
        
    # Enforce exact target at the end
    sales_array[-1] = round(target_sales, 2)
    
    _SIMULATION_CACHE[cache_key] = sales_array
    return sales_array

def get_current_countdown_state(session_seed):
    """
    Evaluates the countdown state for the current system time and session seed.
    Uses India Standard Time (IST) to ensure timezone consistency.
    """
    latest_date, target_sales = get_target_sales_data()
    
    from datetime import timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(IST)
    current_time_str = now.strftime('%H:%M:%S')
    
    # Business Hour boundaries (11:00:00 AM to 08:30:00 PM IST)
    start_time = now.replace(hour=11, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=20, minute=30, second=0, microsecond=0)
    
    if now < start_time:
        # Before hours: display start text and current time
        # The starting value can be calculated or initialized
        sales_array = get_simulated_sales_array(session_seed, target_sales)
        return {
            'status': 'BEFORE',
            'current_time': current_time_str,
            'sales_value': sales_array[0],
            'target_sales': target_sales,
            'latest_invoice_date': latest_date.strftime('%Y-%m-%d') if latest_date else ''
        }
    elif now >= end_time:
        # After hours: display target achieved
        return {
            'status': 'AFTER',
            'current_time': current_time_str,
            'sales_value': target_sales,
            'target_sales': target_sales,
            'latest_invoice_date': latest_date.strftime('%Y-%m-%d') if latest_date else ''
        }
    else:
        # During hours: active countdown
        elapsed_seconds = int((now - start_time).total_seconds())
        # Safeguard index boundaries
        elapsed_seconds = max(0, min(elapsed_seconds, 34200))
        
        sales_array = get_simulated_sales_array(session_seed, target_sales)
        return {
            'status': 'DURING',
            'current_time': current_time_str,
            'sales_value': sales_array[elapsed_seconds],
            'target_sales': target_sales,
            'latest_invoice_date': latest_date.strftime('%Y-%m-%d') if latest_date else ''
        }
