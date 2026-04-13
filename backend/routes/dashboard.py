from flask import Blueprint, render_template, session, jsonify, request
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


@dashboard_bp.route('/api/dashboard/drilldown')
@login_required
def dashboard_drilldown():
    """Drilldown: return store-level breakdown for a given dimension.

    Query params:
      type = 'carbon_category' | 'carbon_month' | 'waste_category'
      category = category name  (for carbon_category / waste_category)
      month    = month number   (for carbon_month)
    """
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': [], 'title': 'No Data'})

    ph = ','.join(['%s'] * len(store_ids))
    sid = list(store_ids)
    drill_type = request.args.get('type', '')
    category   = request.args.get('category', '')
    month      = request.args.get('month', '')

    if drill_type == 'carbon_category' and category:
        rows = query_db(
            'SELECT s.name AS store_name, SUM(cr.total_carbon) AS total '
            'FROM carbon_record cr '
            'JOIN store s ON s.id = cr.store_id '
            f'WHERE cr.store_id IN ({ph}) '
            'AND cr.category = %s AND YEAR(cr.record_date) = YEAR(CURDATE()) '
            'GROUP BY s.name ORDER BY total DESC LIMIT 15',
            sid + [category]
        )
        title = f'Carbon – {category} (by Store)'
        unit  = 'kgCO2e'

    elif drill_type == 'carbon_month' and month:
        rows = query_db(
            'SELECT s.name AS store_name, SUM(cr.total_carbon) AS total '
            'FROM carbon_record cr '
            'JOIN store s ON s.id = cr.store_id '
            f'WHERE cr.store_id IN ({ph}) '
            'AND MONTH(cr.record_date) = %s AND YEAR(cr.record_date) = YEAR(CURDATE()) '
            'GROUP BY s.name ORDER BY total DESC LIMIT 15',
            sid + [int(month)]
        )
        month_names = ['Jan','Feb','Mar','Apr','May','Jun',
                       'Jul','Aug','Sep','Oct','Nov','Dec']
        mname = month_names[int(month) - 1] if month.isdigit() else month
        title = f'Carbon Emissions – {mname} (by Store)'
        unit  = 'kgCO2e'

    elif drill_type == 'waste_category' and category:
        rows = query_db(
            'SELECT s.name AS store_name, SUM(wr.weight_kg) AS total '
            'FROM waste_record wr '
            'JOIN waste_category wc ON wc.id = wr.category_id '
            'JOIN store s ON s.id = wr.store_id '
            f'WHERE wr.store_id IN ({ph}) '
            'AND wc.name = %s AND YEAR(wr.record_date) = YEAR(CURDATE()) '
            'GROUP BY s.name ORDER BY total DESC LIMIT 15',
            sid + [category]
        )
        title = f'Waste – {category} (by Store)'
        unit  = 'kg'

    else:
        return jsonify({'success': False, 'message': 'Invalid drilldown parameters'}), 400

    data = [{'store': r['store_name'], 'value': float(r['total'] or 0)} for r in rows]
    return jsonify({'success': True, 'title': title, 'unit': unit, 'data': data})


@dashboard_bp.route('/api/dashboard/sdg12')
@login_required
def dashboard_sdg12():
    """Return SDG 12 sub-indicator scores for the current user's accessible stores."""
    store_ids  = get_accessible_store_ids()
    company_id = session.get('company_id')
    if not store_ids:
        return jsonify({'success': True, 'data': {
            'recovery': 0, 'carbon': 0, 'reporting': 0, 'coverage': 0
        }})

    ph  = ','.join(['%s'] * len(store_ids))
    sid = list(store_ids)

    # 12.5 – Waste recovery rate (target ≥ 60 %)
    waste = query_db(
        f'SELECT SUM(weight_kg) AS total, SUM(recycled_kg) AS recycled '
        f'FROM waste_record WHERE store_id IN ({ph}) AND YEAR(record_date) = YEAR(CURDATE())',
        sid, one=True
    )
    total_w  = float(waste['total']   or 0)
    recycled = float(waste['recycled'] or 0)
    rate     = recycled / total_w * 100 if total_w > 0 else 0
    recovery_score = min(int(round(rate / 60 * 100)), 100)

    # 12.2 – Carbon efficiency (lower carbon/store = better; 50 kgCO2e/month target)
    carbon = query_db(
        f'SELECT SUM(total_carbon) AS total FROM carbon_record '
        f'WHERE store_id IN ({ph}) AND YEAR(record_date) = YEAR(CURDATE())',
        sid, one=True
    )
    total_c = float(carbon['total'] or 0)
    per_store = total_c / max(len(store_ids), 1)
    carbon_score = max(0, min(100, int(round(100 - per_store / 50))))

    # 12.6 – Sustainability reporting (target ≥ 4 reports/year)
    rpt = query_db(
        'SELECT COUNT(*) AS cnt FROM report WHERE company_id = %s AND YEAR(created_at) = YEAR(CURDATE())',
        (company_id,), one=True
    )
    reporting_score = min(int((rpt['cnt'] if rpt else 0) / 4 * 100), 100)

    # 12.3 – Store data coverage (stores with any waste record / total stores)
    with_data = query_db(
        f'SELECT COUNT(DISTINCT store_id) AS cnt FROM waste_record '
        f'WHERE store_id IN ({ph}) AND YEAR(record_date) = YEAR(CURDATE())',
        sid, one=True
    )
    coverage_score = min(int(round((with_data['cnt'] if with_data else 0) / max(len(store_ids), 1) * 100)), 100)

    return jsonify({'success': True, 'data': {
        'recovery':  recovery_score,
        'carbon':    carbon_score,
        'reporting': reporting_score,
        'coverage':  coverage_score,
        'rate_raw':  round(rate, 1),
        'report_count': rpt['cnt'] if rpt else 0,
    }})


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
