from flask import Blueprint, request, session, jsonify, render_template
from backend.utils.db import query_db, execute_db, insert_db
from backend.utils.auth_helper import login_required, role_required

supplier_bp = Blueprint('supplier', __name__)

DIMENSION_FIELDS = {
    'carbon': [
        'carbon_disclosure',
        'carbon_target',
        'carbon_measures',
        'carbon_certification',
    ],
    'waste': [
        'waste_policy',
        'waste_recycling',
        'waste_packaging',
        'waste_tracking',
    ],
    'ethics': [
        'ethics_labor',
        'ethics_safety',
        'ethics_working_conditions',
        'ethics_governance',
    ],
    'reporting': [
        'reporting_report',
        'reporting_completeness',
        'reporting_frequency',
        'reporting_verification',
    ],
}

DIMENSION_WEIGHTS = {
    'carbon': [0.30, 0.25, 0.25, 0.20],
    'waste': [0.25, 0.30, 0.25, 0.20],
    'ethics': [0.35, 0.25, 0.20, 0.20],
    'reporting': [0.30, 0.30, 0.20, 0.20],
}

OVERALL_WEIGHTS = {
    'carbon': 0.30,
    'waste': 0.30,
    'ethics': 0.20,
    'reporting': 0.20,
}

MOCK_SUPPLIERS = [
    {'id':1,'name':'GreenBean Co.','category':'Coffee Beans','country':'Colombia',
     'carbon_score':83,'waste_score':73,'ethics_score':90,'reporting_score':80,
     'overall_grade':'B','notes':'Rainforest Alliance certified; annual sustainability report published.','audited_at':None},
    {'id':2,'name':'EcoPack Ltd.','category':'Packaging','country':'China',
     'carbon_score':68,'waste_score':83,'ethics_score':75,'reporting_score':65,
     'overall_grade':'B','notes':'Uses 80% recycled materials; limited carbon disclosure.','audited_at':None},
    {'id':3,'name':'SwiftLogistics Inc.','category':'Logistics','country':'Ireland',
     'carbon_score':43,'waste_score':50,'ethics_score':63,'reporting_score':45,
     'overall_grade':'C','notes':'Fleet electrification plan underway; no formal ESG report yet.','audited_at':None},
    {'id':4,'name':'PureMilk Farms','category':'Dairy','country':'Ireland',
     'carbon_score':68,'waste_score':60,'ethics_score':80,'reporting_score':65,
     'overall_grade':'B','notes':'Carbon-neutral milk pilot; moderate waste recovery rate.','audited_at':None},
    {'id':5,'name':'CleanCup Corp.','category':'Disposables','country':'Germany',
     'carbon_score':90,'waste_score':90,'ethics_score':85,'reporting_score':90,
     'overall_grade':'A','notes':'Industry leader in compostable cup technology; full GRI reporting.','audited_at':None},
]


def _normalize_score_value(value):
    if value in (None, ''):
        return None
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValueError('Scorecard values must be 0, 50, or 100')
    if value not in (0, 50, 100):
        raise ValueError('Scorecard values must be 0, 50, or 100')
    return value


def _grade_from_score(score):
    if score is None:
        return None
    if score >= 85:
        return 'A'
    if score >= 70:
        return 'B'
    if score >= 55:
        return 'C'
    if score >= 40:
        return 'D'
    return 'F'


def _build_scorecard(data):
    normalized = {}
    for fields in DIMENSION_FIELDS.values():
        for field in fields:
            normalized[field] = _normalize_score_value(data.get(field))

    dimension_scores = {}
    for dimension, fields in DIMENSION_FIELDS.items():
        values = [normalized[field] for field in fields]
        if any(value is None for value in values):
            raise ValueError(f'All {dimension} scorecard items are required')
        weights = DIMENSION_WEIGHTS[dimension]
        dimension_scores[dimension] = round(sum(value * weight for value, weight in zip(values, weights)))

    overall_score = round(sum(dimension_scores[key] * OVERALL_WEIGHTS[key] for key in OVERALL_WEIGHTS))

    return {
        'normalized': normalized,
        'dimension_scores': dimension_scores,
        'overall_score': overall_score,
        'overall_grade': _grade_from_score(overall_score),
    }


def _use_mock():
    """Return True if supplier table doesn't exist or has no rows for this company."""
    try:
        rows = query_db('SELECT COUNT(*) AS cnt FROM supplier WHERE company_id = %s',
                        (session.get('company_id', 1),), one=True)
        return (rows['cnt'] == 0)
    except Exception:
        return True


@supplier_bp.route('/supplier')
@login_required
def supplier_page():
    return render_template('supplier.html')


@supplier_bp.route('/api/supplier/list')
@login_required
def supplier_list():
    company_id = session['company_id']
    if _use_mock():
        return jsonify({'success': True, 'data': MOCK_SUPPLIERS, 'mock': True})
    rows = query_db(
        'SELECT s.id, s.name, s.category, s.country, '
        's.carbon_disclosure, s.carbon_target, s.carbon_measures, s.carbon_certification, '
        's.waste_policy, s.waste_recycling, s.waste_packaging, s.waste_tracking, '
        's.ethics_labor, s.ethics_safety, s.ethics_working_conditions, s.ethics_governance, '
        's.reporting_report, s.reporting_completeness, s.reporting_frequency, s.reporting_verification, '
        's.carbon_score, s.waste_score, s.ethics_score, s.reporting_score, '
        's.overall_grade, s.notes, s.audited_at, u.display_name AS audited_by_name '
        'FROM supplier s LEFT JOIN `user` u ON u.id = s.audited_by '
        'WHERE s.company_id = %s ORDER BY s.overall_grade, s.name',
        (company_id,)
    )
    for r in rows:
        r['audited_at'] = str(r['audited_at']) if r['audited_at'] else None
    return jsonify({'success': True, 'data': rows})


@supplier_bp.route('/api/supplier/add', methods=['POST'])
@login_required
@role_required('hq_manager', 'admin')
def supplier_add():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Supplier name is required'}), 400

    try:
        scorecard = _build_scorecard(data)
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400

    new_id = insert_db(
        'INSERT INTO supplier (company_id, name, category, country, '
        'carbon_disclosure, carbon_target, carbon_measures, carbon_certification, '
        'waste_policy, waste_recycling, waste_packaging, waste_tracking, '
        'ethics_labor, ethics_safety, ethics_working_conditions, ethics_governance, '
        'reporting_report, reporting_completeness, reporting_frequency, reporting_verification, '
        'carbon_score, waste_score, ethics_score, reporting_score, '
        'overall_grade, notes, audited_by, audited_at) '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())',
        (session['company_id'], name,
         data.get('category'), data.get('country'),
         scorecard['normalized']['carbon_disclosure'], scorecard['normalized']['carbon_target'],
         scorecard['normalized']['carbon_measures'], scorecard['normalized']['carbon_certification'],
         scorecard['normalized']['waste_policy'], scorecard['normalized']['waste_recycling'],
         scorecard['normalized']['waste_packaging'], scorecard['normalized']['waste_tracking'],
         scorecard['normalized']['ethics_labor'], scorecard['normalized']['ethics_safety'],
         scorecard['normalized']['ethics_working_conditions'], scorecard['normalized']['ethics_governance'],
         scorecard['normalized']['reporting_report'], scorecard['normalized']['reporting_completeness'],
         scorecard['normalized']['reporting_frequency'], scorecard['normalized']['reporting_verification'],
         scorecard['dimension_scores']['carbon'], scorecard['dimension_scores']['waste'],
         scorecard['dimension_scores']['ethics'], scorecard['dimension_scores']['reporting'],
         scorecard['overall_grade'], data.get('notes'), session['user_id'])
    )
    return jsonify({'success': True, 'message': 'Supplier added', 'data': {'id': new_id}}), 201


@supplier_bp.route('/api/supplier/edit/<int:sid>', methods=['PUT'])
@login_required
@role_required('hq_manager', 'admin')
def supplier_edit(sid):
    row = query_db('SELECT id FROM supplier WHERE id = %s AND company_id = %s',
                   (sid, session['company_id']), one=True)
    if not row:
        return jsonify({'success': False, 'message': 'Supplier not found'}), 404

    data = request.get_json() or {}

    try:
        scorecard = _build_scorecard(data)
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400

    execute_db(
        'UPDATE supplier SET name=%s, category=%s, country=%s, '
        'carbon_disclosure=%s, carbon_target=%s, carbon_measures=%s, carbon_certification=%s, '
        'waste_policy=%s, waste_recycling=%s, waste_packaging=%s, waste_tracking=%s, '
        'ethics_labor=%s, ethics_safety=%s, ethics_working_conditions=%s, ethics_governance=%s, '
        'reporting_report=%s, reporting_completeness=%s, reporting_frequency=%s, reporting_verification=%s, '
        'carbon_score=%s, waste_score=%s, ethics_score=%s, reporting_score=%s, '
        'overall_grade=%s, notes=%s, audited_by=%s, audited_at=NOW() '
        'WHERE id=%s',
        (data.get('name'), data.get('category'), data.get('country'),
         scorecard['normalized']['carbon_disclosure'], scorecard['normalized']['carbon_target'],
         scorecard['normalized']['carbon_measures'], scorecard['normalized']['carbon_certification'],
         scorecard['normalized']['waste_policy'], scorecard['normalized']['waste_recycling'],
         scorecard['normalized']['waste_packaging'], scorecard['normalized']['waste_tracking'],
         scorecard['normalized']['ethics_labor'], scorecard['normalized']['ethics_safety'],
         scorecard['normalized']['ethics_working_conditions'], scorecard['normalized']['ethics_governance'],
         scorecard['normalized']['reporting_report'], scorecard['normalized']['reporting_completeness'],
         scorecard['normalized']['reporting_frequency'], scorecard['normalized']['reporting_verification'],
         scorecard['dimension_scores']['carbon'], scorecard['dimension_scores']['waste'],
         scorecard['dimension_scores']['ethics'], scorecard['dimension_scores']['reporting'],
         scorecard['overall_grade'], data.get('notes'), session['user_id'], sid)
    )
    return jsonify({'success': True, 'message': 'Supplier updated'})


@supplier_bp.route('/api/supplier/delete/<int:sid>', methods=['DELETE'])
@login_required
@role_required('hq_manager', 'admin')
def supplier_delete(sid):
    row = query_db('SELECT id FROM supplier WHERE id = %s AND company_id = %s',
                   (sid, session['company_id']), one=True)
    if not row:
        return jsonify({'success': False, 'message': 'Supplier not found'}), 404
    execute_db('DELETE FROM supplier WHERE id = %s', (sid,))
    return jsonify({'success': True, 'message': 'Supplier deleted'})
