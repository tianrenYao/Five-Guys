from functools import wraps
from flask import session, redirect, url_for, flash, jsonify, request


def login_required(f):
    """Decorator: redirect to login if user is not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized', 'message': 'Please login first'}), 401
            flash('Please login first.', 'warning')
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Decorator: restrict access to specific roles (admin, business, staff)."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Unauthorized'}), 401
                return redirect(url_for('auth.login_page'))
            if session.get('role') not in roles:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Forbidden', 'message': 'Insufficient permissions'}), 403
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard.dashboard_page'))
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_current_user():
    """Get current logged-in user info from session."""
    return {
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role'),
        'company_id': session.get('company_id'),
        'display_name': session.get('display_name')
    }
