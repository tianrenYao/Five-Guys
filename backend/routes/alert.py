from flask import Blueprint, request, session, jsonify, render_template
from backend.utils.db import query_db, execute_db, insert_db
from backend.utils.auth_helper import login_required, role_required

alert_bp = Blueprint('alert', __name__)


@alert_bp.route('/alerts')
@login_required
@role_required('hq_manager', 'region_manager', 'admin')
def alerts_page():
    return render_template('alerts.html')

# ──────────────────────────────────────────────
# 阈值配置（仅 hq_manager / admin 可写）
# ──────────────────────────────────────────────

@alert_bp.route('/api/alert/thresholds')
@login_required
@role_required('hq_manager', 'admin')
def threshold_list():
    """List all alert thresholds for the current company."""
    rows = query_db(
        'SELECT t.id, t.metric_type, t.scope, t.scope_id, '
        't.threshold_value, t.comparison, t.is_active, t.created_at, '
        'u.display_name AS created_by_name '
        'FROM alert_threshold t '
        'LEFT JOIN `user` u ON u.id = t.created_by '
        'WHERE t.company_id = %s ORDER BY t.metric_type, t.scope',
        (session['company_id'],)
    )
    for r in rows:
        r['threshold_value'] = float(r['threshold_value'])
        r['created_at'] = str(r['created_at']) if r['created_at'] else None
    return jsonify({'success': True, 'data': rows})


@alert_bp.route('/api/alert/thresholds', methods=['POST'])
@login_required
@role_required('hq_manager', 'admin')
def threshold_create():
    """Create a new alert threshold."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'}), 400

    metric_type     = data.get('metric_type')
    scope           = data.get('scope', 'company')
    scope_id        = data.get('scope_id')
    threshold_value = data.get('threshold_value')
    comparison      = data.get('comparison', 'lt')

    valid_metrics = ('waste_recycling_rate', 'carbon_mom_growth', 'waste_weight_daily')
    if metric_type not in valid_metrics:
        return jsonify({'success': False, 'message': f'metric_type must be one of {valid_metrics}'}), 400
    if scope not in ('company', 'region', 'store'):
        return jsonify({'success': False, 'message': 'scope must be company / region / store'}), 400
    if comparison not in ('lt', 'gt'):
        return jsonify({'success': False, 'message': 'comparison must be lt or gt'}), 400
    if threshold_value is None:
        return jsonify({'success': False, 'message': 'threshold_value is required'}), 400

    new_id = insert_db(
        'INSERT INTO alert_threshold '
        '(company_id, metric_type, scope, scope_id, threshold_value, comparison, created_by) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s)',
        (session['company_id'], metric_type, scope, scope_id,
         float(threshold_value), comparison, session['user_id'])
    )
    return jsonify({'success': True, 'message': 'Threshold created', 'data': {'id': new_id}}), 201


@alert_bp.route('/api/alert/thresholds/<int:threshold_id>', methods=['PUT'])
@login_required
@role_required('hq_manager', 'admin')
def threshold_update(threshold_id):
    """Update an existing threshold."""
    row = query_db(
        'SELECT id FROM alert_threshold WHERE id = %s AND company_id = %s',
        (threshold_id, session['company_id']), one=True
    )
    if not row:
        return jsonify({'success': False, 'message': 'Threshold not found'}), 404

    data = request.get_json() or {}
    fields, params = [], []
    for col in ('threshold_value', 'comparison', 'is_active', 'scope', 'scope_id'):
        if col in data:
            fields.append(f'{col} = %s')
            params.append(data[col])

    if fields:
        params.append(threshold_id)
        execute_db(f'UPDATE alert_threshold SET {", ".join(fields)} WHERE id = %s', params)

    return jsonify({'success': True, 'message': 'Threshold updated'})


@alert_bp.route('/api/alert/thresholds/<int:threshold_id>', methods=['DELETE'])
@login_required
@role_required('hq_manager', 'admin')
def threshold_delete(threshold_id):
    """Delete a threshold."""
    row = query_db(
        'SELECT id FROM alert_threshold WHERE id = %s AND company_id = %s',
        (threshold_id, session['company_id']), one=True
    )
    if not row:
        return jsonify({'success': False, 'message': 'Threshold not found'}), 404

    execute_db('DELETE FROM alert_threshold WHERE id = %s', (threshold_id,))
    return jsonify({'success': True, 'message': 'Threshold deleted'})


# ──────────────────────────────────────────────
# 预警日志（hq_manager 和 region_manager 可见）
# ──────────────────────────────────────────────

@alert_bp.route('/api/alert/logs')
@login_required
@role_required('hq_manager', 'region_manager', 'admin')
def alert_logs():
    """List alert logs, filtered by the user's accessible region/stores."""
    company_id = session['company_id']
    role       = session.get('role')
    region_id  = session.get('region_id')

    if role in ('hq_manager', 'admin'):
        rows = query_db(
            'SELECT al.id, al.store_id, al.metric_type, al.current_value, '
            'al.threshold_value, al.triggered_at, al.is_read, al.read_at, '
            's.name AS store_name, r.name AS region_name '
            'FROM alert_log al '
            'LEFT JOIN store s ON s.id = al.store_id '
            'LEFT JOIN region r ON r.id = s.region_id '
            'WHERE al.company_id = %s ORDER BY al.triggered_at DESC LIMIT 100',
            (company_id,)
        )
    else:
        rows = query_db(
            'SELECT al.id, al.store_id, al.metric_type, al.current_value, '
            'al.threshold_value, al.triggered_at, al.is_read, al.read_at, '
            's.name AS store_name, r.name AS region_name '
            'FROM alert_log al '
            'LEFT JOIN store s ON s.id = al.store_id '
            'LEFT JOIN region r ON r.id = s.region_id '
            'WHERE al.company_id = %s AND s.region_id = %s '
            'ORDER BY al.triggered_at DESC LIMIT 100',
            (company_id, region_id)
        )

    for r in rows:
        r['current_value']   = float(r['current_value'])
        r['threshold_value'] = float(r['threshold_value'])
        r['triggered_at']    = str(r['triggered_at']) if r['triggered_at'] else None
        r['read_at']         = str(r['read_at'])       if r['read_at']     else None
    return jsonify({'success': True, 'data': rows})


@alert_bp.route('/api/alert/unread-count')
@login_required
def unread_count():
    """Return unread alert count for the current user (used by nav badge)."""
    company_id = session['company_id']
    role       = session.get('role')
    region_id  = session.get('region_id')

    if role == 'store_staff':
        return jsonify({'success': True, 'data': {'count': 0}})

    if role in ('hq_manager', 'admin'):
        row = query_db(
            'SELECT COUNT(*) AS cnt FROM alert_log '
            'WHERE company_id = %s AND is_read = 0',
            (company_id,), one=True
        )
    else:
        row = query_db(
            'SELECT COUNT(*) AS cnt FROM alert_log al '
            'LEFT JOIN store s ON s.id = al.store_id '
            'WHERE al.company_id = %s AND s.region_id = %s AND al.is_read = 0',
            (company_id, region_id), one=True
        )

    return jsonify({'success': True, 'data': {'count': row['cnt'] if row else 0}})


@alert_bp.route('/api/alert/logs/<int:log_id>/read', methods=['POST'])
@login_required
@role_required('hq_manager', 'region_manager', 'admin')
def mark_read(log_id):
    """Mark an alert log entry as read."""
    execute_db(
        'UPDATE alert_log SET is_read = 1, read_by = %s, read_at = NOW() '
        'WHERE id = %s AND company_id = %s',
        (session['user_id'], log_id, session['company_id'])
    )
    return jsonify({'success': True, 'message': 'Marked as read'})


@alert_bp.route('/api/alert/logs/read-all', methods=['POST'])
@login_required
@role_required('hq_manager', 'admin')
def mark_all_read():
    """Mark all unread alert logs as read (hq_manager only)."""
    execute_db(
        'UPDATE alert_log SET is_read = 1, read_by = %s, read_at = NOW() '
        'WHERE company_id = %s AND is_read = 0',
        (session['user_id'], session['company_id'])
    )
    return jsonify({'success': True, 'message': 'All alerts marked as read'})
