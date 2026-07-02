from flask import session


# ---------------------------------------------------
# Allowed Locations
# ---------------------------------------------------

def get_allowed_locations():
    try:
        return session.get(
            'locations',
            []
        )
    except RuntimeError:
        # Fallback when running outside active Flask request context (e.g. CLI tests)
        return ['ALL']