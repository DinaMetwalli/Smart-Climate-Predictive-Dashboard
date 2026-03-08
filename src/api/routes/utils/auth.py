from functools import wraps
from flask import session, jsonify

def authorize(f):
    """Decorator to require login for a route by authorizing them."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_id():
    """Helper to get current user ID from stored session."""
    return session.get('user_id')