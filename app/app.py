import os
import sys

# Ensure the project root directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import request, session

from pages import home
from pages import login

from dash import (
    Dash,
    dcc,
    html,
    Input,
    Output,
    State
)

import dash_bootstrap_components as dbc

from datetime import timedelta

from pages.sales import performance_dashboard
from pages.sales import mini_nsv_dash
from pages.sales import comparison_dash
from pages.inventory import aging_stock_dash
from pages.customer_care import daily_customer_dash
from pages.inventory import stock_movement_dash
from pages.inventory import design_performance_dash
from pages.sales import branch_health_dash
from pages.sales import old_gold_dash
from pages.sales import period_comparison_dash
from pages.directors_hub import company_snapshot_dash
from pages.directors_hub import sales_countdown_dash
from pages.customer_care import dormant_customer_dash
from pages.directors_hub import live_customer_dash
from pages.execution_tracker import home as execution_tracker_dash
from pages.sales import employee_performance_dash
from pages.sales import customer_bucket_dash
from pages.accounts import profitability_analysis_Dash
from pages.accounts import roas_conversion_dash
from pages.admin_hub import dashboard_catalog_dash
from pages.admin_hub import user_settings_dash
from pages.sales import live_customer_dash as sales_live_customer_dash
from pages.sales import sme_performance_dash
from pages.sales import geo_analytics_dash




from pages.sales.basket_analysis_dash import (
    layout as basket_analysis_layout
)

from pages.inventory.inventory_optimization_dash import (
    layout as inventory_optimization_layout
)

from pages.procurement.vendor_analysis_dash import (
    layout as vendor_analysis_layout
)

from pages.inventory.home import (
    layout as inventory_home_layout
)

from pages.procurement.home import (
    layout as procurement_home_layout
)

from pages.sales.home import (
    layout as sales_home_layout
)

from pages.customer_care.home import (
    layout as customer_care_home_layout
)

from pages.directors_hub.home import (
    layout as directors_hub_home_layout
)

from pages.accounts.home import (
    layout as accounts_home_layout
)

from pages.hr.home import (
    layout as hr_home_layout
)

from pages.it.home import (
    layout as it_home_layout
)

from pages.marketing.home import (
    layout as marketing_home_layout
)

from pages.admin_hub.home import (
    layout as admin_hub_home_layout
)


from backend.cache import data_cache
from backend.services.auth import validate_user


# ---------------------------------------------------
# App Initialization
# ---------------------------------------------------

app = Dash(

    __name__,

    title="Orient BI",

    external_stylesheets=[
        dbc.themes.BOOTSTRAP
    ],

    suppress_callback_exceptions=True

)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="icon" type="image/png" href="/assets/orient_logo_for_dark_theme.png">
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

server = app.server


# ---------------------------------------------------
# Session Configuration
# ---------------------------------------------------

server.secret_key = "orient_bi_secret_key"

server.permanent_session_lifetime = timedelta(days=30)

SESSION_VERSION = "v26"


# ---------------------------------------------------
# Block Direct HF Access
# ---------------------------------------------------

@server.before_request
def block_hf_space_access():

    current_host = request.host


    # Allow HF internal signed traffic
    if "__sign" in request.url:

        return None


    if "hf.space" in current_host:

        return """

        <h1 style='text-align:center;
                   margin-top:100px;
                   font-family:Arial;'>

            Direct access is blocked.

        </h1>

        """, 403


# ---------------------------------------------------
# Main Layout
# ---------------------------------------------------

app.layout = html.Div([

    dcc.Location(

        id='url',

        refresh=False

    ),

    html.Div(

        id='page-content'

    )

])


# ---------------------------------------------------
# Dynamic Browser Tab Title Callback
# ---------------------------------------------------

app.layout.children.append(
    html.Div(id='dummy-title-output', style={'display': 'none'})
)

app.clientside_callback(
    """
    function(pathname) {
        if (!pathname || pathname === '/' || pathname === '/home') {
            document.title = 'Orient BI';
            return '';
        }
        
        let name = pathname.substring(1);
        
        const customNames = {
            'roas-conversion-analytics': 'ROAS & Conversion',
            'profitability-analysis': 'Profitability Analysis',
            'inventory-optimization': 'Inventory Optimization',
            'employee-performance': 'Employee Performance',
            'sme-performance': 'SME Performance',
            'dormant-customer': 'Dormant Customer List',
            'daily-customer': 'Daily Customer',
            'design-performance': 'Design Performance',
            'branch-health': 'Branch Health',
            'old-gold': 'Old Gold',
            'period-comparison': 'Period Comparison',
            'company-snapshot': 'Company Snapshot',
            'sales-countdown': 'Sales Countdown',
            'live-customer': 'Live Customer Counter',
            'live-customer-counter': 'Live Customer Counter',
            'vendor-analysis': 'Vendor Analysis',
            'basket-analysis': 'Basket Analysis',
            'customer-bucket': 'Customer Bucket Analysis',
            'geo-analytics': 'Geo Analytics',
            'execution-tracker': 'Execution Tracker',
            'dashboard-catalog': 'Dashboard Catalog',
            'user-settings': 'User Settings',
            'directors-hub': 'Directors Hub - Home',
            'sales': 'Sales - Home',
            'accounts': 'Accounts - Home',
            'admin-hub': 'Admin Hub - Home',
            'it': 'IT - Home',
            'hr': 'HR - Home',
            'marketing': 'Marketing - Home',
            'procurement': 'Procurement - Home',
            'customer-care': 'Customer Care - Home',
            'login': 'Login'
        };

        if (customNames[name]) {
            document.title = customNames[name];
            return '';
        }

        name = name.split('-').map(word => {
            if (word.toLowerCase() === 'nsv') return 'NSV';
            if (word.toLowerCase() === 'roas') return 'ROAS';
            if (word.toLowerCase() === 'bi') return 'BI';
            return word.charAt(0).toUpperCase() + word.slice(1);
        }).join(' ');

        document.title = name;
        return '';
    }
    """,
    Output('dummy-title-output', 'children'),
    Input('url', 'pathname')
)


# ---------------------------------------------------
# Page Routing
# ---------------------------------------------------

@app.callback(

    Output('page-content', 'children'),

    Input('url', 'pathname')

)

def display_page(pathname):

    # ---------------------------------------------------
    # Force Logout On Session Version Change
    # ---------------------------------------------------

    if session.get('session_version') != SESSION_VERSION:

        session.clear()

        return login.layout


    # ---------------------------------------------------
    # Login Check
    # ---------------------------------------------------

    if not session.get('logged_in'):

        return login.layout


    # ---------------------------------------------------
    # Allowed Dashboards
    # ---------------------------------------------------

    allowed_dashboards = session.get(

        'dashboards',

        []

    )

    allowed_modules = session.get(

        'modules',

        []

    )


    # ---------------------------------------------------
    # Logout
    # ---------------------------------------------------

    if pathname == '/logout':

        session.clear()

        return login.layout


    # ---------------------------------------------------
    # Log User Dashboard Access (Fully Automatic)
    # ---------------------------------------------------

    permission = pathname.strip('/')

    perm_check = permission
    if permission == 'sales-countdown-live':
        perm_check = 'sales-countdown'
    elif permission == 'live-customer-counter':
        perm_check = 'live-customer'

    if perm_check in allowed_dashboards:

        db_name = " ".join([w.upper() if w.lower() == 'nsv' else w.capitalize() for w in perm_check.split('-')]) + " Dashboard"

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), db_name)

    elif pathname == '/' or pathname == '':

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), 'Home Page')

    elif pathname == '/inventory':

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), 'Inventory Department')

    elif pathname == '/procurement':

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), 'Procurement Department')

    elif pathname == '/sales':

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), 'Sales Department')

    elif pathname == '/customer-care':

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), 'Customer Care Department')

    elif pathname == '/live-customer':

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), 'Live Customer Counter')


    elif pathname == '/directors-hub':

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), 'Directors Hub Department')

    elif pathname == '/accounts':

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), 'Accounts Department')

    elif pathname == '/hr':

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), 'HR Department')

    elif pathname == '/it':

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), 'IT Department')

    elif pathname == '/marketing':

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), 'Marketing Department')

    elif pathname == '/admin-hub':

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), 'Admin Hub')

    elif pathname == '/dashboard-catalog':

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), 'Dashboard Catalog')

    elif pathname == '/user-settings':

        from backend.services.activity_logger import log_activity

        log_activity(session.get('email'), 'User Settings')






    # ---------------------------------------------------
    # Performance Dashboard
    # ---------------------------------------------------

    if pathname == '/performance':

        if 'performance' not in allowed_dashboards:

            return html.H3("Access Denied")

        return performance_dashboard.layout

    # ---------------------------------------------------
    # Procurement Sales Dashboard (Copy of Performance)
    # ---------------------------------------------------

    elif pathname == '/procurement-sales':

        if 'procurement-sales' not in allowed_dashboards:

            return html.H3("Access Denied")

        return performance_dashboard.layout


    # ---------------------------------------------------
    # Comparison Dashboard
    # ---------------------------------------------------

    elif pathname == '/comparison':

        if 'comparison' not in allowed_dashboards:

            return html.H3("Access Denied")

        return comparison_dash.layout


    # ---------------------------------------------------
    # Aging Stock Dashboard
    # ---------------------------------------------------

    elif pathname == '/aging-stock':

        if 'aging-stock' not in allowed_dashboards:

            return html.H3("Access Denied")

        return aging_stock_dash.layout

    # ---------------------------------------------------
    # Design Performance Dashboard
    # ---------------------------------------------------

    elif pathname == '/design-performance':

        if 'design-performance' not in allowed_dashboards:

            return html.H3("Access Denied")

        return design_performance_dash.layout


    # ---------------------------------------------------
    # Daily Customer Dashboard
    # ---------------------------------------------------

    elif pathname == '/daily-customer':

        if 'daily-customer' not in allowed_dashboards:

            return html.H3("Access Denied")

        return daily_customer_dash.layout


    # ---------------------------------------------------
    # Stock Movement Dashboard
    # ---------------------------------------------------

    elif pathname == '/stock-movement':

        if 'stock-movement' not in allowed_dashboards:

            return html.H3("Access Denied")

        return stock_movement_dash.layout


    # ---------------------------------------------------
    # Basket Analysis Dashboard
    # ---------------------------------------------------

    elif pathname == '/basket-analysis':

        if 'basket-analysis' not in allowed_dashboards:

            return html.H3("Access Denied")

        return basket_analysis_layout

    # ---------------------------------------------------
    # Inventory Landing Page
    # ---------------------------------------------------

    elif pathname == '/inventory':

        if 'inventory' not in allowed_modules:

            return html.H3("Access Denied")

        return inventory_home_layout

    # ---------------------------------------------------
    # Procurement Landing Page
    # ---------------------------------------------------

    elif pathname == '/procurement':

        if 'procurement' not in allowed_modules:

            return html.H3("Access Denied")

        return procurement_home_layout

    # ---------------------------------------------------
    # Sales Landing Page
    # ---------------------------------------------------

    elif pathname == '/sales':

        if 'sales' not in allowed_modules:

            return html.H3("Access Denied")

        return sales_home_layout

    elif pathname == '/customer-care':

        if 'customer-care' not in allowed_modules:

            return html.H3("Access Denied")

        return customer_care_home_layout

    elif pathname == '/directors-hub':

        if 'directors-hub' not in allowed_modules:

            return html.H3("Access Denied")

        return directors_hub_home_layout

    elif pathname == '/accounts':

        if 'accounts' not in allowed_modules:

            return html.H3("Access Denied")

        return accounts_home_layout

    elif pathname == '/hr':

        if 'hr' not in allowed_modules:

            return html.H3("Access Denied")

        return hr_home_layout

    elif pathname == '/it':

        if 'it' not in allowed_modules:

            return html.H3("Access Denied")

        return it_home_layout

    elif pathname == '/marketing':

        if 'marketing' not in allowed_modules:

            return html.H3("Access Denied")

        return marketing_home_layout

    elif pathname == '/admin-hub':

        if 'admin-hub' not in allowed_modules:

            return html.H3("Access Denied")

        return admin_hub_home_layout

    elif pathname == '/dashboard-catalog':

        if 'dashboard-catalog' not in allowed_dashboards and 'admin-hub' not in allowed_modules:

            return html.H3("Access Denied")

        return dashboard_catalog_dash.layout

    elif pathname == '/user-settings':

        if 'user-settings' not in allowed_dashboards and 'admin-hub' not in allowed_modules:

            return html.H3("Access Denied")

        return user_settings_dash.layout




    # ---------------------------------------------------
    # Inventory Optimization Dashboard
    # ---------------------------------------------------

    elif pathname == '/inventory-optimization':

        if 'inventory-optimization' not in allowed_dashboards:

            return html.H3("Access Denied")

        return inventory_optimization_layout

    # ---------------------------------------------------
    # Vendor Analysis Dashboard
    # ---------------------------------------------------

    elif pathname == '/vendor-analysis':

        if 'vendor-analysis' not in allowed_dashboards:

            return html.H3("Access Denied")

        return vendor_analysis_layout

    # ---------------------------------------------------
    # Branch Health Dashboard
    # ---------------------------------------------------

    elif pathname == '/branch-health':

        if 'branch-health' not in allowed_dashboards:

            return html.H3("Access Denied")

        return branch_health_dash.layout
    
    # ---------------------------------------------------
    # Period Comparison Dashboard
    # ---------------------------------------------------

    elif pathname == '/period-comparison':

        if 'period-comparison' not in allowed_dashboards:

            return html.H3("Access Denied")

        return period_comparison_dash.layout
    
    # ---------------------------------------------------
    # Old Gold Dashboard
    # ---------------------------------------------------

    elif pathname == '/old-gold':

        if 'old-gold' not in allowed_dashboards:

            return html.H3("Access Denied")

        return old_gold_dash.layout


    # ---------------------------------------------------
    # Profitability Analysis Dashboard
    # ---------------------------------------------------

    elif pathname == '/profitability-analysis':

        if 'profitability-analysis' not in allowed_dashboards:

            return html.H3("Access Denied")

        return profitability_analysis_Dash.layout

    # ---------------------------------------------------
    # ROAS & Conversion Analytics Dashboard
    # ---------------------------------------------------

    elif pathname == '/roas-conversion-analytics':

        if 'roas-conversion-analytics' not in allowed_dashboards:

            return html.H3("Access Denied")

        return roas_conversion_dash.layout

    # ---------------------------------------------------
    # Company Snapshot Dashboard
    # ---------------------------------------------------

    elif pathname == '/company-snapshot':

        if 'company-snapshot' not in allowed_dashboards:

            return html.H3("Access Denied")

        return company_snapshot_dash.layout

    # ---------------------------------------------------
    # Sales Countdown Dashboard (Unified)
    # ---------------------------------------------------

    elif pathname in ['/sales-countdown', '/sales-countdown-live']:

        if 'sales-countdown' not in allowed_dashboards:

            return html.H3("Access Denied")

        return sales_countdown_dash.layout

    # ---------------------------------------------------
    # Mini NSV Dashboard
    # ---------------------------------------------------

    elif pathname == '/mini-nsv':

        if 'mini-nsv' not in allowed_dashboards:

            return html.H3("Access Denied")

        return mini_nsv_dash.layout


    # ---------------------------------------------------
    # Employee Performance Dashboard
    # ---------------------------------------------------

    elif pathname == '/employee-performance':

        if 'employee-performance' not in allowed_dashboards:

            return html.H3("Access Denied")

        return employee_performance_dash.layout


    # ---------------------------------------------------
    # SME Performance Dashboard
    # ---------------------------------------------------

    elif pathname == '/sme-performance':

        if 'sme-performance' not in allowed_dashboards:

            return html.H3("Access Denied")

        return sme_performance_dash.layout


    # ---------------------------------------------------
    # Dormant Customer Dashboard
    # ---------------------------------------------------

    elif pathname == '/dormant-customer':

        if 'dormant-customer' not in allowed_dashboards:

            return html.H3("Access Denied")

        return dormant_customer_dash.layout


    # ---------------------------------------------------
    # Live Customer Counter Dashboard
    # ---------------------------------------------------

    elif pathname == '/live-customer':

        if 'live-customer' not in allowed_dashboards:

            return html.H3("Access Denied")

        return live_customer_dash.layout

    elif pathname == '/live-customer-counter':

        if 'live-customer' not in allowed_dashboards:

            return html.H3("Access Denied")

        return sales_live_customer_dash.layout



    # ---------------------------------------------------
    # Customer Bucket Dashboard
    # ---------------------------------------------------

    elif pathname == '/customer-bucket':

        if 'customer-bucket' not in allowed_dashboards:

            return html.H3("Access Denied")

        return customer_bucket_dash.layout


    # ---------------------------------------------------
    # Geo Analytics Dashboard
    # ---------------------------------------------------

    elif pathname == '/geo-analytics':

        if 'geo-analytics' not in allowed_dashboards:

            return html.H3("Access Denied")

        return geo_analytics_dash.layout


    # ---------------------------------------------------
    # Execution Tracker
    # ---------------------------------------------------

    elif pathname == '/execution-tracker':

        if 'execution-tracker' not in allowed_modules:

            return html.H3("Access Denied")

        return execution_tracker_dash.layout


    # ---------------------------------------------------
    # Home Page
    # ---------------------------------------------------

    return home.get_layout()


# ---------------------------------------------------
# Login Callback
# ---------------------------------------------------

@app.callback(

    [

        Output('login-message', 'children'),

        Output('url', 'pathname')

    ],

    Input('login-btn', 'n_clicks'),

    [

        State('login-email', 'value'),

        State('login-password', 'value')

    ],

    prevent_initial_call=True

)

def login_user(

    n_clicks,

    email,

    password

):

    user = validate_user(

        email,

        password

    )


    # ---------------------------------------------------
    # Invalid Login
    # ---------------------------------------------------

    if user is None:

        return "Invalid Email or Password", '/'


    # ---------------------------------------------------
    # Session Creation
    # ---------------------------------------------------

    session.permanent = True

    session['logged_in'] = True

    session['email'] = user['email']

    session['dashboards'] = user['dashboards']

    session['locations'] = user['locations']

    session['modules'] = user.get('modules', [])

    session['session_version'] = SESSION_VERSION


    return "", "/"


# ---------------------------------------------------
# Run App
# ---------------------------------------------------

if __name__ == '__main__':

    app.run(

        host='0.0.0.0',

        port=7860,

        debug=False

    )