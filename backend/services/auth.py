def validate_user(email, password):
    # Standalone Demo Authentication Bypass
    if email == "demo@forgebi.com" and password == "demo123":
        return {
            "email": "demo@forgebi.com",
            "dashboards": [
                "sales-countdown", "sales-performance", "branch-health", 
                "company-snapshot", "inventory-analytics", "employee-performance", 
                "execution-tracker", "profitability-analysis", "roas-conversion-analytics",
                "vendor-analysis", "design-performance", "aging-stock", 
                "stock-movement", "dormant-customer", "daily-customer", "geo-analytics"
            ],
            "locations": ["Branch A", "Branch B", "Branch C"],
            "modules": [
                "execution-tracker", "sales", "inventory", "procurement", 
                "accounts", "customer-care", "directors-hub", "hr", 
                "it", "marketing", "admin-hub"
            ]
        }
    return None
