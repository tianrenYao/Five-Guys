from flask import Blueprint, request, session, render_template, jsonify
from backend.utils.db import query_db, execute_db, insert_db
from backend.utils.auth_helper import login_required, role_required, get_accessible_store_ids

training_bp = Blueprint('training', __name__)

COURSE_TYPES = [
    'carbon_awareness', 'waste_management', 'energy_efficiency',
    'sustainability_reporting', 'green_procurement', 'other'
]


@training_bp.route('/training')
@login_required
def training_page():
    return render_template('training.html')


@training_bp.route('/api/training/list')
@login_required
def training_list():
    """List training records accessible to the current user."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': []})

    ph  = ','.join(['%s'] * len(store_ids))
    sid = list(store_ids)

    store_filter  = request.args.get('store_id',    '')
    course_filter = request.args.get('course_type', '')
    status_filter = request.args.get('status',      '')
    date_from     = request.args.get('date_from',   '')
    date_to       = request.args.get('date_to',     '')

    where  = [f'tr.store_id IN ({ph})']
    params = sid

    if store_filter:
        where.append('tr.store_id = %s'); params.append(int(store_filter))
    if course_filter:
        where.append('tr.course_type = %s'); params.append(course_filter)
    if status_filter:
        where.append('tr.status = %s'); params.append(status_filter)
    if date_from:
        where.append('tr.completion_date >= %s'); params.append(date_from)
    if date_to:
        where.append('tr.completion_date <= %s'); params.append(date_to)

    sql = (
        'SELECT tr.id, tr.course_name, tr.course_type, tr.duration_hours, '
        'tr.completion_date, tr.score, tr.status, tr.note, '
        's.name AS store_name, '
        'u.display_name AS trainee_name, '
        'cb.display_name AS created_by '
        'FROM training_record tr '
        'LEFT JOIN store s ON s.id = tr.store_id '
        'LEFT JOIN `user` u ON u.id = tr.trainee_user_id '
        'LEFT JOIN `user` cb ON cb.id = tr.created_by '
        f'WHERE {" AND ".join(where)} '
        'ORDER BY tr.completion_date DESC'
    )
    rows = query_db(sql, params)
    for r in rows:
        r['completion_date'] = str(r['completion_date']) if r['completion_date'] else None
        r['duration_hours']  = float(r['duration_hours'] or 0)
    return jsonify({'success': True, 'data': rows})


@training_bp.route('/api/training/stats')
@login_required
def training_stats():
    """Aggregate training stats for the current company's accessible stores."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': {}})

    ph  = ','.join(['%s'] * len(store_ids))
    sid = list(store_ids)

    totals = query_db(
        f'SELECT COUNT(*) AS total_sessions, '
        f'SUM(duration_hours) AS total_hours, '
        f'COUNT(DISTINCT trainee_user_id) AS unique_trainees, '
        f'ROUND(AVG(score),1) AS avg_score '
        f'FROM training_record WHERE store_id IN ({ph}) '
        f'AND YEAR(completion_date) = YEAR(CURDATE()) '
        f'AND status = "completed"',
        sid, one=True
    )
    by_type = query_db(
        f'SELECT course_type, COUNT(*) AS cnt, SUM(duration_hours) AS hours '
        f'FROM training_record WHERE store_id IN ({ph}) '
        f'AND YEAR(completion_date) = YEAR(CURDATE()) '
        f'AND status = "completed" '
        f'GROUP BY course_type ORDER BY cnt DESC',
        sid
    )
    for r in by_type:
        r['hours'] = float(r['hours'] or 0)

    return jsonify({
        'success': True,
        'data': {
            'total_sessions':  totals['total_sessions'] or 0,
            'total_hours':     float(totals['total_hours'] or 0),
            'unique_trainees': totals['unique_trainees'] or 0,
            'avg_score':       float(totals['avg_score'] or 0),
            'by_type':         by_type
        }
    })


@training_bp.route('/api/training/create', methods=['POST'])
@login_required
def training_create():
    """Log a new training record."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400

    course_name      = data.get('course_name', '').strip()
    course_type      = data.get('course_type', 'other')
    store_id         = data.get('store_id')
    trainee_user_id  = data.get('trainee_user_id')
    duration_hours   = data.get('duration_hours', 0)
    completion_date  = data.get('completion_date')
    score            = data.get('score')
    status           = data.get('status', 'completed')
    note             = data.get('note', '').strip() or None

    if not all([course_name, completion_date]):
        return jsonify({'success': False, 'message': 'course_name and completion_date are required'}), 400
    if course_type not in COURSE_TYPES:
        course_type = 'other'

    # Verify store belongs to company
    company_id   = session['company_id']
    accessible   = get_accessible_store_ids()
    if store_id and int(store_id) not in accessible:
        return jsonify({'success': False, 'message': 'Store not accessible'}), 403

    record_id = insert_db(
        'INSERT INTO training_record '
        '(company_id, store_id, trainee_user_id, course_name, course_type, '
        'duration_hours, completion_date, score, status, note, created_by) '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
        (company_id, store_id or None, trainee_user_id or None,
         course_name, course_type, float(duration_hours),
         completion_date, score or None, status, note, session['user_id'])
    )

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s,%s,%s,%s,%s,%s)',
        (session['user_id'], 'CREATE', 'training_record', record_id,
         f'Logged training: {course_name}', request.remote_addr)
    )

    return jsonify({'success': True, 'message': 'Training record created', 'id': record_id}), 201


@training_bp.route('/api/training/<int:record_id>', methods=['DELETE'])
@login_required
@role_required('admin', 'hq_manager', 'region_manager')
def training_delete(record_id):
    """Delete a training record."""
    row = query_db(
        'SELECT id FROM training_record WHERE id = %s AND company_id = %s',
        (record_id, session['company_id']), one=True
    )
    if not row:
        return jsonify({'success': False, 'message': 'Record not found'}), 404

    execute_db('DELETE FROM training_record WHERE id = %s', (record_id,))
    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s,%s,%s,%s,%s,%s)',
        (session['user_id'], 'DELETE', 'training_record', record_id,
         f'Deleted training record #{record_id}', request.remote_addr)
    )
    return jsonify({'success': True, 'message': 'Deleted'})
