from flask import Blueprint, request, session, render_template, jsonify
from backend.utils.db import query_db
from backend.utils.auth_helper import login_required, role_required

audit_bp = Blueprint('audit', __name__)


@audit_bp.route('/admin/audit-log')
@login_required
@role_required('admin', 'hq_manager')
def audit_log_page():
    return render_template('audit_log.html')


@audit_bp.route('/api/audit/logs')
@login_required
@role_required('admin', 'hq_manager')
def audit_logs_api():
    """Return audit log entries with optional filters."""
    company_id  = session.get('company_id')
    role        = session.get('role')

    action      = request.args.get('action', '')
    target_type = request.args.get('target_type', '')
    date_from   = request.args.get('date_from', '')
    date_to     = request.args.get('date_to', '')
    limit       = min(int(request.args.get('limit', 200)), 500)

    if role == 'admin':
        # Platform admin sees everything
        sql = (
            'SELECT al.id, al.action, al.target_type, al.target_id, '
            'al.detail, al.ip_address, al.created_at, '
            'u.username, u.display_name, u.role AS user_role '
            'FROM audit_log al '
            'LEFT JOIN `user` u ON u.id = al.user_id '
            'WHERE 1=1 '
        )
        params = []
    else:
        # hq_manager sees only their company's users
        sql = (
            'SELECT al.id, al.action, al.target_type, al.target_id, '
            'al.detail, al.ip_address, al.created_at, '
            'u.username, u.display_name, u.role AS user_role '
            'FROM audit_log al '
            'LEFT JOIN `user` u ON u.id = al.user_id '
            'WHERE (u.company_id = %s OR u.id IS NULL) '
        )
        params = [company_id]

    if action:
        sql += 'AND al.action = %s '
        params.append(action)
    if target_type:
        sql += 'AND al.target_type = %s '
        params.append(target_type)
    if date_from:
        sql += 'AND DATE(al.created_at) >= %s '
        params.append(date_from)
    if date_to:
        sql += 'AND DATE(al.created_at) <= %s '
        params.append(date_to)

    sql += f'ORDER BY al.created_at DESC LIMIT {limit}'

    rows = query_db(sql, params)
    for r in rows:
        r['created_at'] = str(r['created_at']) if r['created_at'] else None

    return jsonify({'success': True, 'data': rows, 'total': len(rows)})


@audit_bp.route('/api/audit/stats')
@login_required
@role_required('admin', 'hq_manager')
def audit_stats_api():
    """Return summary stats: action counts for the last 7 days."""
    company_id = session.get('company_id')
    role       = session.get('role')

    if role == 'admin':
        rows = query_db(
            'SELECT al.action, COUNT(*) AS cnt '
            'FROM audit_log al '
            'WHERE al.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) '
            'GROUP BY al.action'
        )
    else:
        rows = query_db(
            'SELECT al.action, COUNT(*) AS cnt '
            'FROM audit_log al '
            'LEFT JOIN `user` u ON u.id = al.user_id '
            'WHERE (u.company_id = %s OR u.id IS NULL) '
            'AND al.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) '
            'GROUP BY al.action',
            (company_id,)
        )

    stats = {r['action']: r['cnt'] for r in rows}
    return jsonify({'success': True, 'data': stats})
