"""
Geographic visualization endpoints.

Provides store-level geocoded data with summary ESG metrics for the
interactive map page. Respects the same role-based access control used
by the rest of the platform (HQ -> all stores, Region -> own region,
Staff -> own store).
"""
from flask import Blueprint, render_template, request, session, jsonify
from backend.utils.db import query_db
from backend.utils.auth_helper import login_required, get_accessible_store_ids


map_bp = Blueprint('map', __name__)


@map_bp.route('/map')
@login_required
def map_page():
    """Render the interactive store map page."""
    return render_template('map.html')


@map_bp.route('/api/map/stores')
@login_required
def map_stores():
    """
    Return geocoded stores accessible to the current user, plus summary
    metrics (carbon emissions YTD, waste recovery rate YTD, alert count).

    Frontend uses these to render markers on a Leaflet map and colour-code
    them by ESG performance.
    """
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'data': [], 'regions': []})

    ph  = ','.join(['%s'] * len(store_ids))
    sid = list(store_ids)

    # ── Stores with coordinates and region info ────────────────────────────
    stores = query_db(
        f'SELECT s.id, s.name, s.city, s.address, s.latitude, s.longitude, '
        f'       s.is_active, r.id AS region_id, r.name AS region_name '
        f'FROM store s '
        f'JOIN region r ON r.id = s.region_id '
        f'WHERE s.id IN ({ph}) AND s.latitude IS NOT NULL AND s.longitude IS NOT NULL '
        f'ORDER BY r.name, s.name',
        sid
    )

    if not stores:
        return jsonify({'success': True, 'data': [], 'regions': []})

    # ── Carbon YTD per store ───────────────────────────────────────────────
    carbon_rows = query_db(
        f'SELECT store_id, COALESCE(SUM(total_carbon), 0) AS total '
        f'FROM carbon_record '
        f'WHERE store_id IN ({ph}) AND YEAR(record_date) = YEAR(CURDATE()) '
        f'GROUP BY store_id',
        sid
    )
    carbon_map = {r['store_id']: float(r['total']) for r in carbon_rows}

    # ── Waste recovery rate YTD per store ──────────────────────────────────
    # ESG-standard "recovery rate" = (diverted from landfill) / (total waste).
    # Anything recycled OR composted counts as diverted.
    waste_rows = query_db(
        f'SELECT store_id, '
        f'       COALESCE(SUM(weight_kg), 0) AS total_waste, '
        f'       COALESCE(SUM(CASE '
        f'           WHEN disposal_method IN (\'recycling\', \'composting\', \'reuse\') '
        f'                THEN weight_kg '
        f'           ELSE recycled_kg '
        f'       END), 0) AS total_recovered '
        f'FROM waste_record '
        f'WHERE store_id IN ({ph}) AND YEAR(record_date) = YEAR(CURDATE()) '
        f'GROUP BY store_id',
        sid
    )
    waste_map = {}
    for r in waste_rows:
        total = float(r['total_waste'])
        recovered = float(r['total_recovered'])
        rate = round(recovered / total * 100, 1) if total > 0 else 0.0
        waste_map[r['store_id']] = {
            'total_waste': total,
            'recovery_rate': rate,
        }

    # ── Open alert count per store ─────────────────────────────────────────
    alert_rows = query_db(
        f'SELECT store_id, COUNT(*) AS cnt FROM alert_log '
        f'WHERE store_id IN ({ph}) AND is_read = 0 '
        f'GROUP BY store_id',
        sid
    )
    alert_map = {r['store_id']: int(r['cnt']) for r in alert_rows}

    # ── Assemble payload + grade colour ────────────────────────────────────
    def _grade(carbon, recovery, alerts):
        """Coarse colour-coding: green (good), amber (warn), red (issue)."""
        if alerts >= 3 or recovery < 30:
            return 'red'
        if recovery < 50 or carbon > 20000:
            return 'amber'
        return 'green'

    data = []
    for s in stores:
        sid_ = s['id']
        carbon = carbon_map.get(sid_, 0.0)
        w = waste_map.get(sid_, {'total_waste': 0.0, 'recovery_rate': 0.0})
        alerts = alert_map.get(sid_, 0)
        data.append({
            'id': sid_,
            'name': s['name'],
            'city': s['city'],
            'address': s['address'] or '',
            'lat': float(s['latitude']),
            'lng': float(s['longitude']),
            'is_active': bool(s['is_active']),
            'region_id': s['region_id'],
            'region_name': s['region_name'],
            'carbon_ytd_kg': round(carbon, 1),
            'waste_total_kg': round(w['total_waste'], 1),
            'recovery_rate': w['recovery_rate'],
            'open_alerts': alerts,
            'grade': _grade(carbon, w['recovery_rate'], alerts),
        })

    # ── Region centroids (for region-level overview view) ──────────────────
    regions = {}
    for d in data:
        rid = d['region_id']
        if rid not in regions:
            regions[rid] = {
                'id': rid,
                'name': d['region_name'],
                'lat_sum': 0.0, 'lng_sum': 0.0,
                'store_count': 0,
                'carbon_total': 0.0,
                'alert_total': 0,
            }
        r = regions[rid]
        r['lat_sum'] += d['lat']
        r['lng_sum'] += d['lng']
        r['store_count'] += 1
        r['carbon_total'] += d['carbon_ytd_kg']
        r['alert_total']  += d['open_alerts']

    region_list = []
    for r in regions.values():
        n = r['store_count']
        region_list.append({
            'id': r['id'],
            'name': r['name'],
            'lat': round(r['lat_sum'] / n, 6),
            'lng': round(r['lng_sum'] / n, 6),
            'store_count': n,
            'carbon_total': round(r['carbon_total'], 1),
            'open_alerts': r['alert_total'],
        })

    return jsonify({
        'success': True,
        'data': data,
        'regions': region_list,
    })


@map_bp.route('/api/map/store-trend')
@login_required
def store_trend():
    """
    Return a single store's monthly carbon & waste trend (current year),
    for rendering a mini sparkline chart inside the map marker popup.
    Access control: store_id must be within the caller's accessible set.
    """
    try:
        store_id = int(request.args.get('store_id', ''))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'invalid store_id'}), 400

    accessible = set(get_accessible_store_ids() or [])
    if store_id not in accessible:
        return jsonify({'success': False, 'error': 'forbidden'}), 403

    # 12-month scaffold so the chart always has full x-axis
    months = list(range(1, 13))

    carbon_rows = query_db(
        'SELECT MONTH(record_date) AS m, COALESCE(SUM(total_carbon), 0) AS total '
        'FROM carbon_record '
        'WHERE store_id = %s AND YEAR(record_date) = YEAR(CURDATE()) '
        'GROUP BY MONTH(record_date)',
        (store_id,)
    )
    carbon_by_month = {int(r['m']): float(r['total']) for r in carbon_rows}

    waste_rows = query_db(
        'SELECT MONTH(record_date) AS m, '
        '       COALESCE(SUM(weight_kg), 0)   AS total, '
        '       COALESCE(SUM(recycled_kg), 0) AS recycled '
        'FROM waste_record '
        'WHERE store_id = %s AND YEAR(record_date) = YEAR(CURDATE()) '
        'GROUP BY MONTH(record_date)',
        (store_id,)
    )
    recycle_by_month = {}
    for r in waste_rows:
        t = float(r['total'])
        rec = float(r['recycled'])
        recycle_by_month[int(r['m'])] = round(rec / t * 100, 1) if t > 0 else 0.0

    return jsonify({
        'success': True,
        'months':   months,
        'carbon':   [round(carbon_by_month.get(m, 0.0), 1) for m in months],
        'recovery': [recycle_by_month.get(m, 0.0) for m in months],
    })
