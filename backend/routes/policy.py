from flask import Blueprint, request, session, jsonify, render_template
from backend.utils.db import query_db, execute_db, insert_db
from backend.utils.auth_helper import login_required, role_required

policy_bp = Blueprint('policy', __name__)

MOCK_POLICIES = [
    {'id':1,'title':'Responsible Consumption & Waste Policy','category':'sdg12',
     'version':'1.2','status':'active','effective_date':'2025-01-01',
     'created_by_name':'HQ ESG Manager','updated_at':'2025-03-10 08:00:00',
     'content':'## Purpose\nThis policy commits the company to SDG 12 targets by reducing single-use plastics, improving packaging recyclability, and achieving ≥60% waste recovery rate across all stores by 2026.\n\n## Key Commitments\n- Replace all single-use plastic cups with certified compostable alternatives by Q4 2025.\n- Mandate supplier ESG assessments (minimum grade C) for all tier-1 suppliers.\n- Publish quarterly waste and recycling KPI dashboards accessible to all store managers.'},
    {'id':2,'title':'Carbon Reduction Roadmap','category':'environment',
     'version':'2.0','status':'active','effective_date':'2025-03-01',
     'created_by_name':'HQ ESG Manager','updated_at':'2025-03-01 00:00:00',
     'content':'## Objective\nReduce absolute carbon emissions by 30% by 2030 (baseline: 2023).\n\n## Actions\n- Transition store energy to renewable sources by 2027.\n- Partner with low-carbon logistics providers.\n- Implement monthly carbon tracking and anomaly reporting for all stores.'},
    {'id':3,'title':'Supplier Code of Conduct','category':'governance',
     'version':'1.0','status':'active','effective_date':'2024-06-01',
     'created_by_name':'HQ ESG Manager','updated_at':'2024-06-01 00:00:00',
     'content':'## Introduction\nAll suppliers must meet minimum ESG standards before onboarding and undergo annual assessments.\n\n## Requirements\n- Carbon disclosure: Must report Scope 1 & 2 emissions.\n- Waste: Must demonstrate a formal waste management plan.\n- Social: No child labour; fair wages; safe working conditions.'},
]


def _use_mock():
    try:
        rows = query_db('SELECT COUNT(*) AS cnt FROM esg_policy WHERE company_id = %s',
                        (session.get('company_id', 1),), one=True)
        return rows['cnt'] == 0
    except Exception:
        return True


@policy_bp.route('/policy')
@login_required
def policy_page():
    return render_template('policy.html')


@policy_bp.route('/api/policy/list')
@login_required
def policy_list():
    if _use_mock():
        return jsonify({'success': True, 'data': MOCK_POLICIES, 'mock': True})
    rows = query_db(
        'SELECT p.id, p.title, p.category, p.version, p.status, p.effective_date, '
        'p.content, p.updated_at, u.display_name AS created_by_name '
        'FROM esg_policy p LEFT JOIN `user` u ON u.id = p.created_by '
        'WHERE p.company_id = %s ORDER BY p.status DESC, p.updated_at DESC',
        (session['company_id'],)
    )
    for r in rows:
        r['effective_date'] = str(r['effective_date']) if r['effective_date'] else None
        r['updated_at']     = str(r['updated_at'])     if r['updated_at']     else None
    return jsonify({'success': True, 'data': rows})


@policy_bp.route('/api/policy/add', methods=['POST'])
@login_required
@role_required('hq_manager', 'admin')
def policy_add():
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    if not title or not content:
        return jsonify({'success': False, 'message': 'Title and content are required'}), 400

    new_id = insert_db(
        'INSERT INTO esg_policy (company_id, title, category, content, version, status, effective_date, created_by) '
        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
        (session['company_id'], title,
         data.get('category', 'other'), content,
         data.get('version', '1.0'),
         data.get('status', 'draft'),
         data.get('effective_date') or None,
         session['user_id'])
    )
    return jsonify({'success': True, 'message': 'Policy created', 'data': {'id': new_id}}), 201


@policy_bp.route('/api/policy/edit/<int:pid>', methods=['PUT'])
@login_required
@role_required('hq_manager', 'admin')
def policy_edit(pid):
    row = query_db('SELECT id FROM esg_policy WHERE id = %s AND company_id = %s',
                   (pid, session['company_id']), one=True)
    if not row:
        return jsonify({'success': False, 'message': 'Policy not found'}), 404

    data = request.get_json() or {}
    fields, params = [], []
    for col in ('title', 'category', 'content', 'version', 'status', 'effective_date'):
        if col in data:
            fields.append(f'{col} = %s')
            params.append(data[col])
    fields.append('updated_by = %s')
    params.append(session['user_id'])

    params.append(pid)
    execute_db(f'UPDATE esg_policy SET {", ".join(fields)} WHERE id = %s', params)
    return jsonify({'success': True, 'message': 'Policy updated'})


@policy_bp.route('/api/policy/delete/<int:pid>', methods=['DELETE'])
@login_required
@role_required('hq_manager', 'admin')
def policy_delete(pid):
    row = query_db('SELECT id FROM esg_policy WHERE id = %s AND company_id = %s',
                   (pid, session['company_id']), one=True)
    if not row:
        return jsonify({'success': False, 'message': 'Policy not found'}), 404
    execute_db('DELETE FROM esg_policy WHERE id = %s', (pid,))
    return jsonify({'success': True, 'message': 'Policy deleted'})
