from flask import Blueprint, render_template, session, jsonify
from backend.utils.db import query_db
from backend.utils.auth_helper import login_required, get_accessible_store_ids

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('dashboard.html')


@dashboard_bp.route('/api/dashboard/summary')
@login_required
def dashboard_summary():
    """Get overview statistics aggregated across accessible stores."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': {
            'carbon_total_kg': 0, 'waste_total_kg': 0,
            'recycling_rate': 0, 'report_count': 0
        }})

    ph = ','.join(['%s'] * len(store_ids))
    sid = list(store_ids)

    carbon_total = query_db(
        f'SELECT COALESCE(SUM(total_carbon), 0) AS total '
        f'FROM carbon_record WHERE store_id IN ({ph}) AND YEAR(record_date) = YEAR(CURDATE())',
        sid, one=True
    )
    waste_total = query_db(
        f'SELECT COALESCE(SUM(weight_kg), 0) AS total '
        f'FROM waste_record WHERE store_id IN ({ph}) AND YEAR(record_date) = YEAR(CURDATE())',
        sid, one=True
    )
    recycled_total = query_db(
        f'SELECT COALESCE(SUM(recycled_kg), 0) AS total '
        f'FROM waste_record WHERE store_id IN ({ph}) AND YEAR(record_date) = YEAR(CURDATE())',
        sid, one=True
    )
    report_count = query_db(
        'SELECT COUNT(*) AS cnt FROM report WHERE company_id = %s',
        (session['company_id'],), one=True
    )

    waste_val  = float(waste_total['total'])
    recyc_val  = float(recycled_total['total'])
    rate = round(recyc_val / waste_val * 100, 1) if waste_val > 0 else 0

    return jsonify({
        'success': True,
        'data': {
            'carbon_total_kg': float(carbon_total['total']),
            'waste_total_kg':  waste_val,
            'recycling_rate':  rate,
            'report_count':    report_count['cnt']
        }
    })


@dashboard_bp.route('/api/dashboard/carbon-trend')
@login_required
def carbon_trend():
    """Monthly carbon emission trend (current year) aggregated across accessible stores."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': {'months': [], 'values': []}})

    ph = ','.join(['%s'] * len(store_ids))
    rows = query_db(
        'SELECT month, SUM(total_carbon_kg) AS total_carbon_kg '
        f'FROM v_carbon_monthly_summary '
        f'WHERE store_id IN ({ph}) AND year = YEAR(CURDATE()) '
        'GROUP BY month ORDER BY month',
        list(store_ids)
    )
    months = [r['month'] for r in rows]
    values = [float(r['total_carbon_kg']) for r in rows]
    return jsonify({'success': True, 'data': {'months': months, 'values': values}})


@dashboard_bp.route('/api/dashboard/carbon-by-category')
@login_required
def carbon_by_category():
    """Carbon emissions breakdown by category (current year) across accessible stores."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': []})

    ph = ','.join(['%s'] * len(store_ids))
    rows = query_db(
        'SELECT category, SUM(total_carbon_kg) AS total '
        f'FROM v_carbon_monthly_summary '
        f'WHERE store_id IN ({ph}) AND year = YEAR(CURDATE()) '
        'GROUP BY category',
        list(store_ids)
    )
    data = [{'name': r['category'], 'value': float(r['total'])} for r in rows]
    return jsonify({'success': True, 'data': data})


@dashboard_bp.route('/api/dashboard/waste-composition')
@login_required
def waste_composition():
    """Waste composition by category (current year) across accessible stores."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': []})

    ph = ','.join(['%s'] * len(store_ids))
    rows = query_db(
        'SELECT wc.name, SUM(wr.weight_kg) AS total '
        'FROM waste_record wr '
        'JOIN waste_category wc ON wc.id = wr.category_id '
        f'WHERE wr.store_id IN ({ph}) AND YEAR(wr.record_date) = YEAR(CURDATE()) '
        'GROUP BY wc.name',
        list(store_ids)
    )
    data = [{'name': r['name'], 'value': float(r['total'])} for r in rows]
    return jsonify({'success': True, 'data': data})


@dashboard_bp.route('/api/dashboard/accessible-stores')
@login_required
def accessible_stores():
    """Return stores the current user can access (used by frontend store selectors)."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': []})

    ph = ','.join(['%s'] * len(store_ids))
    rows = query_db(
        f'SELECT s.id, s.name, s.city, r.name AS region_name '
        f'FROM store s JOIN region r ON r.id = s.region_id '
        f'WHERE s.id IN ({ph}) ORDER BY r.name, s.name',
        list(store_ids)
    )
    return jsonify({'success': True, 'data': rows})
