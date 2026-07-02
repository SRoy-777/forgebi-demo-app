import os
import re
import pandas as pd

# Define paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
PAGES_DIR = os.path.join(PROJECT_ROOT, "app", "pages")
APP_PY_PATH = os.path.join(PROJECT_ROOT, "app", "app.py")

# Special casings dict
SPECIAL_CASES = {
    'nsv': 'NSV',
    'roas': 'ROAS',
    'it': 'IT',
    'hr': 'HR',
}

def parse_filename(filename):
    base, ext = os.path.splitext(filename)
    if ext.lower() != '.py':
        return None
    
    # Ignore home, __init__, and login files
    if base.lower() in ('home', '__init__', 'login'):
        return None
        
    # Extract Dashboard ID by stripping _dash or _dashboard suffix and replacing underscores
    db_id = re.sub(r'_(dash|dashboard)$', '', base, flags=re.IGNORECASE)
    db_id = db_id.replace('_', '-')
    
    if db_id == 'roas-conversion':
        db_id = 'roas-conversion-analytics'
        name = 'ROAS Conversion Analytics'
    else:
        # Format Dashboard Name
        if base.lower().endswith('_dash'):
            name_base = base[:-5]
            name = " ".join([SPECIAL_CASES.get(w.lower(), w.capitalize()) for w in name_base.split('_')])
        elif base.lower().endswith('_dashboard'):
            name_base = base[:-10]
            name = " ".join([SPECIAL_CASES.get(w.lower(), w.capitalize()) for w in name_base.split('_')]) + " Dashboard"
        else:
            name = " ".join([SPECIAL_CASES.get(w.lower(), w.capitalize()) for w in base.split('_')])
        
    return db_id, name

def generate_catalog_data():
    if not os.path.exists(PAGES_DIR):
        return pd.DataFrame(columns=['Dashboard ID', 'Dashboard Name', 'Module', 'File Path', 'Python File Name', 'Dashboard Active'])
    
    # Read app.py content to identify registered (active) dashboards
    app_content = ""
    if os.path.exists(APP_PY_PATH):
        try:
            with open(APP_PY_PATH, 'r', encoding='utf-8') as f:
                app_content = f.read()
        except Exception as e:
            print(f"Error reading app.py: {e}")
            
    db_dict = {}
    
    for root, dirs, files in os.walk(PAGES_DIR):
        rel_path = os.path.relpath(root, PAGES_DIR)
        if rel_path == '.':
            continue
            
        parts = rel_path.split(os.sep)
        module_folder = parts[0]
        # Convert module folder to permission identifier format (e.g. customer_care -> customer-care)
        module_name = module_folder.replace('_', '-')
        
        for file in files:
            parsed = parse_filename(file)
            if not parsed:
                continue
            db_id, db_name = parsed
            
            # Build relative path from project root
            full_file_path = os.path.join(root, file)
            proj_rel_path = os.path.relpath(full_file_path, PROJECT_ROOT).replace('\\', '/')
            
            # Check if active (i.e. is routed inside app.py)
            is_active = f"/{db_id}" in app_content
            
            if db_id not in db_dict:
                db_dict[db_id] = {
                    'Dashboard ID': db_id,
                    'Dashboard Name': db_name,
                    'Modules': [module_name],
                    'File Paths': [proj_rel_path],
                    'Python File Name': file,
                    'Dashboard Active': 'Yes' if is_active else 'No'
                }
            else:
                if module_name not in db_dict[db_id]['Modules']:
                    db_dict[db_id]['Modules'].append(module_name)
                if proj_rel_path not in db_dict[db_id]['File Paths']:
                    db_dict[db_id]['File Paths'].append(proj_rel_path)
                    
    # Flatten the dynamic registry into rows
    rows = []
    for db_id, data in db_dict.items():
        rows.append({
            'Dashboard ID': db_id,
            'Dashboard Name': data['Dashboard Name'],
            'Module': ", ".join(sorted(data['Modules'])),
            'File Path': ", ".join(data['File Paths']),
            'Python File Name': data['Python File Name'],
            'Dashboard Active': data['Dashboard Active']
        })
        
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=['Dashboard ID', 'Dashboard Name', 'Module', 'File Path', 'Python File Name', 'Dashboard Active'])
    
    return df.sort_values(by='Dashboard ID').reset_index(drop=True)

def generate_export_dataframe(search_val=None, selected_modules=None):
    df = generate_catalog_data()
    
    if search_val:
        search_query = search_val.strip().lower()
        df = df[
            df['Dashboard Name'].str.lower().str.contains(search_query, na=False) |
            df['Dashboard ID'].str.lower().str.contains(search_query, na=False) |
            df['Python File Name'].str.lower().str.contains(search_query, na=False)
        ]
        
    if selected_modules:
        mask = df['Module'].apply(lambda x: any(mod in [m.strip() for m in x.split(',')] for mod in selected_modules))
        df = df[mask]
        
    return df
