from flask import Blueprint, request, session, render_template, jsonify
from backend.utils.db import query_db, execute_db, insert_db
from backend.utils.auth_helper import login_required

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
    """Get waste records for the current company."""
    company_id = session['company_id']
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    sql = (
        'SELECT wr.id, wc.name AS category_name, wc.is_recyclable, '
        'wr.weight_kg, wr.record_date, wr.note, wr.created_at, '
        'u.display_name AS recorded_by '
        'FROM waste_record wr '
        'JOIN waste_category wc ON wc.id = wr.category_id '
        'LEFT JOIN `user` u ON u.id = wr.user_id '
        'WHERE wr.company_id = %s '
    )
    params = [company_id]

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

    category_id = data.get('category_id')
    weight_kg = data.get('weight_kg')
    record_date = data.get('record_date')
    note = data.get('note', '')

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

    record_id = insert_db(
        'INSERT INTO waste_record (company_id, user_id, category_id, weight_kg, record_date, note) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['company_id'], session['user_id'], category_id, weight_kg, record_date, note)
    )

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'CREATE', 'waste_record', record_id,
         f'Added waste record: {weight_kg} kg', request.remote_addr)
    )

    return jsonify({
        'success': True,
        'message': 'Waste record added successfully',
        'data': {'id': record_id}
    }), 201


@waste_bp.route('/api/waste/delete/<int:record_id>', methods=['DELETE'])
@login_required
def waste_delete(record_id):
    """Delete a waste record."""
    record = query_db(
        'SELECT id FROM waste_record WHERE id = %s AND company_id = %s',
        (record_id, session['company_id']), one=True
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
    """Get waste statistics: total, recyclable, recovery rate."""
    company_id = session['company_id']
    rows = query_db(
        'SELECT year, month, total_weight_kg, recyclable_kg, recovery_rate_pct '
        'FROM v_waste_monthly_summary '
        'WHERE company_id = %s AND year = YEAR(CURDATE()) '
        'ORDER BY month',
        (company_id,)
    )
    for r in rows:
        r['total_weight_kg'] = float(r['total_weight_kg'])
        r['recyclable_kg'] = float(r['recyclable_kg'])
        r['recovery_rate_pct'] = float(r['recovery_rate_pct']) if r['recovery_rate_pct'] else 0
    return jsonify({'success': True, 'data': rows})
