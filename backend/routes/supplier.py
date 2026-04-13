from flask import Blueprint, request, session, jsonify, render_template
from backend.utils.db import query_db, execute_db, insert_db
from backend.utils.auth_helper import login_required, role_required

supplier_bp = Blueprint('supplier', __name__)

MOCK_SUPPLIERS = [
    {'id':1,'name':'GreenBean Co.','category':'Coffee Beans','country':'Colombia',
     'carbon_score':82,'waste_score':75,'ethics_score':90,'reporting_score':70,
     'overall_grade':'B','notes':'Rainforest Alliance certified; annual sustainability report published.','audited_at':None},
    {'id':2,'name':'EcoPack Ltd.','category':'Packaging','country':'China',
     'carbon_score':65,'waste_score':88,'ethics_score':72,'reporting_score':55,
     'overall_grade':'B','notes':'Uses 80% recycled materials; limited carbon disclosure.','audited_at':None},
    {'id':3,'name':'SwiftLogistics Inc.','category':'Logistics','country':'Ireland',
     'carbon_score':45,'waste_score':50,'ethics_score':68,'reporting_score':40,
     'overall_grade':'C','notes':'Fleet electrification plan underway; no formal ESG report yet.','audited_at':None},
    {'id':4,'name':'PureMilk Farms','category':'Dairy','country':'Ireland',
     'carbon_score':70,'waste_score':60,'ethics_score':80,'reporting_score':60,
     'overall_grade':'B','notes':'Carbon-neutral milk pilot; moderate waste recovery rate.','audited_at':None},
    {'id':5,'name':'CleanCup Corp.','category':'Disposables','country':'Germany',
     'carbon_score':90,'waste_score':92,'ethics_score':85,'reporting_score':88,
     'overall_grade':'A','notes':'Industry leader in compostable cup technology; full GRI reporting.','audited_at':None},
]


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

    def grade(scores):
        valid = [s for s in scores if s is not None]
        if not valid:
            return None
        avg = sum(valid) / len(valid)
        if avg >= 85: return 'A'
        if avg >= 70: return 'B'
        if avg >= 55: return 'C'
        if avg >= 40: return 'D'
        return 'F'

    scores = [data.get('carbon_score'), data.get('waste_score'),
              data.get('ethics_score'), data.get('reporting_score')]
    overall = grade(scores)

    new_id = insert_db(
        'INSERT INTO supplier (company_id, name, category, country, '
        'carbon_score, waste_score, ethics_score, reporting_score, '
        'overall_grade, notes, audited_by, audited_at) '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())',
        (session['company_id'], name,
         data.get('category'), data.get('country'),
         data.get('carbon_score'), data.get('waste_score'),
         data.get('ethics_score'), data.get('reporting_score'),
         overall, data.get('notes'), session['user_id'])
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
    scores = [data.get('carbon_score'), data.get('waste_score'),
              data.get('ethics_score'), data.get('reporting_score')]

    def grade(scores):
        valid = [s for s in scores if s is not None]
        if not valid: return None
        avg = sum(valid) / len(valid)
        if avg >= 85: return 'A'
        if avg >= 70: return 'B'
        if avg >= 55: return 'C'
        if avg >= 40: return 'D'
        return 'F'

    execute_db(
        'UPDATE supplier SET name=%s, category=%s, country=%s, '
        'carbon_score=%s, waste_score=%s, ethics_score=%s, reporting_score=%s, '
        'overall_grade=%s, notes=%s, audited_by=%s, audited_at=NOW() '
        'WHERE id=%s',
        (data.get('name'), data.get('category'), data.get('country'),
         data.get('carbon_score'), data.get('waste_score'),
         data.get('ethics_score'), data.get('reporting_score'),
         grade(scores), data.get('notes'), session['user_id'], sid)
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
