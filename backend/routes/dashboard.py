from flask import Blueprint, render_template, session, jsonify
from backend.utils.db import query_db
from backend.utils.auth_helper import login_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('dashboard.html')


@dashboard_bp.route('/api/dashboard/summary')
@login_required
def dashboard_summary():
    """Get overview statistics for the current company."""
    company_id = session['company_id']

    # Total carbon emissions this year
    carbon_total = query_db(
        'SELECT COALESCE(SUM(total_carbon), 0) AS total '
        'FROM carbon_record WHERE company_id = %s AND YEAR(record_date) = YEAR(CURDATE())',
        (company_id,), one=True
    )

    # Total waste this year
    waste_total = query_db(
        'SELECT COALESCE(SUM(weight_kg), 0) AS total '
        'FROM waste_record WHERE company_id = %s AND YEAR(record_date) = YEAR(CURDATE())',
        (company_id,), one=True
    )

    # Recycling rate this year
    recycling = query_db(
        'SELECT COALESCE(SUM(wr.weight_kg), 0) AS recyclable '
        'FROM waste_record wr '
        'JOIN waste_category wc ON wc.id = wr.category_id '
        'WHERE wr.company_id = %s AND YEAR(wr.record_date) = YEAR(CURDATE()) '
        'AND wc.is_recyclable = 1',
        (company_id,), one=True
    )

    # Report count
    report_count = query_db(
        'SELECT COUNT(*) AS cnt FROM report WHERE company_id = %s',
        (company_id,), one=True
    )

    waste_val = float(waste_total['total'])
    recyc_val = float(recycling['recyclable'])
    rate = round(recyc_val / waste_val * 100, 1) if waste_val > 0 else 0

    return jsonify({
        'success': True,
        'data': {
            'carbon_total_kg': float(carbon_total['total']),
            'waste_total_kg': waste_val,
            'recycling_rate': rate,
            'report_count': report_count['cnt']
        }
    })


@dashboard_bp.route('/api/dashboard/carbon-trend')
@login_required
def carbon_trend():
    """Monthly carbon emission trend for the current year."""
    company_id = session['company_id']
    rows = query_db(
        'SELECT month, total_carbon_kg '
        'FROM v_carbon_monthly_summary '
        'WHERE company_id = %s AND year = YEAR(CURDATE()) '
        'ORDER BY month',
        (company_id,)
    )
    months = [r['month'] for r in rows]
    values = [float(r['total_carbon_kg']) for r in rows]
    return jsonify({'success': True, 'data': {'months': months, 'values': values}})


@dashboard_bp.route('/api/dashboard/carbon-by-category')
@login_required
def carbon_by_category():
    """Carbon emissions breakdown by category for the current year."""
    company_id = session['company_id']
    rows = query_db(
        'SELECT category, SUM(total_carbon_kg) AS total '
        'FROM v_carbon_monthly_summary '
        'WHERE company_id = %s AND year = YEAR(CURDATE()) '
        'GROUP BY category',
        (company_id,)
    )
    data = [{'name': r['category'], 'value': float(r['total'])} for r in rows]
    return jsonify({'success': True, 'data': data})


@dashboard_bp.route('/api/dashboard/waste-composition')
@login_required
def waste_composition():
    """Waste composition by category for the current year."""
    company_id = session['company_id']
    rows = query_db(
        'SELECT wc.name, SUM(wr.weight_kg) AS total '
        'FROM waste_record wr '
        'JOIN waste_category wc ON wc.id = wr.category_id '
        'WHERE wr.company_id = %s AND YEAR(wr.record_date) = YEAR(CURDATE()) '
        'GROUP BY wc.name',
        (company_id,)
    )
    data = [{'name': r['name'], 'value': float(r['total'])} for r in rows]
    return jsonify({'success': True, 'data': data})
