from flask import Blueprint, request, session, render_template, jsonify
from backend.utils.db import query_db, execute_db, insert_db
from backend.utils.auth_helper import login_required

carbon_bp = Blueprint('carbon', __name__)


@carbon_bp.route('/carbon')
@login_required
def carbon_page():
    return render_template('carbon.html')


@carbon_bp.route('/api/carbon/factors')
@login_required
def get_factors():
    """Get all available emission factors."""
    rows = query_db(
        'SELECT id, category, sub_type, factor, unit, source, valid_year '
        'FROM emission_factor ORDER BY category, sub_type'
    )
    return jsonify({'success': True, 'data': rows})


@carbon_bp.route('/api/carbon/list')
@login_required
def carbon_list():
    """Get carbon records for the current company, with optional date filter."""
    company_id = session['company_id']
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    sql = (
        'SELECT cr.id, cr.category, cr.activity_value, cr.total_carbon, '
        'cr.record_date, cr.note, cr.created_at, '
        'ef.sub_type, ef.unit, ef.factor, '
        'u.display_name AS recorded_by '
        'FROM carbon_record cr '
        'LEFT JOIN emission_factor ef ON ef.id = cr.factor_id '
        'LEFT JOIN `user` u ON u.id = cr.user_id '
        'WHERE cr.company_id = %s '
    )
    params = [company_id]

    if date_from:
        sql += 'AND cr.record_date >= %s '
        params.append(date_from)
    if date_to:
        sql += 'AND cr.record_date <= %s '
        params.append(date_to)

    sql += 'ORDER BY cr.record_date DESC, cr.id DESC'
    rows = query_db(sql, params)

    # Convert date/datetime to string for JSON serialization
    for r in rows:
        r['record_date'] = str(r['record_date']) if r['record_date'] else None
        r['created_at'] = str(r['created_at']) if r['created_at'] else None

    return jsonify({'success': True, 'data': rows})


@carbon_bp.route('/api/carbon/add', methods=['POST'])
@login_required
def carbon_add():
    """Add a new carbon emission record."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'}), 400

    factor_id = data.get('factor_id')
    activity_value = data.get('activity_value')
    record_date = data.get('record_date')
    note = data.get('note', '')

    if not all([factor_id, activity_value, record_date]):
        return jsonify({'success': False, 'message': 'factor_id, activity_value, and record_date are required'}), 400

    try:
        activity_value = float(activity_value)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'activity_value must be a number'}), 400

    if activity_value <= 0:
        return jsonify({'success': False, 'message': 'activity_value must be positive'}), 400

    # Get the emission factor
    factor = query_db('SELECT id, category, factor FROM emission_factor WHERE id = %s', (factor_id,), one=True)
    if not factor:
        return jsonify({'success': False, 'message': 'Invalid emission factor'}), 400

    total_carbon = round(activity_value * float(factor['factor']), 4)

    record_id = insert_db(
        'INSERT INTO carbon_record (company_id, user_id, factor_id, category, activity_value, total_carbon, record_date, note) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
        (session['company_id'], session['user_id'], factor_id,
         factor['category'], activity_value, total_carbon, record_date, note)
    )

    # Audit log
    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'CREATE', 'carbon_record', record_id,
         f'Added {factor["category"]} record: {activity_value} -> {total_carbon} kgCO2e',
         request.remote_addr)
    )

    return jsonify({
        'success': True,
        'message': 'Carbon record added successfully',
        'data': {'id': record_id, 'total_carbon': total_carbon}
    }), 201


@carbon_bp.route('/api/carbon/delete/<int:record_id>', methods=['DELETE'])
@login_required
def carbon_delete(record_id):
    """Delete a carbon emission record."""
    record = query_db(
        'SELECT id FROM carbon_record WHERE id = %s AND company_id = %s',
        (record_id, session['company_id']), one=True
    )
    if not record:
        return jsonify({'success': False, 'message': 'Record not found'}), 404

    execute_db('DELETE FROM carbon_record WHERE id = %s', (record_id,))

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'DELETE', 'carbon_record', record_id,
         f'Deleted carbon record #{record_id}', request.remote_addr)
    )

    return jsonify({'success': True, 'message': 'Record deleted successfully'})
