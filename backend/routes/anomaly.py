"""AI Data Anomaly Detection module.

Two-stage architecture:
    1. Statistical layer  \u2014 per-category Z-score + hard validation rules
       (fast, deterministic, runs every detection request).
    2. AI insight layer    \u2014 DeepSeek LLM produces a per-anomaly root-cause
       hypothesis + recommended audit actions, plus an overall summary
       (only on demand via `enable_ai=1`; falls back to a deterministic
       template when the API is unavailable).

Detected anomalies are persisted into the `anomaly_review` table so they
become trackable work items rather than ephemeral list output. Auditors
can mark each anomaly as Reviewed / False Positive / Resolved; the
human verdict is preserved across re-detection runs.
"""
import math
from collections import defaultdict

from flask import Blueprint, request, session, render_template, jsonify, current_app

from backend.utils.db import query_db, execute_db, insert_db
from backend.utils.auth_helper import (
    login_required, role_required, get_accessible_store_ids,
)
from backend.utils.markdown_helper import render_markdown
from backend.utils.ai_insight import generate_anomaly_insights

anomaly_bp = Blueprint('anomaly', __name__)


# ──────────────────────────────────────────────
# Statistical layer
# ──────────────────────────────────────────────

def _zscore_anomalies(records, value_key, label_fn, threshold=2.0):
    """Flag rows whose `value_key` deviates from the group mean by `threshold` σ."""
    values = [float(r[value_key] or 0) for r in records]
    if len(values) < 3:
        return []

    n    = len(values)
    mean = sum(values) / n
    std  = math.sqrt(sum((v - mean) ** 2 for v in values) / n)
    if std == 0:
        return []

    out = []
    for r, v in zip(records, values):
        z = (v - mean) / std
        if abs(z) >= threshold:
            out.append({
                'record_id':   r['id'],
                'label':       label_fn(r),
                'value':       round(v, 2),
                'mean':        round(mean, 2),
                'std':         round(std, 2),
                'z_score':     round(z, 2),
                'severity':    'high' if abs(z) >= 3.0 else 'medium',
                'direction':   'above' if z > 0 else 'below',
                'store_id':    r.get('store_id'),
                'store_name':  r.get('store_name', ''),
                'record_date': str(r.get('record_date', '')),
                'note':        None,
            })
    out.sort(key=lambda a: abs(a['z_score']), reverse=True)
    return out


# ──────────────────────────────────────────────
# Persistence helpers
# ──────────────────────────────────────────────

def _clamp_decimal(value, abs_max):
    """Clamp `value` to [-abs_max, abs_max]; pass-through for None."""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v != v:        # NaN guard
        return None
    if v >  abs_max: return  abs_max
    if v < -abs_max: return -abs_max
    return v


def _upsert_review(company_id, record_type, anomaly):
    """Insert a new anomaly_review row OR refresh metrics on an existing OPEN one.

    Closed reviews (reviewed / false_positive / resolved) are never overwritten
    so a human verdict survives re-detection.

    Returns (review_id, status).
    """
    existing = query_db(
        'SELECT id, status FROM anomaly_review '
        'WHERE record_type = %s AND record_id = %s',
        (record_type, anomaly['record_id']), one=True
    )

    z_safe = _clamp_decimal(anomaly.get('z_score'), 99999.999)

    if existing:
        if existing['status'] == 'open':
            execute_db(
                'UPDATE anomaly_review SET '
                '  severity = %s, direction = %s, `value` = %s, '
                '  mean_value = %s, std_value = %s, z_score = %s, '
                '  label = %s, note = %s, store_id = %s, record_date = %s, '
                '  detected_at = NOW() '
                'WHERE id = %s',
                (
                    anomaly['severity'],
                    anomaly.get('direction', 'above'),
                    anomaly.get('value'),
                    anomaly.get('mean'),
                    anomaly.get('std'),
                    z_safe,
                    (anomaly.get('label') or '')[:255],
                    (anomaly.get('note') or '')[:255] or None,
                    anomaly.get('store_id'),
                    anomaly.get('record_date') or None,
                    existing['id'],
                )
            )
        return existing['id'], existing['status']

    review_id = insert_db(
        'INSERT INTO anomaly_review '
        '(company_id, record_type, record_id, store_id, record_date, '
        ' severity, direction, `value`, mean_value, std_value, z_score, '
        ' label, note, status) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (
            company_id, record_type, anomaly['record_id'],
            anomaly.get('store_id'),
            anomaly.get('record_date') or None,
            anomaly['severity'],
            anomaly.get('direction', 'above'),
            anomaly.get('value'),
            anomaly.get('mean'),
            anomaly.get('std'),
            z_safe,
            (anomaly.get('label') or '')[:255],
            (anomaly.get('note') or '')[:255] or None,
            'open',
        )
    )
    return review_id, 'open'


def _save_ai_insight(review_id, risk_category, insight_markdown, current_status):
    """Persist AI insight ONLY for open reviews (preserves human-edited notes)."""
    if current_status != 'open' or not insight_markdown:
        return
    execute_db(
        'UPDATE anomaly_review SET risk_category = %s, ai_insight = %s '
        'WHERE id = %s',
        ((risk_category or '')[:64], insight_markdown, review_id)
    )


def _clear_stale_ai_insights(company_id, record_type, keep_review_ids):
    """Clear ai_insight / risk_category from OPEN reviews of this (company, type)
    that are NOT in ``keep_review_ids``. Preserves closed (human-reviewed) rows.

    Called after each AI run so that only the *current* top-N anomalies retain
    AI analysis in the DB — previous top-N items demoted out of the ranking get
    their stale insight stripped.
    """
    if keep_review_ids:
        ph = ','.join(['%s'] * len(keep_review_ids))
        execute_db(
            f'UPDATE anomaly_review '
            f'   SET ai_insight = NULL, risk_category = NULL '
            f' WHERE company_id = %s AND record_type = %s AND status = %s '
            f'   AND id NOT IN ({ph})',
            [company_id, record_type, 'open'] + list(keep_review_ids)
        )
    else:
        # No current top-N → clear all open reviews of this type.
        execute_db(
            'UPDATE anomaly_review '
            '   SET ai_insight = NULL, risk_category = NULL '
            ' WHERE company_id = %s AND record_type = %s AND status = %s',
            (company_id, record_type, 'open')
        )


def _attach_saved_insights(anomalies):
    """Batch-load any previously-persisted ai_insight / risk_category onto anomalies."""
    review_ids = [a['review_id'] for a in anomalies if a.get('review_id')]
    if not review_ids:
        return
    ph = ','.join(['%s'] * len(review_ids))
    rows = query_db(
        f'SELECT id, risk_category, ai_insight FROM anomaly_review WHERE id IN ({ph})',
        review_ids
    )
    by_id = {r['id']: r for r in rows}
    for a in anomalies:
        row = by_id.get(a.get('review_id'))
        if row and row.get('ai_insight'):
            a['risk_category']    = row.get('risk_category') or ''
            a['ai_insight']       = row['ai_insight']
            a['ai_insight_html']  = render_markdown(row['ai_insight'])


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
    """Detect, persist, optionally enrich with LLM insight, and return.

    Query params:
        days       \u2014 look-back window (default 90)
        threshold  \u2014 z-score threshold (default 2.0)
        enable_ai  \u2014 '1' / 'true' to call DeepSeek for top-N (default off)
    """
    try:
        return _detect_anomalies_impl()
    except Exception as exc:
        current_app.logger.exception('[anomaly] detect failed')
        return jsonify({
            'success': False,
            'message': f'{type(exc).__name__}: {exc}',
        }), 500


def _detect_anomalies_impl():
    store_ids = get_accessible_store_ids()
    if not store_ids:
        return jsonify({
            'success': True, 'carbon': [], 'waste': [],
            'summary': {
                'carbon_total_records': 0, 'carbon_anomalies': 0,
                'waste_total_records':  0, 'waste_anomalies':  0,
                'days': 0, 'threshold': 0, 'enable_ai': False,
                'used_llm': False, 'overall_summary_html': '',
            },
        })

    days       = int(request.args.get('days', 90))
    threshold  = float(request.args.get('threshold', 2.0))
    enable_ai  = request.args.get('enable_ai', '').lower() in ('1', 'true', 'yes')
    company_id = session.get('company_id')

    ph  = ','.join(['%s'] * len(store_ids))
    sid = list(store_ids)

    # ── Carbon records ────────────────────────────────────────
    carbon_rows = query_db(
        'SELECT cr.id, cr.store_id, cr.category, cr.activity_value, cr.total_carbon, '
        '       cr.record_date, s.name AS store_name, ef.sub_type, ef.unit '
        'FROM carbon_record cr '
        'JOIN store s ON s.id = cr.store_id '
        'LEFT JOIN emission_factor ef ON ef.id = cr.factor_id '
        f'WHERE cr.store_id IN ({ph}) '
        '  AND cr.record_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY) '
        'ORDER BY cr.category, cr.record_date',
        sid + [days]
    )

    carbon_by_cat = defaultdict(list)
    for r in carbon_rows:
        carbon_by_cat[r['category']].append(r)

    carbon_anomalies = []
    for _cat, rows in carbon_by_cat.items():
        carbon_anomalies.extend(_zscore_anomalies(
            rows, 'total_carbon',
            lambda r: f"{r['store_name']} | {r['category']} | "
                      f"{r.get('sub_type') or '-'} | {r['record_date']}",
            threshold,
        ))

    # Hard rule: zero or negative activity value
    for r in carbon_rows:
        if float(r['activity_value'] or 0) <= 0:
            carbon_anomalies.append({
                'record_id':   r['id'],
                'label':       f"{r['store_name']} | {r['category']} | {r['record_date']}",
                'value':       float(r['activity_value'] or 0),
                'mean':        None, 'std': None, 'z_score': None,
                'severity':    'high',
                'direction':   'rule',
                'store_id':    r['store_id'],
                'store_name':  r['store_name'],
                'record_date': str(r['record_date']),
                'note':        'Zero or negative activity value',
            })

    # ── Waste records ─────────────────────────────────────────
    waste_rows = query_db(
        'SELECT wr.id, wr.store_id, wc.name AS category, wr.weight_kg, wr.recycled_kg, '
        '       wr.record_date, s.name AS store_name '
        'FROM waste_record wr '
        'JOIN waste_category wc ON wc.id = wr.category_id '
        'JOIN store s ON s.id = wr.store_id '
        f'WHERE wr.store_id IN ({ph}) '
        '  AND wr.record_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY) '
        'ORDER BY wc.name, wr.record_date',
        sid + [days]
    )

    waste_by_cat = defaultdict(list)
    for r in waste_rows:
        waste_by_cat[r['category']].append(r)

    waste_anomalies = []
    for _cat, rows in waste_by_cat.items():
        waste_anomalies.extend(_zscore_anomalies(
            rows, 'weight_kg',
            lambda r: f"{r['store_name']} | {r['category']} | {r['record_date']}",
            threshold,
        ))

    # Hard rule: recycled > total weight
    for r in waste_rows:
        if float(r['recycled_kg'] or 0) > float(r['weight_kg'] or 0):
            waste_anomalies.append({
                'record_id':   r['id'],
                'label':       f"{r['store_name']} | {r['category']} | {r['record_date']}",
                'value':       float(r['recycled_kg'] or 0),
                'mean':        None, 'std': None, 'z_score': None,
                'severity':    'high',
                'direction':   'rule',
                'store_id':    r['store_id'],
                'store_name':  r['store_name'],
                'record_date': str(r['record_date']),
                'note':        'Recycled kg exceeds total weight kg',
            })

    # ── Sort: high severity first, then |z|
    def _key(a):
        return (a['severity'] == 'high', abs(a['z_score'] or 0))
    carbon_anomalies.sort(key=_key, reverse=True)
    waste_anomalies.sort(key=_key, reverse=True)

    # Cap to top 50 of each list to keep payload manageable
    carbon_anomalies = carbon_anomalies[:50]
    waste_anomalies  = waste_anomalies[:50]

    # ── Persist + attach review_id / status
    for a in carbon_anomalies:
        rid, status = _upsert_review(company_id, 'carbon', a)
        a['review_id'], a['review_status'] = rid, status
    for a in waste_anomalies:
        rid, status = _upsert_review(company_id, 'waste', a)
        a['review_id'], a['review_status'] = rid, status

    # ── Only top 3 of each category receive AI insight enrichment; this keeps
    #    the UI consistent (exactly the highlighted rows are expandable).
    AI_TOP_N   = 3
    top_carbon = carbon_anomalies[:AI_TOP_N]
    top_waste  = waste_anomalies[:AI_TOP_N]

    # Attach any previously-saved AI insight ONLY to the current top-N rows.
    # Rows that were top-N in the past but are no longer will simply have no
    # ai_insight_html attached, so the frontend shows a "—" dash (no chevron).
    _attach_saved_insights(top_carbon)
    _attach_saved_insights(top_waste)

    # ── Optional fresh LLM enrichment: top 3 of EACH section (up to 6 total)
    overall_summary = ''
    used_llm        = False
    if enable_ai:
        # Tag each top item with its type and a synthetic uid so the LLM result
        # can be unambiguously routed back even when carbon_record.id and
        # waste_record.id collide.

        def _payload(a, kind):
            return {
                'record_id':   f'{kind[0]}-{a["record_id"]}',  # e.g. "c-123" / "w-45"
                'type':        kind,
                'store':       a['store_name'],
                'date':        a['record_date'],
                'value':       a['value'],
                'mean':        a['mean'],
                'std':         a['std'],
                'z_score':     a['z_score'],
                'severity':    a['severity'],
                'direction':   a['direction'],
                'note':        a.get('note'),
            }

        prompt_payload = (
            [_payload(a, 'carbon') for a in top_carbon] +
            [_payload(a, 'waste')  for a in top_waste]
        )

        result          = generate_anomaly_insights(prompt_payload, top_n=6)
        overall_summary = result['summary']
        used_llm        = result['used_llm']
        per_record      = result['per_record_insight']

        # Route insights back to the correct list using the type prefix.
        lookup = {}
        for a in top_carbon:
            lookup[f'c-{a["record_id"]}'] = a
        for a in top_waste:
            lookup[f'w-{a["record_id"]}'] = a

        for rid, ins in per_record.items():
            anom = lookup.get(str(rid))
            if not anom:
                continue
            anom['risk_category']    = ins.get('risk_category', '')
            anom['ai_insight']       = ins.get('insight_markdown', '')
            anom['ai_insight_html']  = render_markdown(anom['ai_insight'])
            _save_ai_insight(
                anom['review_id'],
                anom['risk_category'],
                anom['ai_insight'],
                anom['review_status'],
            )

        # Purge any stale AI insights from open reviews that are no longer in
        # the current top-N ranking — keeps the "only top 3 are expandable"
        # invariant consistent in the DB.
        _clear_stale_ai_insights(
            company_id, 'carbon',
            [a['review_id'] for a in top_carbon if a.get('review_id')],
        )
        _clear_stale_ai_insights(
            company_id, 'waste',
            [a['review_id'] for a in top_waste  if a.get('review_id')],
        )

    summary = {
        'carbon_total_records': len(carbon_rows),
        'carbon_anomalies':     len(carbon_anomalies),
        'waste_total_records':  len(waste_rows),
        'waste_anomalies':      len(waste_anomalies),
        'days':                 days,
        'threshold':            threshold,
        'enable_ai':            enable_ai,
        'used_llm':             used_llm,
        'overall_summary_html': render_markdown(overall_summary),
    }

    return jsonify({
        'success': True,
        'carbon':  carbon_anomalies,
        'waste':   waste_anomalies,
        'summary': summary,
    })


# ──────────────────────────────────────────────
# API: review actions
# ──────────────────────────────────────────────

@anomaly_bp.route('/api/anomaly/review/<int:review_id>', methods=['POST'])
@login_required
@role_required('admin', 'hq_manager', 'region_manager')
def update_review(review_id):
    """Mark an anomaly review as open / reviewed / false_positive / resolved."""
    data   = request.get_json() or {}
    status = data.get('status')
    notes  = (data.get('notes') or '').strip()

    if status not in ('open', 'reviewed', 'false_positive', 'resolved'):
        return jsonify({'success': False, 'message': 'Invalid status'}), 400

    company_id = session.get('company_id')
    review = query_db(
        'SELECT id FROM anomaly_review WHERE id = %s AND company_id = %s',
        (review_id, company_id), one=True
    )
    if not review:
        return jsonify({'success': False, 'message': 'Review not found'}), 404

    if status == 'open':
        execute_db(
            'UPDATE anomaly_review SET status = %s, '
            '  review_notes = %s, reviewed_by = NULL, reviewed_at = NULL '
            'WHERE id = %s',
            (status, notes or None, review_id)
        )
    else:
        execute_db(
            'UPDATE anomaly_review SET status = %s, review_notes = %s, '
            '  reviewed_by = %s, reviewed_at = NOW() '
            'WHERE id = %s',
            (status, notes or None, session.get('user_id'), review_id)
        )

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session.get('user_id'), 'UPDATE', 'anomaly_review', review_id,
         f'Set anomaly review #{review_id} status to {status}', request.remote_addr)
    )
    return jsonify({'success': True, 'message': f'Marked as {status}'})


@anomaly_bp.route('/api/anomaly/reviews')
@login_required
@role_required('admin', 'hq_manager', 'region_manager')
def list_reviews():
    """Return persisted anomaly reviews for the current company."""
    company_id    = session.get('company_id')
    status_filter = request.args.get('status')
    limit         = int(request.args.get('limit', 100))

    sql = (
        'SELECT ar.*, u.display_name AS reviewed_by_name, s.name AS store_name '
        'FROM anomaly_review ar '
        'LEFT JOIN `user`  u ON u.id = ar.reviewed_by '
        'LEFT JOIN store   s ON s.id = ar.store_id '
        'WHERE ar.company_id = %s '
    )
    params = [company_id]
    if status_filter:
        sql += 'AND ar.status = %s '
        params.append(status_filter)
    sql += 'ORDER BY ar.detected_at DESC LIMIT %s'
    params.append(limit)

    rows = query_db(sql, params)
    for r in rows:
        r['detected_at']     = str(r['detected_at']) if r['detected_at'] else None
        r['reviewed_at']     = str(r['reviewed_at']) if r['reviewed_at'] else None
        r['record_date']     = str(r['record_date']) if r['record_date'] else None
        r['ai_insight_html'] = render_markdown(r.get('ai_insight'))
    return jsonify({'success': True, 'data': rows})
