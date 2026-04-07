from functools import wraps
from flask import session, redirect, url_for, flash, jsonify, request
from backend.utils.db import query_db


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
    """Decorator: restrict access to specific roles.
    Valid roles: admin, hq_manager, region_manager, store_staff
    """
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
        'user_id':    session.get('user_id'),
        'username':   session.get('username'),
        'role':       session.get('role'),
        'company_id': session.get('company_id'),
        'region_id':  session.get('region_id'),
        'store_id':   session.get('store_id'),
        'display_name': session.get('display_name')
    }


def get_accessible_store_ids():
    """Return the list of store IDs the current user is allowed to access.

    Role mapping:
      admin / hq_manager  -> all stores in the company
      region_manager      -> all stores in their region
      store_staff         -> only their own store
    Returns an empty list if the user has no company context.
    """
    role       = session.get('role')
    company_id = session.get('company_id')
    region_id  = session.get('region_id')
    store_id   = session.get('store_id')

    if not company_id:
        return []

    if role in ('admin', 'hq_manager'):
        rows = query_db(
            'SELECT id FROM store WHERE company_id = %s AND is_active = 1',
            (company_id,)
        )
        return [r['id'] for r in rows]

    if role == 'region_manager':
        if not region_id:
            return []
        rows = query_db(
            'SELECT id FROM store WHERE region_id = %s AND is_active = 1',
            (region_id,)
        )
        return [r['id'] for r in rows]

    if role == 'store_staff':
        return [store_id] if store_id else []

    return []
