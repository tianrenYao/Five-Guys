from flask import Blueprint, request, session, render_template, jsonify
from werkzeug.security import generate_password_hash
from backend.utils.db import query_db, execute_db, insert_db
from backend.utils.auth_helper import login_required, role_required

admin_bp = Blueprint('admin', __name__)


# ──────────────────────────────────────────────
# Page
# ──────────────────────────────────────────────

@admin_bp.route('/admin/users')
@login_required
@role_required('admin', 'hq_manager')
def admin_users_page():
    return render_template('admin_users.html')


# ──────────────────────────────────────────────
# API: list users
# ──────────────────────────────────────────────

@admin_bp.route('/api/admin/users')
@login_required
@role_required('admin', 'hq_manager')
def list_users():
    company_id = session.get('company_id')
    role       = session.get('role')

    if role == 'admin':
        rows = query_db(
            'SELECT u.id, u.username, u.display_name, u.email, u.role, '
            'u.is_active, u.last_login, u.created_at, u.company_id, '
            'u.region_id, u.store_id, '
            'c.name AS company_name, '
            'r.name AS region_name, '
            's.name AS store_name '
            'FROM `user` u '
            'LEFT JOIN company c ON c.id = u.company_id '
            'LEFT JOIN region  r ON r.id = u.region_id '
            'LEFT JOIN store   s ON s.id = u.store_id '
            'ORDER BY u.company_id, u.role, u.id'
        )
    else:
        rows = query_db(
            'SELECT u.id, u.username, u.display_name, u.email, u.role, '
            'u.is_active, u.last_login, u.created_at, u.company_id, '
            'u.region_id, u.store_id, '
            'c.name AS company_name, '
            'r.name AS region_name, '
            's.name AS store_name '
            'FROM `user` u '
            'LEFT JOIN company c ON c.id = u.company_id '
            'LEFT JOIN region  r ON r.id = u.region_id '
            'LEFT JOIN store   s ON s.id = u.store_id '
            'WHERE u.company_id = %s '
            'ORDER BY u.role, u.id',
            (company_id,)
        )

    for r in rows:
        r['last_login']  = str(r['last_login'])  if r['last_login']  else None
        r['created_at']  = str(r['created_at'])  if r['created_at']  else None

    return jsonify({'success': True, 'data': rows})


# ──────────────────────────────────────────────
# API: get regions & stores for dropdowns
# ──────────────────────────────────────────────

@admin_bp.route('/api/admin/regions-stores')
@login_required
@role_required('admin', 'hq_manager')
def regions_stores():
    company_id = session.get('company_id')
    regions = query_db(
        'SELECT id, name FROM region WHERE company_id = %s ORDER BY name',
        (company_id,)
    )
    stores = query_db(
        'SELECT id, name, region_id FROM store WHERE company_id = %s ORDER BY name',
        (company_id,)
    )
    return jsonify({'success': True, 'regions': regions, 'stores': stores})


# ──────────────────────────────────────────────
# API: create user
# ──────────────────────────────────────────────

@admin_bp.route('/api/admin/users', methods=['POST'])
@login_required
@role_required('admin', 'hq_manager')
def create_user():
    data = request.get_json()
    company_id   = session.get('company_id')
    username     = (data.get('username') or '').strip()
    password     = data.get('password') or ''
    display_name = (data.get('display_name') or '').strip()
    email        = (data.get('email') or '').strip()
    role         = data.get('role', 'store_staff')
    region_id    = data.get('region_id') or None
    store_id     = data.get('store_id')  or None

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
    if role not in ('admin', 'hq_manager', 'region_manager', 'store_staff'):
        return jsonify({'success': False, 'message': 'Invalid role'}), 400

    existing = query_db('SELECT id FROM `user` WHERE username = %s', (username,), one=True)
    if existing:
        return jsonify({'success': False, 'message': f'Username "{username}" is already taken'}), 409

    pw_hash = generate_password_hash(password)
    uid = insert_db(
        'INSERT INTO `user` (company_id, region_id, store_id, username, password, display_name, email, role) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
        (company_id, region_id, store_id, username, pw_hash, display_name or None, email or None, role)
    )

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'CREATE', 'user', uid,
         f'Created user: {username} ({role})', request.remote_addr)
    )

    return jsonify({'success': True, 'message': f'User "{username}" created successfully', 'id': uid}), 201


# ──────────────────────────────────────────────
# API: update user
# ──────────────────────────────────────────────

@admin_bp.route('/api/admin/users/<int:uid>', methods=['PUT'])
@login_required
@role_required('admin', 'hq_manager')
def update_user(uid):
    data         = request.get_json()
    company_id   = session.get('company_id')
    role_session = session.get('role')

    target = query_db('SELECT id, company_id, username FROM `user` WHERE id = %s', (uid,), one=True)
    if not target:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    if role_session != 'admin' and target['company_id'] != company_id:
        return jsonify({'success': False, 'message': 'Forbidden'}), 403

    display_name = (data.get('display_name') or '').strip() or None
    email        = (data.get('email') or '').strip() or None
    role_new     = data.get('role', 'store_staff')
    region_id    = data.get('region_id') or None
    store_id     = data.get('store_id')  or None
    is_active    = int(data.get('is_active', 1))

    if role_new not in ('admin', 'hq_manager', 'region_manager', 'store_staff'):
        return jsonify({'success': False, 'message': 'Invalid role'}), 400

    execute_db(
        'UPDATE `user` SET display_name=%s, email=%s, role=%s, '
        'region_id=%s, store_id=%s, is_active=%s WHERE id=%s',
        (display_name, email, role_new, region_id, store_id, is_active, uid)
    )

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'UPDATE', 'user', uid,
         f'Updated user: {target["username"]} → role={role_new}, active={is_active}',
         request.remote_addr)
    )

    return jsonify({'success': True, 'message': 'User updated successfully'})


# ──────────────────────────────────────────────
# API: reset password
# ──────────────────────────────────────────────

@admin_bp.route('/api/admin/users/<int:uid>/reset-password', methods=['POST'])
@login_required
@role_required('admin', 'hq_manager')
def reset_password(uid):
    data         = request.get_json()
    company_id   = session.get('company_id')
    role_session = session.get('role')
    new_password = data.get('password', '')

    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400

    target = query_db('SELECT id, company_id, username FROM `user` WHERE id = %s', (uid,), one=True)
    if not target:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    if role_session != 'admin' and target['company_id'] != company_id:
        return jsonify({'success': False, 'message': 'Forbidden'}), 403

    pw_hash = generate_password_hash(new_password)
    execute_db('UPDATE `user` SET password = %s WHERE id = %s', (pw_hash, uid))

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'UPDATE', 'user', uid,
         f'Password reset for user: {target["username"]}', request.remote_addr)
    )

    return jsonify({'success': True, 'message': 'Password reset successfully'})


# ──────────────────────────────────────────────
# API: delete user
# ──────────────────────────────────────────────

@admin_bp.route('/api/admin/users/<int:uid>', methods=['DELETE'])
@login_required
@role_required('admin', 'hq_manager')
def delete_user(uid):
    company_id   = session.get('company_id')
    role_session = session.get('role')

    if uid == session['user_id']:
        return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 400

    target = query_db('SELECT id, company_id, username FROM `user` WHERE id = %s', (uid,), one=True)
    if not target:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    if role_session != 'admin' and target['company_id'] != company_id:
        return jsonify({'success': False, 'message': 'Forbidden'}), 403

    execute_db('DELETE FROM `user` WHERE id = %s', (uid,))

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'DELETE', 'user', uid,
         f'Deleted user: {target["username"]}', request.remote_addr)
    )

    return jsonify({'success': True, 'message': f'User "{target["username"]}" deleted'})
