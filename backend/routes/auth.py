import os

from flask import Blueprint, request, session, redirect, url_for, render_template, flash, jsonify, send_file
from werkzeug.security import check_password_hash
from backend.utils.db import query_db, execute_db
from backend.utils.auth_helper import login_required

auth_bp = Blueprint('auth', __name__)
LUCKIN_LOGO_PATH = (
    '/Users/lance-lee/.cursor/projects/Users-lance-lee-Desktop-Five-Guys/assets/'
    'cdnlogo.com_luckin-coffee-b62b131f-6022-4981-9c9d-e793347ac0da.png'
)
LUCKIN_HERO_BG_PATH = (
    '/Users/lance-lee/.cursor/projects/Users-lance-lee-Desktop-Five-Guys/assets/'
    'image-8b5a0b9a-01c5-46a4-ac69-bd5df7dc876b.png'
)
COMPANY_LOGO_PATH = (
    '/Users/lance-lee/.cursor/projects/Users-lance-lee-Desktop-Five-Guys/assets/'
    '__logo-c47f451e-fffa-4b48-ad36-0e914fd133e1.png'
)


@auth_bp.route('/welcome', methods=['GET'])
def welcome_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard_page'))
    return render_template('welcome.html')


@auth_bp.route('/brand/luckin-logo', methods=['GET'])
def luckin_logo():
    if not os.path.exists(LUCKIN_LOGO_PATH):
        return jsonify({'success': False, 'message': 'Logo not found'}), 404
    return send_file(LUCKIN_LOGO_PATH, mimetype='image/png')


@auth_bp.route('/brand/luckin-hero', methods=['GET'])
def luckin_hero():
    if not os.path.exists(LUCKIN_HERO_BG_PATH):
        return jsonify({'success': False, 'message': 'Hero image not found'}), 404
    return send_file(LUCKIN_HERO_BG_PATH, mimetype='image/png')


@auth_bp.route('/brand/company-logo', methods=['GET'])
def company_logo():
    if not os.path.exists(COMPANY_LOGO_PATH):
        return jsonify({'success': False, 'message': 'Company logo not found'}), 404
    return send_file(COMPANY_LOGO_PATH, mimetype='image/png')


@auth_bp.route('/login', methods=['GET'])
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard_page'))
    return render_template('login.html')


@auth_bp.route('/api/login', methods=['POST'])
def login_api():
    data = request.get_json() if request.is_json else request.form
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'}), 400

    user = query_db(
        'SELECT id, company_id, region_id, store_id, username, password, display_name, role, is_active '
        'FROM `user` WHERE username = %s',
        (username,), one=True
    )

    if not user:
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

    if not user['is_active']:
        return jsonify({'success': False, 'message': 'Account is disabled'}), 403

    if not check_password_hash(user['password'], password):
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

    # Set session
    session['user_id']    = user['id']
    session['username']   = user['username']
    session['display_name'] = user['display_name'] or user['username']
    session['role']       = user['role']
    session['company_id'] = user['company_id']
    session['region_id']  = user['region_id']
    session['store_id']   = user['store_id']

    # Update last_login
    execute_db('UPDATE `user` SET last_login = NOW() WHERE id = %s', (user['id'],))

    # Log the login action
    execute_db(
        'INSERT INTO audit_log (user_id, action, detail, ip_address) VALUES (%s, %s, %s, %s)',
        (user['id'], 'LOGIN', f'User {username} logged in', request.remote_addr)
    )

    return jsonify({
        'success': True,
        'message': 'Login successful',
        'user': {
            'id': user['id'],
            'username': user['username'],
            'display_name': user['display_name'],
            'role': user['role']
        }
    })


@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        execute_db(
            'INSERT INTO audit_log (user_id, action, detail, ip_address) VALUES (%s, %s, %s, %s)',
            (user_id, 'LOGOUT', 'User logged out', request.remote_addr)
        )
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login_page'))


@auth_bp.route('/api/me')
@login_required
def current_user():
    user = query_db(
        'SELECT u.id, u.username, u.display_name, u.email, u.role, '
        'u.region_id, u.store_id, '
        'c.name AS company_name, '
        'r.name AS region_name, '
        's.name AS store_name '
        'FROM `user` u '
        'LEFT JOIN company c ON c.id = u.company_id '
        'LEFT JOIN region r  ON r.id = u.region_id '
        'LEFT JOIN store s   ON s.id = u.store_id '
        'WHERE u.id = %s',
        (session['user_id'],), one=True
    )
    return jsonify({'success': True, 'user': user})
