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


@waste_bp.route('/api/waste/edit/<int:record_id>', methods=['PUT'])
@login_required
def waste_edit(record_id):
    """Edit a waste record. store_staff may only edit within 24 h of creation."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': False, 'message': 'No accessible stores'}), 403

    ph = ','.join(['%s'] * len(store_ids))
    record = query_db(
        f'SELECT id, created_at FROM waste_record WHERE id = %s AND store_id IN ({ph})',
        [record_id] + list(store_ids), one=True
    )
    if not record:
        return jsonify({'success': False, 'message': 'Record not found'}), 404

    if session.get('role') == 'store_staff':
        from datetime import datetime
        created = record['created_at']
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        if (datetime.now() - created.replace(tzinfo=None)).total_seconds() > 86400:
            return jsonify({'success': False,
                            'message': 'Store staff can only edit records within 24 hours of creation'}), 403

    data = request.get_json() or {}
    fields, params = [], []
    for col in ('weight_kg', 'recycled_kg', 'source_type', 'disposal_method', 'record_date', 'note'):
        if col in data:
            fields.append(f'{col} = %s')
            params.append(data[col])
    if not fields:
        return jsonify({'success': False, 'message': 'No fields to update'}), 400

    params.append(record_id)
    execute_db(f'UPDATE waste_record SET {", ".join(fields)} WHERE id = %s', params)
    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'UPDATE', 'waste_record', record_id,
         f'Edited waste record #{record_id}', request.remote_addr)
    )
    return jsonify({'success': True, 'message': 'Waste record updated'})


@waste_bp.route('/api/waste/delete/<int:record_id>', methods=['DELETE'])
@login_required
def waste_delete(record_id):
    """Delete a waste record. store_staff may only withdraw within 24 h."""
    store_ids = get_accessible_store_ids()
    placeholders = ','.join(['%s'] * len(store_ids)) if store_ids else '0'
    record = query_db(
        f'SELECT id, created_at FROM waste_record WHERE id = %s AND store_id IN ({placeholders})',
        [record_id] + list(store_ids), one=True
    )
    if not record:
        return jsonify({'success': False, 'message': 'Record not found'}), 404

    if session.get('role') == 'store_staff':
        from datetime import datetime
        created = record['created_at']
        if isinstance(created, str):
            created = datetime.fromisoformat(created)
        if (datetime.now() - created.replace(tzinfo=None)).total_seconds() > 86400:
            return jsonify({'success': False,
                            'message': 'Store staff can only withdraw records within 24 hours of creation'}), 403

    execute_db('DELETE FROM waste_record WHERE id = %s', (record_id,))
    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'DELETE', 'waste_record', record_id,
         f'Deleted waste record #{record_id}', request.remote_addr)
    )
    return jsonify({'success': True, 'message': 'Record deleted successfully'})


@waste_bp.route('/api/waste/compare')
@login_required
def waste_compare():
    """Compare current month vs last month waste, and store vs region average."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': {}})

    store_id = request.args.get('store_id', type=int)
    if not store_id or store_id not in store_ids:
        store_id = list(store_ids)[0]

    monthly = query_db(
        'SELECT YEAR(record_date) AS y, MONTH(record_date) AS m, SUM(weight_kg) AS total '
        'FROM waste_record WHERE store_id = %s '
        'AND record_date >= DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), "%%Y-%%m-01") '
        'GROUP BY y, m ORDER BY y, m',
        (store_id,)
    )
    this_month = float(monthly[-1]['total']) if monthly else 0
    last_month = float(monthly[0]['total']) if len(monthly) >= 2 else 0
    mom_pct    = round((this_month - last_month) / last_month * 100, 1) if last_month else None

    store_row  = query_db('SELECT region_id FROM store WHERE id = %s', (store_id,), one=True)
    region_avg = None
    if store_row and store_row['region_id']:
        ph = ','.join(['%s'] * len(store_ids))
        avg_row = query_db(
            f'SELECT AVG(monthly_total) AS avg_val FROM ('
            f'  SELECT store_id, SUM(weight_kg) AS monthly_total '
            f'  FROM waste_record WHERE store_id IN ({ph}) '
            f'  AND YEAR(record_date) = YEAR(CURDATE()) '
            f'  AND MONTH(record_date) = MONTH(CURDATE()) '
            f'  GROUP BY store_id) t',
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


@waste_bp.route('/api/waste/export-csv')
@login_required
def waste_export_csv():
    """Export waste records as CSV (same filters as list)."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': False, 'message': 'No accessible stores'}), 403

    date_from    = request.args.get('date_from', '')
    date_to      = request.args.get('date_to', '')
    filter_store = request.args.get('store_id', '')

    placeholders = ','.join(['%s'] * len(store_ids))
    sql = (
        'SELECT wr.id, s.name AS store_name, r.name AS region_name, '
        'wc.name AS category_name, wr.source_type, '
        'wr.weight_kg, wr.recycled_kg, '
        'wr.disposal_method, wr.disposal_unit, '
        'wr.record_date, wr.note, '
        'u.display_name AS recorded_by, wr.created_at '
        'FROM waste_record wr '
        'JOIN waste_category wc ON wc.id = wr.category_id '
        'LEFT JOIN `user` u ON u.id = wr.user_id '
        'LEFT JOIN store s ON s.id = wr.store_id '
        'LEFT JOIN region r ON r.id = s.region_id '
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

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Store', 'Region', 'Category', 'Source Type',
                     'Total Weight (kg)', 'Recycled (kg)', 'Recycling Rate (%)',
                     'Disposal Method', 'Disposal Unit',
                     'Date', 'Note', 'Recorded By', 'Created At'])
    for r in rows:
        rate = round(float(r['recycled_kg'] or 0) / float(r['weight_kg']) * 100, 1) \
               if r['weight_kg'] else 0
        writer.writerow([
            r['id'], r['store_name'], r['region_name'],
            r['category_name'], r['source_type'],
            r['weight_kg'], r['recycled_kg'], rate,
            r['disposal_method'] or '', r['disposal_unit'] or '',
            r['record_date'], r['note'] or '',
            r['recorded_by'] or '', r['created_at']
        ])

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s)',
        (session['user_id'], 'EXPORT', 'waste_record',
         f'Exported {len(rows)} waste records to CSV', request.remote_addr)
    )

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=waste_records.csv'}
    )


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


@waste_bp.route('/api/waste/import-template')
@login_required
def waste_import_template():
    """Download a blank CSV template for batch waste import."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['store_name', 'category_name', 'source_type',
                     'weight_kg', 'recycled_kg', 'record_date', 'note'])
    writer.writerow(['Beijing Chaoyang Store', 'Cardboard & Paper',
                     'packaging', '45.5', '30.0', '2026-01-15', 'Monthly collection'])
    writer.writerow(['Beijing Chaoyang Store', 'Food Waste',
                     'food_residue', '120.0', '0', '2026-01-15', ''])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=waste_import_template.csv'}
    )


@waste_bp.route('/api/waste/import', methods=['POST'])
@login_required
def waste_import():
    """Batch import waste records from uploaded CSV/Excel file."""
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

    required_cols = {'store_name', 'category_name', 'weight_kg', 'record_date'}
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
    category_map = {
        r['name']: r['id']
        for r in query_db('SELECT id, name FROM waste_category')
    }

    VALID_SOURCE = {'packaging', 'food_residue', 'hazardous', 'other'}
    success_count = 0
    errors = []

    for i, row in df.iterrows():
        row_num = i + 2
        store_name    = str(row.get('store_name', '')).strip()
        category_name = str(row.get('category_name', '')).strip()
        source_type   = str(row.get('source_type', 'other')).strip()
        note          = str(row.get('note', '')).strip() if pd.notna(row.get('note')) else ''

        if store_name not in store_map:
            errors.append(f'Row {row_num}: Store "{store_name}" not found')
            continue
        if category_name not in category_map:
            errors.append(f'Row {row_num}: Category "{category_name}" not found')
            continue
        if source_type not in VALID_SOURCE:
            source_type = 'other'

        try:
            weight_kg    = float(row['weight_kg'])
            recycled_kg  = float(row.get('recycled_kg', 0) or 0)
            if weight_kg <= 0:
                raise ValueError()
            recycled_kg = min(recycled_kg, weight_kg)
        except (ValueError, TypeError):
            errors.append(f'Row {row_num}: Invalid weight_kg value')
            continue

        try:
            record_date = str(pd.to_datetime(row['record_date']).date())
        except Exception:
            errors.append(f'Row {row_num}: Invalid record_date format')
            continue

        store_id    = store_map[store_name]
        category_id = category_map[category_name]

        insert_db(
            'INSERT INTO waste_record '
            '(company_id, store_id, user_id, category_id, source_type, '
            'weight_kg, recycled_kg, record_date, note) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (company_id, store_id, session['user_id'], category_id,
             source_type, weight_kg, recycled_kg, record_date, note or None)
        )
        success_count += 1

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s)',
        (session['user_id'], 'CREATE', 'waste_record',
         f'Batch imported {success_count} waste records', request.remote_addr)
    )

    return jsonify({
        'success': True,
        'imported': success_count,
        'errors': errors,
        'total_rows': len(df)
    })
