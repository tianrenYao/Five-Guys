from flask import Blueprint, request, session, render_template, jsonify
from backend.utils.db import query_db, execute_db, insert_db
from backend.utils.auth_helper import login_required, get_accessible_store_ids
from backend.utils.alert_checker import check_alerts_for_store

waste_bp = Blueprint('waste', __name__)


@waste_bp.route('/waste')
@login_required
def waste_page():
    return render_template('waste.html')


@waste_bp.route('/api/waste/categories')
@login_required
def get_categories():
    """Get all waste categories."""
    rows = query_db('SELECT id, name, is_recyclable FROM waste_category ORDER BY id')
    return jsonify({'success': True, 'data': rows})


@waste_bp.route('/api/waste/list')
@login_required
def waste_list():
    """Get waste records for accessible stores, with optional date/store filter."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': []})

    date_from    = request.args.get('date_from', '')
    date_to      = request.args.get('date_to', '')
    filter_store = request.args.get('store_id', '')

    placeholders = ','.join(['%s'] * len(store_ids))
    sql = (
        'SELECT wr.id, wc.name AS category_name, wc.is_recyclable, '
        'wr.weight_kg, wr.recycled_kg, wr.source_type, '
        'wr.disposal_method, wr.disposal_unit, '
        'wr.record_date, wr.note, wr.created_at, wr.attachment_url, '
        'u.display_name AS recorded_by, '
        's.name AS store_name '
        'FROM waste_record wr '
        'JOIN waste_category wc ON wc.id = wr.category_id '
        'LEFT JOIN `user` u ON u.id = wr.user_id '
        'LEFT JOIN store s ON s.id = wr.store_id '
        f'WHERE wr.store_id IN ({placeholders}) '
    )
    params = list(store_ids)

    if filter_store and int(filter_store) in store_ids:
        sql += 'AND wr.store_id = %s '
        params.append(int(filter_store))
    if date_from:
        sql += 'AND wr.record_date >= %s '
        params.append(date_from)
    if date_to:
        sql += 'AND wr.record_date <= %s '
        params.append(date_to)

    sql += 'ORDER BY wr.record_date DESC, wr.id DESC'
    rows = query_db(sql, params)

    for r in rows:
        r['record_date'] = str(r['record_date']) if r['record_date'] else None
        r['created_at'] = str(r['created_at']) if r['created_at'] else None

    return jsonify({'success': True, 'data': rows})


@waste_bp.route('/api/waste/add', methods=['POST'])
@login_required
def waste_add():
    """Add a new waste record."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'}), 400

    category_id     = data.get('category_id')
    weight_kg       = data.get('weight_kg')
    record_date     = data.get('record_date')
    note            = data.get('note', '')
    source_type     = data.get('source_type', 'other')
    recycled_kg     = data.get('recycled_kg', 0)
    disposal_method = data.get('disposal_method')
    disposal_unit   = data.get('disposal_unit', '')

    store_ids = get_accessible_store_ids()
    role = session.get('role')
    if role == 'store_staff':
        store_id = session.get('store_id')
    else:
        store_id = data.get('store_id')

    if not store_id:
        return jsonify({'success': False, 'message': 'store_id is required'}), 400
    if store_id not in store_ids:
        return jsonify({'success': False, 'message': 'Access to this store is not permitted'}), 403

    if not all([category_id, weight_kg, record_date]):
        return jsonify({'success': False, 'message': 'category_id, weight_kg, and record_date are required'}), 400

    try:
        weight_kg = float(weight_kg)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'weight_kg must be a number'}), 400

    if weight_kg <= 0:
        return jsonify({'success': False, 'message': 'weight_kg must be positive'}), 400

    # Verify category exists
    cat = query_db('SELECT id FROM waste_category WHERE id = %s', (category_id,), one=True)
    if not cat:
        return jsonify({'success': False, 'message': 'Invalid waste category'}), 400

    try:
        recycled_kg = float(recycled_kg)
        if recycled_kg < 0 or recycled_kg > float(weight_kg):
            recycled_kg = 0
    except (ValueError, TypeError):
        recycled_kg = 0

    record_id = insert_db(
        'INSERT INTO waste_record '
        '(company_id, store_id, user_id, category_id, source_type, weight_kg, recycled_kg, '
        'disposal_method, disposal_unit, record_date, note) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (session['company_id'], store_id, session['user_id'], category_id,
         source_type, weight_kg, recycled_kg, disposal_method, disposal_unit,
         record_date, note)
    )

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'CREATE', 'waste_record', record_id,
         f'Added waste record: {weight_kg} kg', request.remote_addr)
    )

    check_alerts_for_store(session['company_id'], store_id)

    return jsonify({
        'success': True,
        'message': 'Waste record added successfully',
        'data': {'id': record_id}
    }), 201


@waste_bp.route('/api/waste/delete/<int:record_id>', methods=['DELETE'])
@login_required
def waste_delete(record_id):
    """Delete a waste record."""
    store_ids = get_accessible_store_ids()
    placeholders = ','.join(['%s'] * len(store_ids)) if store_ids else '0'
    record = query_db(
        f'SELECT id FROM waste_record WHERE id = %s AND store_id IN ({placeholders})',
        [record_id] + list(store_ids), one=True
    )
    if not record:
        return jsonify({'success': False, 'message': 'Record not found'}), 404

    execute_db('DELETE FROM waste_record WHERE id = %s', (record_id,))

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'DELETE', 'waste_record', record_id,
         f'Deleted waste record #{record_id}', request.remote_addr)
    )

    return jsonify({'success': True, 'message': 'Record deleted successfully'})


@waste_bp.route('/api/waste/stats')
@login_required
def waste_stats():
    """Get waste statistics aggregated across accessible stores."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': []})

    placeholders = ','.join(['%s'] * len(store_ids))
    rows = query_db(
        'SELECT year, month, '
        'SUM(total_weight_kg) AS total_weight_kg, '
        'SUM(total_recycled_kg) AS total_recycled_kg, '
        'ROUND(SUM(total_recycled_kg)/NULLIF(SUM(total_weight_kg),0)*100,2) AS recovery_rate_pct '
        f'FROM v_waste_monthly_summary '
        f'WHERE store_id IN ({placeholders}) AND year = YEAR(CURDATE()) '
        'GROUP BY year, month ORDER BY month',
        list(store_ids)
    )
    for r in rows:
        r['total_weight_kg']   = float(r['total_weight_kg'] or 0)
        r['total_recycled_kg'] = float(r['total_recycled_kg'] or 0)
        r['recovery_rate_pct'] = float(r['recovery_rate_pct'] or 0)
    return jsonify({'success': True, 'data': rows})
