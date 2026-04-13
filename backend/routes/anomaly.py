import math
from flask import Blueprint, request, session, render_template, jsonify
from backend.utils.db import query_db
from backend.utils.auth_helper import login_required, role_required, get_accessible_store_ids

anomaly_bp = Blueprint('anomaly', __name__)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _zscore_anomalies(records, value_key, label_fn, threshold=2.0):
    """Return anomaly dicts for records whose value_key deviates > threshold σ."""
    values = [float(r[value_key] or 0) for r in records]
    if len(values) < 3:
        return []

    n    = len(values)
    mean = sum(values) / n
    std  = math.sqrt(sum((v - mean) ** 2 for v in values) / n)
    if std == 0:
        return []

    anomalies = []
    for r, v in zip(records, values):
        z = (v - mean) / std
        if abs(z) >= threshold:
            severity = 'high' if abs(z) >= 3.0 else 'medium'
            anomalies.append({
                'record_id':   r['id'],
                'label':       label_fn(r),
                'value':       round(v, 2),
                'mean':        round(mean, 2),
                'std':         round(std, 2),
                'z_score':     round(z, 2),
                'severity':    severity,
                'direction':   'above' if z > 0 else 'below',
                'store_name':  r.get('store_name', ''),
                'record_date': str(r.get('record_date', '')),
            })

    anomalies.sort(key=lambda a: abs(a['z_score']), reverse=True)
    return anomalies


# ──────────────────────────────────────────────
# Page
# ──────────────────────────────────────────────

@anomaly_bp.route('/admin/anomaly-detection')
@login_required
@role_required('admin', 'hq_manager', 'region_manager')
def anomaly_page():
    return render_template('anomaly_detection.html')


# ──────────────────────────────────────────────
# API: detect anomalies
# ──────────────────────────────────────────────

@anomaly_bp.route('/api/anomaly/detect')
@login_required
@role_required('admin', 'hq_manager', 'region_manager')
def detect_anomalies():
    """Detect statistical anomalies in carbon and waste records.

    Query params:
      days     - look-back window in days (default 90)
      threshold - Z-score threshold (default 2.0)
    """
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({'success': True, 'carbon': [], 'waste': [], 'summary': {}})

    days      = int(request.args.get('days', 90))
    threshold = float(request.args.get('threshold', 2.0))
    ph        = ','.join(['%s'] * len(store_ids))
    sid       = list(store_ids)

    # ── Carbon records ──────────────────────────────────────
    carbon_rows = query_db(
        'SELECT cr.id, cr.category, cr.activity_value, cr.total_carbon, '
        'cr.record_date, s.name AS store_name, ef.sub_type, ef.unit '
        'FROM carbon_record cr '
        'JOIN store s ON s.id = cr.store_id '
        'LEFT JOIN emission_factor ef ON ef.id = cr.factor_id '
        f'WHERE cr.store_id IN ({ph}) '
        'AND cr.record_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY) '
        'ORDER BY cr.category, cr.record_date',
        sid + [days]
    )

    # Group by category for per-category Z-score
    from collections import defaultdict
    carbon_by_cat = defaultdict(list)
    for r in carbon_rows:
        carbon_by_cat[r['category']].append(r)

    carbon_anomalies = []
    for cat, rows in carbon_by_cat.items():
        carbon_anomalies.extend(
            _zscore_anomalies(
                rows, 'total_carbon',
                lambda r: f"{r['store_name']} | {r['category']} | {r['sub_type']} | {r['record_date']}",
                threshold
            )
        )

    # Also flag zero/negative activity values as rule-based anomalies
    for r in carbon_rows:
        if float(r['activity_value'] or 0) <= 0:
            carbon_anomalies.append({
                'record_id':   r['id'],
                'label':       f"{r['store_name']} | {r['category']} | {r['record_date']}",
                'value':       float(r['activity_value'] or 0),
                'mean':        None, 'std': None, 'z_score': None,
                'severity':    'high',
                'direction':   'rule',
                'store_name':  r['store_name'],
                'record_date': str(r['record_date']),
                'note':        'Zero or negative activity value'
            })

    # ── Waste records ───────────────────────────────────────
    waste_rows = query_db(
        'SELECT wr.id, wc.name AS category, wr.weight_kg, wr.recycled_kg, '
        'wr.record_date, s.name AS store_name '
        'FROM waste_record wr '
        'JOIN waste_category wc ON wc.id = wr.category_id '
        'JOIN store s ON s.id = wr.store_id '
        f'WHERE wr.store_id IN ({ph}) '
        'AND wr.record_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY) '
        'ORDER BY wc.name, wr.record_date',
        sid + [days]
    )

    waste_by_cat = defaultdict(list)
    for r in waste_rows:
        waste_by_cat[r['category']].append(r)

    waste_anomalies = []
    for cat, rows in waste_by_cat.items():
        waste_anomalies.extend(
            _zscore_anomalies(
                rows, 'weight_kg',
                lambda r: f"{r['store_name']} | {r['category']} | {r['record_date']}",
                threshold
            )
        )

    # Flag recycled_kg > weight_kg
    for r in waste_rows:
        if float(r['recycled_kg'] or 0) > float(r['weight_kg'] or 0):
            waste_anomalies.append({
                'record_id':   r['id'],
                'label':       f"{r['store_name']} | {r['category']} | {r['record_date']}",
                'value':       float(r['recycled_kg'] or 0),
                'mean':        None, 'std': None, 'z_score': None,
                'severity':    'high',
                'direction':   'rule',
                'store_name':  r['store_name'],
                'record_date': str(r['record_date']),
                'note':        'Recycled kg exceeds total weight kg'
            })

    carbon_anomalies.sort(key=lambda a: (a['severity'] == 'high', abs(a['z_score'] or 0)), reverse=True)
    waste_anomalies.sort(key=lambda a: (a['severity'] == 'high', abs(a['z_score'] or 0)), reverse=True)

    summary = {
        'carbon_total_records':   len(carbon_rows),
        'carbon_anomalies':       len(carbon_anomalies),
        'waste_total_records':    len(waste_rows),
        'waste_anomalies':        len(waste_anomalies),
        'days':                   days,
        'threshold':              threshold,
    }

    return jsonify({
        'success': True,
        'carbon':  carbon_anomalies[:50],
        'waste':   waste_anomalies[:50],
        'summary': summary
    })
