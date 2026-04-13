import csv
import io
from flask import Blueprint, request, session, render_template, jsonify, Response
try:
    import pandas as pd
    _PANDAS_OK = True
except ImportError:
    _PANDAS_OK = False
from backend.utils.db import query_db, execute_db, insert_db
from backend.utils.auth_helper import login_required, get_accessible_store_ids
from backend.utils.alert_checker import check_alerts_for_store

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
    """Get carbon records for accessible stores, with optional date/store filter."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': []})

    date_from   = request.args.get('date_from', '')
    date_to     = request.args.get('date_to', '')
    filter_store = request.args.get('store_id', '')

    placeholders = ','.join(['%s'] * len(store_ids))
    sql = (
        'SELECT cr.id, cr.category, cr.activity_value, cr.total_carbon, '
        'cr.record_date, cr.note, cr.created_at, cr.attachment_url, '
        'ef.sub_type, ef.unit, ef.factor, '
        'u.display_name AS recorded_by, '
        's.name AS store_name '
        'FROM carbon_record cr '
        'LEFT JOIN emission_factor ef ON ef.id = cr.factor_id '
        'LEFT JOIN `user` u ON u.id = cr.user_id '
        'LEFT JOIN store s ON s.id = cr.store_id '
        f'WHERE cr.store_id IN ({placeholders}) '
    )
    params = list(store_ids)

    if filter_store and int(filter_store) in store_ids:
        sql += 'AND cr.store_id = %s '
        params.append(int(filter_store))
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

    factor_id      = data.get('factor_id')
    activity_value = data.get('activity_value')
    record_date    = data.get('record_date')
    note           = data.get('note', '')

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
        'INSERT INTO carbon_record (company_id, store_id, user_id, factor_id, category, activity_value, total_carbon, record_date, note) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (session['company_id'], store_id, session['user_id'], factor_id,
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

    check_alerts_for_store(session['company_id'], store_id)

    return jsonify({
        'success': True,
        'message': 'Carbon record added successfully',
        'data': {'id': record_id, 'total_carbon': total_carbon}
    }), 201


@carbon_bp.route('/api/carbon/edit/<int:record_id>', methods=['PUT'])
@login_required
def carbon_edit(record_id):
    """Edit a carbon record. store_staff may only edit within 24 h of creation."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': False, 'message': 'No accessible stores'}), 403

    ph = ','.join(['%s'] * len(store_ids))
    record = query_db(
        f'SELECT id, created_at, user_id FROM carbon_record '
        f'WHERE id = %s AND store_id IN ({ph})',
        [record_id] + list(store_ids), one=True
    )
    if not record:
        return jsonify({'success': False, 'message': 'Record not found'}), 404

    role = session.get('role')
    if role == 'store_staff':
        from datetime import datetime, timezone
        created = record['created_at']
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        now = datetime.now()
        if (now - created.replace(tzinfo=None)).total_seconds() > 86400:
            return jsonify({'success': False,
                            'message': 'Store staff can only edit records within 24 hours of creation'}), 403

    data = request.get_json() or {}
    fields, params = [], []
    for col in ('category', 'activity_value', 'total_carbon', 'record_date', 'note', 'factor_id'):
        if col in data:
            fields.append(f'{col} = %s')
            params.append(data[col])
    if not fields:
        return jsonify({'success': False, 'message': 'No fields to update'}), 400

    params.append(record_id)
    execute_db(f'UPDATE carbon_record SET {", ".join(fields)} WHERE id = %s', params)
    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'UPDATE', 'carbon_record', record_id,
         f'Edited carbon record #{record_id}', request.remote_addr)
    )
    return jsonify({'success': True, 'message': 'Carbon record updated'})


@carbon_bp.route('/api/carbon/delete/<int:record_id>', methods=['DELETE'])
@login_required
def carbon_delete(record_id):
    """Delete a carbon emission record. store_staff may only withdraw within 24 h."""
    store_ids = get_accessible_store_ids()
    placeholders = ','.join(['%s'] * len(store_ids)) if store_ids else '0'
    record = query_db(
        f'SELECT id, created_at FROM carbon_record WHERE id = %s AND store_id IN ({placeholders})',
        [record_id] + list(store_ids), one=True
    )
    if not record:
        return jsonify({'success': False, 'message': 'Record not found'}), 404

    role = session.get('role')
    if role == 'store_staff':
        from datetime import datetime
        created = record['created_at']
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        if (datetime.now() - created.replace(tzinfo=None)).total_seconds() > 86400:
            return jsonify({'success': False,
                            'message': 'Store staff can only withdraw records within 24 hours of creation'}), 403

    execute_db('DELETE FROM carbon_record WHERE id = %s', (record_id,))
    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'DELETE', 'carbon_record', record_id,
         f'Deleted carbon record #{record_id}', request.remote_addr)
    )
    return jsonify({'success': True, 'message': 'Record deleted successfully'})


@carbon_bp.route('/api/carbon/compare')
@login_required
def carbon_compare():
    """Compare current month vs last month, and store vs region average."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': {}})

    store_id = request.args.get('store_id', type=int)
    if not store_id or store_id not in store_ids:
        store_id = list(store_ids)[0]

    # Current month vs last month for this store
    monthly = query_db(
        'SELECT YEAR(record_date) AS y, MONTH(record_date) AS m, '
        'SUM(total_carbon) AS total '
        'FROM carbon_record WHERE store_id = %s '
        'AND record_date >= DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), "%%Y-%%m-01") '
        'GROUP BY y, m ORDER BY y, m',
        (store_id,)
    )
    this_month = float(monthly[-1]['total']) if monthly else 0
    last_month = float(monthly[0]['total']) if len(monthly) >= 2 else 0
    mom_pct    = round((this_month - last_month) / last_month * 100, 1) if last_month else None

    # Region average (current month)
    store_row = query_db('SELECT region_id FROM store WHERE id = %s', (store_id,), one=True)
    region_id = store_row['region_id'] if store_row else None
    region_avg = None
    if region_id:
        ph = ','.join(['%s'] * len(store_ids))
        avg_row = query_db(
            f'SELECT AVG(monthly_total) AS avg_val FROM ('
            f'  SELECT store_id, SUM(total_carbon) AS monthly_total '
            f'  FROM carbon_record '
            f'  WHERE store_id IN ({ph}) '
            f'  AND YEAR(record_date) = YEAR(CURDATE()) '
            f'  AND MONTH(record_date) = MONTH(CURDATE()) '
            f'  GROUP BY store_id'
            f') t',
            list(store_ids), one=True
        )
        region_avg = round(float(avg_row['avg_val']), 2) if avg_row and avg_row['avg_val'] else None

    return jsonify({'success': True, 'data': {
        'store_id':   store_id,
        'this_month': round(this_month, 2),
        'last_month': round(last_month, 2),
        'mom_pct':    mom_pct,
        'region_avg': region_avg,
    }})


@carbon_bp.route('/api/carbon/export-csv')
@login_required
def carbon_export_csv():
    """Export carbon records as CSV (same filters as list)."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': False, 'message': 'No accessible stores'}), 403

    date_from    = request.args.get('date_from', '')
    date_to      = request.args.get('date_to', '')
    filter_store = request.args.get('store_id', '')

    placeholders = ','.join(['%s'] * len(store_ids))
    sql = (
        'SELECT cr.id, s.name AS store_name, r.name AS region_name, '
        'cr.category, ef.sub_type, cr.activity_value, ef.unit, '
        'cr.total_carbon, cr.record_date, cr.note, '
        'u.display_name AS recorded_by, cr.created_at '
        'FROM carbon_record cr '
        'LEFT JOIN emission_factor ef ON ef.id = cr.factor_id '
        'LEFT JOIN `user` u ON u.id = cr.user_id '
        'LEFT JOIN store s ON s.id = cr.store_id '
        'LEFT JOIN region r ON r.id = s.region_id '
        f'WHERE cr.store_id IN ({placeholders}) '
    )
    params = list(store_ids)

    if filter_store and int(filter_store) in store_ids:
        sql += 'AND cr.store_id = %s '
        params.append(int(filter_store))
    if date_from:
        sql += 'AND cr.record_date >= %s '
        params.append(date_from)
    if date_to:
        sql += 'AND cr.record_date <= %s '
        params.append(date_to)

    sql += 'ORDER BY cr.record_date DESC, cr.id DESC'
    rows = query_db(sql, params)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Store', 'Region', 'Category', 'Emission Source',
                     'Activity Value', 'Unit', 'CO2e (kg)', 'Date', 'Note',
                     'Recorded By', 'Created At'])
    for r in rows:
        writer.writerow([
            r['id'], r['store_name'], r['region_name'],
            r['category'], r['sub_type'],
            r['activity_value'], r['unit'], r['total_carbon'],
            r['record_date'], r['note'] or '',
            r['recorded_by'] or '', r['created_at']
        ])

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s)',
        (session['user_id'], 'EXPORT', 'carbon_record',
         f'Exported {len(rows)} carbon records to CSV', request.remote_addr)
    )

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=carbon_records.csv'}
    )


@carbon_bp.route('/api/carbon/import-template')
@login_required
def carbon_import_template():
    """Download a blank CSV template for batch import."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['store_name', 'sub_type', 'activity_value', 'record_date', 'note'])
    writer.writerow(['Beijing Chaoyang Store', 'Grid Electricity', '1200', '2026-01-15', 'January bill'])
    writer.writerow(['Beijing Chaoyang Store', 'Natural Gas', '300', '2026-01-15', ''])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=carbon_import_template.csv'}
    )


@carbon_bp.route('/api/carbon/import', methods=['POST'])
@login_required
def carbon_import():
    """Batch import carbon records from uploaded CSV/Excel file."""
    if not _PANDAS_OK:
        return jsonify({'success': False, 'message': 'pandas not installed on server'}), 500

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400

    file = request.files['file']
    filename = file.filename.lower()

    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return jsonify({'success': False, 'message': 'Only CSV or Excel files are supported'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to parse file: {e}'}), 400

    required_cols = {'store_name', 'sub_type', 'activity_value', 'record_date'}
    missing = required_cols - set(df.columns.str.strip())
    if missing:
        return jsonify({'success': False,
                        'message': f'Missing required columns: {missing}'}), 400

    df.columns = df.columns.str.strip()
    company_id = session['company_id']

    store_map = {
        r['name']: r['id']
        for r in query_db('SELECT id, name FROM store WHERE company_id = %s', (company_id,))
    }
    factor_map = {
        r['sub_type']: {'id': r['id'], 'factor': float(r['factor']), 'category': r['category']}
        for r in query_db('SELECT id, sub_type, factor, category FROM emission_factor')
    }

    success_count = 0
    errors = []

    for i, row in df.iterrows():
        row_num = i + 2
        store_name = str(row.get('store_name', '')).strip()
        sub_type   = str(row.get('sub_type', '')).strip()
        note       = str(row.get('note', '')).strip() if pd.notna(row.get('note')) else ''

        if store_name not in store_map:
            errors.append(f'Row {row_num}: Store "{store_name}" not found')
            continue
        if sub_type not in factor_map:
            errors.append(f'Row {row_num}: Emission source "{sub_type}" not found')
            continue

        try:
            activity_value = float(row['activity_value'])
            if activity_value <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            errors.append(f'Row {row_num}: Invalid activity_value')
            continue

        try:
            record_date = str(pd.to_datetime(row['record_date']).date())
        except Exception:
            errors.append(f'Row {row_num}: Invalid record_date format')
            continue

        store_id = store_map[store_name]
        fm = factor_map[sub_type]
        total_carbon = round(activity_value * fm['factor'], 4)

        record_id = insert_db(
            'INSERT INTO carbon_record '
            '(company_id, store_id, user_id, factor_id, category, activity_value, total_carbon, record_date, note) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (company_id, store_id, session['user_id'], fm['id'],
             fm['category'], activity_value, total_carbon, record_date, note or None)
        )
        success_count += 1

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s)',
        (session['user_id'], 'CREATE', 'carbon_record',
         f'Batch imported {success_count} carbon records', request.remote_addr)
    )

    return jsonify({
        'success': True,
        'imported': success_count,
        'errors': errors,
        'total_rows': len(df)
    })
