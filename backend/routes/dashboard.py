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


# ──────────────────────────────────────────────────────────────────────
# Role-specific dashboard widgets
# ──────────────────────────────────────────────────────────────────────

@dashboard_bp.route('/api/dashboard/staff-view')
@login_required
def staff_view():
    """Store-staff dashboard widget: own store's this-month KPIs + open alerts."""
    store_id = session.get('store_id')
    if not store_id:
        return jsonify({'success': False, 'message': 'No store assigned'}), 400

    # This month carbon + waste + recycling
    this_month = query_db(
        'SELECT COALESCE(SUM(total_carbon), 0) AS total '
        'FROM carbon_record WHERE store_id = %s '
        'AND YEAR(record_date) = YEAR(CURDATE()) AND MONTH(record_date) = MONTH(CURDATE())',
        (store_id,), one=True
    )
    last_month = query_db(
        'SELECT COALESCE(SUM(total_carbon), 0) AS total '
        'FROM carbon_record WHERE store_id = %s '
        'AND record_date >= DATE_SUB(DATE_FORMAT(CURDATE(),"%%Y-%%m-01"), INTERVAL 1 MONTH) '
        'AND record_date <  DATE_FORMAT(CURDATE(),"%%Y-%%m-01")',
        (store_id,), one=True
    )
    waste = query_db(
        'SELECT COALESCE(SUM(weight_kg),0) AS total, COALESCE(SUM(recycled_kg),0) AS recycled '
        'FROM waste_record WHERE store_id = %s '
        'AND YEAR(record_date) = YEAR(CURDATE()) AND MONTH(record_date) = MONTH(CURDATE())',
        (store_id,), one=True
    )

    c_now  = float(this_month['total'] or 0)
    c_prev = float(last_month['total'] or 0)
    mom_pct = round((c_now - c_prev) / c_prev * 100, 1) if c_prev > 0 else None

    w_total    = float(waste['total']    or 0)
    w_recycled = float(waste['recycled'] or 0)
    recycle_rate = round(w_recycled / w_total * 100, 1) if w_total > 0 else 0

    # Open alerts (unread) for this store — column aliases keep JSON API stable
    alerts = query_db(
        'SELECT id, '
        '  metric_type     AS alert_type, '
        '  current_value   AS actual_value, '
        '  threshold_value, '
        '  triggered_at    AS created_at '
        'FROM alert_log WHERE store_id = %s AND is_read = 0 '
        'ORDER BY triggered_at DESC LIMIT 5',
        (store_id,)
    )
    for a in alerts:
        a['created_at'] = str(a['created_at']) if a['created_at'] else None
        a['actual_value']    = float(a['actual_value']    or 0)
        a['threshold_value'] = float(a['threshold_value'] or 0)

    open_alerts_total = query_db(
        'SELECT COUNT(*) AS cnt FROM alert_log WHERE store_id = %s AND is_read = 0',
        (store_id,), one=True
    )['cnt']

    # Store name for header
    store = query_db('SELECT name, city FROM store WHERE id = %s', (store_id,), one=True)

    return jsonify({'success': True, 'data': {
        'store_name':   store['name'] if store else '—',
        'store_city':   store['city'] if store else '',
        'carbon_this_month': round(c_now, 2),
        'carbon_last_month': round(c_prev, 2),
        'carbon_mom_pct':    mom_pct,
        'waste_this_month':  round(w_total, 2),
        'recycle_rate':      recycle_rate,
        'open_alerts_count': open_alerts_total,
        'recent_alerts':     alerts,
    }})


@dashboard_bp.route('/api/dashboard/region-leaderboard')
@login_required
def region_leaderboard():
    """Region-manager dashboard: store ranking by recycling rate and carbon (YTD)."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': {'recycling': [], 'carbon': []}})

    ph  = ','.join(['%s'] * len(store_ids))
    sid = list(store_ids)

    # Best & worst recycling rate (YTD)
    recycling = query_db(
        f'SELECT s.id, s.name AS store_name, r.name AS region_name, '
        f'  SUM(wr.weight_kg) AS total_kg, '
        f'  SUM(wr.recycled_kg) AS recycled_kg, '
        f'  ROUND(SUM(wr.recycled_kg) / NULLIF(SUM(wr.weight_kg),0) * 100, 1) AS rate '
        f'FROM store s '
        f'LEFT JOIN region r ON r.id = s.region_id '
        f'LEFT JOIN waste_record wr ON wr.store_id = s.id '
        f'  AND YEAR(wr.record_date) = YEAR(CURDATE()) '
        f'WHERE s.id IN ({ph}) '
        f'GROUP BY s.id, s.name, r.name '
        f'ORDER BY rate DESC',
        sid
    )
    # Convert / fill nulls
    for r in recycling:
        r['total_kg']    = float(r['total_kg']    or 0)
        r['recycled_kg'] = float(r['recycled_kg'] or 0)
        r['rate']        = float(r['rate']        or 0)

    # Highest carbon (YTD)
    carbon = query_db(
        f'SELECT s.id, s.name AS store_name, r.name AS region_name, '
        f'  COALESCE(SUM(cr.total_carbon), 0) AS total_carbon '
        f'FROM store s '
        f'LEFT JOIN region r ON r.id = s.region_id '
        f'LEFT JOIN carbon_record cr ON cr.store_id = s.id '
        f'  AND YEAR(cr.record_date) = YEAR(CURDATE()) '
        f'WHERE s.id IN ({ph}) '
        f'GROUP BY s.id, s.name, r.name '
        f'ORDER BY total_carbon DESC',
        sid
    )
    for c in carbon:
        c['total_carbon'] = float(c['total_carbon'] or 0)

    return jsonify({'success': True, 'data': {
        'recycling': recycling,
        'carbon':    carbon,
    }})


@dashboard_bp.route('/api/dashboard/risk-watch')
@login_required
def risk_watch():
    """HQ-manager dashboard: high-risk stores (open alerts ≥ 3 / no data this month / carbon spike)."""
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': {
            'high_alert_stores': [], 'silent_stores': [], 'spike_stores': []
        }})

    ph  = ','.join(['%s'] * len(store_ids))
    sid = list(store_ids)

    # Stores with ≥3 unread alerts
    high_alert = query_db(
        f'SELECT s.id, s.name AS store_name, r.name AS region_name, '
        f'  COUNT(al.id) AS open_alerts '
        f'FROM store s '
        f'LEFT JOIN region r ON r.id = s.region_id '
        f'JOIN alert_log al ON al.store_id = s.id AND al.is_read = 0 '
        f'WHERE s.id IN ({ph}) '
        f'GROUP BY s.id, s.name, r.name '
        f'HAVING open_alerts >= 3 '
        f'ORDER BY open_alerts DESC LIMIT 10',
        sid
    )

    # Stores with no records this month (either carbon or waste)
    silent = query_db(
        f'SELECT s.id, s.name AS store_name, r.name AS region_name '
        f'FROM store s '
        f'LEFT JOIN region r ON r.id = s.region_id '
        f'WHERE s.id IN ({ph}) '
        f'AND s.id NOT IN ( '
        f'  SELECT DISTINCT store_id FROM carbon_record '
        f'  WHERE YEAR(record_date) = YEAR(CURDATE()) '
        f'  AND MONTH(record_date) = MONTH(CURDATE()) '
        f') '
        f'AND s.id NOT IN ( '
        f'  SELECT DISTINCT store_id FROM waste_record '
        f'  WHERE YEAR(record_date) = YEAR(CURDATE()) '
        f'  AND MONTH(record_date) = MONTH(CURDATE()) '
        f') '
        f'ORDER BY s.name LIMIT 10',
        sid
    )

    # Carbon spike: this month vs last month ≥ +30%
    spike = query_db(
        f'SELECT s.id, s.name AS store_name, r.name AS region_name, '
        f'  COALESCE(SUM(CASE WHEN MONTH(cr.record_date)=MONTH(CURDATE()) '
        f'    AND YEAR(cr.record_date)=YEAR(CURDATE()) THEN cr.total_carbon END),0) AS this_month, '
        f'  COALESCE(SUM(CASE WHEN cr.record_date >= DATE_SUB(DATE_FORMAT(CURDATE(),"%%Y-%%m-01"), INTERVAL 1 MONTH) '
        f'    AND cr.record_date < DATE_FORMAT(CURDATE(),"%%Y-%%m-01") THEN cr.total_carbon END),0) AS last_month '
        f'FROM store s '
        f'LEFT JOIN region r ON r.id = s.region_id '
        f'LEFT JOIN carbon_record cr ON cr.store_id = s.id '
        f'WHERE s.id IN ({ph}) '
        f'GROUP BY s.id, s.name, r.name '
        f'HAVING last_month > 0 AND this_month / last_month >= 1.3 '
        f'ORDER BY (this_month / last_month) DESC LIMIT 10',
        sid
    )
    for row in spike:
        row['this_month'] = float(row['this_month'] or 0)
        row['last_month'] = float(row['last_month'] or 0)
        row['change_pct'] = round((row['this_month'] - row['last_month']) / row['last_month'] * 100, 1)

    return jsonify({'success': True, 'data': {
        'high_alert_stores': high_alert,
        'silent_stores':     silent,
        'spike_stores':      spike,
    }})


@dashboard_bp.route('/api/dashboard/system-health')
@login_required
def system_health():
    """Admin-only dashboard: platform health (user activity, record volume, recent audit)."""
    if session.get('role') not in ('admin', 'hq_manager'):
        return jsonify({'success': False, 'message': 'Forbidden'}), 403

    company_id = session.get('company_id')
    is_admin   = session.get('role') == 'admin'

    # User activity (active = logged in within 30 days)
    if is_admin:
        users = query_db(
            'SELECT '
            '  COUNT(*) AS total, '
            '  SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS enabled, '
            '  SUM(CASE WHEN last_login >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) AS active_30d '
            'FROM `user`', one=True
        )
    else:
        users = query_db(
            'SELECT '
            '  COUNT(*) AS total, '
            '  SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS enabled, '
            '  SUM(CASE WHEN last_login >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) AS active_30d '
            'FROM `user` WHERE company_id = %s', (company_id,), one=True
        )

    # Records created today
    company_filter = '' if is_admin else 'WHERE company_id = %s'
    params = () if is_admin else (company_id,)
    carbon_today = query_db(
        f'SELECT COUNT(*) AS cnt FROM carbon_record '
        f'{company_filter}{" AND" if not is_admin else "WHERE"} DATE(created_at) = CURDATE()',
        params, one=True
    )
    waste_today = query_db(
        f'SELECT COUNT(*) AS cnt FROM waste_record '
        f'{company_filter}{" AND" if not is_admin else "WHERE"} DATE(created_at) = CURDATE()',
        params, one=True
    )

    # Total store / company count (admin only)
    stores_total = query_db(
        'SELECT COUNT(*) AS cnt FROM store' if is_admin
        else 'SELECT COUNT(*) AS cnt FROM store WHERE company_id = %s',
        () if is_admin else (company_id,), one=True
    )

    # Latest audit log entries (5 newest)
    if is_admin:
        audit = query_db(
            'SELECT al.id, al.action, al.target_type, al.detail, al.created_at, '
            '  u.display_name AS actor '
            'FROM audit_log al LEFT JOIN `user` u ON u.id = al.user_id '
            'ORDER BY al.created_at DESC LIMIT 5'
        )
    else:
        audit = query_db(
            'SELECT al.id, al.action, al.target_type, al.detail, al.created_at, '
            '  u.display_name AS actor '
            'FROM audit_log al JOIN `user` u ON u.id = al.user_id '
            'WHERE u.company_id = %s '
            'ORDER BY al.created_at DESC LIMIT 5', (company_id,)
        )
    for a in audit:
        a['created_at'] = str(a['created_at']) if a['created_at'] else None

    # AI service availability
    import os
    ai_configured   = bool(os.getenv('DEEPSEEK_API_KEY'))
    mail_configured = bool(os.getenv('MAIL_SERVER'))

    return jsonify({'success': True, 'data': {
        'users_total':      int(users['total']      or 0),
        'users_enabled':    int(users['enabled']    or 0),
        'users_active_30d': int(users['active_30d'] or 0),
        'stores_total':     int(stores_total['cnt'] or 0),
        'carbon_today':     int(carbon_today['cnt'] or 0),
        'waste_today':      int(waste_today['cnt']  or 0),
        'recent_audit':     audit,
        'ai_configured':    ai_configured,
        'mail_configured':  mail_configured,
    }})
