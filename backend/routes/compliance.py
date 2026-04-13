"""
Compliance Scoring Module
Calculates a multi-dimensional ESG compliance score for the company's
accessible stores, based on:
  - Carbon data completeness & intensity
  - Waste management & recycling rate
  - Sustainability training coverage
  - Reporting frequency
  - Alert resolution rate

Score is 0–100 and broken into five weighted dimensions.
"""
import math
from datetime import datetime, date
from flask import Blueprint, request, session, render_template, jsonify
from backend.utils.db import query_db
from backend.utils.auth_helper import login_required, role_required, get_accessible_store_ids

compliance_bp = Blueprint('compliance', __name__)


def _clamp(value, lo=0, hi=100):
    return max(lo, min(hi, value))


def _score_carbon(store_ids, year):
    """
    Carbon dimension (30 pts):
      - Data completeness:  stores with ≥1 carbon record / total stores × 15
      - Intensity score:    penalise if average carbon/store > 2000 kgCO2e/month
    """
    if not store_ids:
        return 0, {}
    ph  = ','.join(['%s'] * len(store_ids))
    sid = list(store_ids)

    stores_with_data = query_db(
        f'SELECT COUNT(DISTINCT store_id) AS cnt FROM carbon_record '
        f'WHERE store_id IN ({ph}) AND YEAR(record_date) = %s',
        sid + [year], one=True
    )
    completeness_score = int(stores_with_data['cnt'] / max(len(store_ids), 1) * 15)

    avg_monthly = query_db(
        f'SELECT AVG(monthly) AS avg FROM ('
        f'  SELECT MONTH(record_date) AS m, SUM(total_carbon) AS monthly '
        f'  FROM carbon_record WHERE store_id IN ({ph}) AND YEAR(record_date) = %s '
        f'  GROUP BY m'
        f') sub',
        sid + [year], one=True
    )
    avg = float(avg_monthly['avg'] or 0)
    intensity_score = _clamp(int(15 - (avg / 2000) * 15), 0, 15)

    total = _clamp(completeness_score + intensity_score, 0, 30)
    detail = {
        'completeness_score': completeness_score,
        'intensity_score':    intensity_score,
        'avg_monthly_carbon': round(avg, 1),
        'stores_with_data':   stores_with_data['cnt'],
        'total_stores':       len(store_ids),
    }
    return total, detail


def _score_waste(store_ids, year):
    """
    Waste dimension (25 pts):
      - Recycling rate ≥ 60 % → full 15 pts; scales linearly below
      - Stores with waste data completeness × 10 pts
    """
    if not store_ids:
        return 0, {}
    ph  = ','.join(['%s'] * len(store_ids))
    sid = list(store_ids)

    agg = query_db(
        f'SELECT SUM(weight_kg) AS total, SUM(recycled_kg) AS recycled '
        f'FROM waste_record WHERE store_id IN ({ph}) AND YEAR(record_date) = %s',
        sid + [year], one=True
    )
    total_w   = float(agg['total']   or 0)
    recycled  = float(agg['recycled'] or 0)
    rate      = recycled / total_w * 100 if total_w > 0 else 0
    recycle_score = _clamp(int(rate / 60 * 15), 0, 15)

    stores_with_waste = query_db(
        f'SELECT COUNT(DISTINCT store_id) AS cnt FROM waste_record '
        f'WHERE store_id IN ({ph}) AND YEAR(record_date) = %s',
        sid + [year], one=True
    )
    data_score = int(stores_with_waste['cnt'] / max(len(store_ids), 1) * 10)

    total = _clamp(recycle_score + data_score, 0, 25)
    detail = {
        'recycling_rate':     round(rate, 1),
        'recycle_score':      recycle_score,
        'data_completeness':  data_score,
        'stores_with_waste':  stores_with_waste['cnt'],
    }
    return total, detail


def _score_training(store_ids, year):
    """
    Training dimension (20 pts):
      - Unique trainees / total staff (from stores) × 20
    """
    if not store_ids:
        return 0, {}
    ph  = ','.join(['%s'] * len(store_ids))
    sid = list(store_ids)

    try:
        trainees = query_db(
            f'SELECT COUNT(DISTINCT trainee_user_id) AS cnt FROM training_record '
            f'WHERE store_id IN ({ph}) AND YEAR(completion_date) = %s AND status = "completed"',
            sid + [year], one=True
        )
        trained = trainees['cnt'] if trainees else 0
    except Exception:
        return 0, {'note': 'Training table not yet created'}

    total_staff = query_db(
        f'SELECT COUNT(*) AS cnt FROM `user` WHERE store_id IN ({ph})',
        sid, one=True
    )
    staff = total_staff['cnt'] if total_staff else 0
    training_score = _clamp(int(trained / max(staff, 1) * 20), 0, 20) if staff else 0

    detail = {
        'trained_staff':  trained,
        'total_staff':    staff,
        'training_score': training_score,
    }
    return training_score, detail


def _score_reporting(company_id, year):
    """
    Reporting dimension (15 pts):
      - Reports generated this year; target ≥ 4 quarterly reports
    """
    reports = query_db(
        'SELECT COUNT(*) AS cnt FROM report WHERE company_id = %s AND YEAR(created_at) = %s',
        (company_id, year), one=True
    )
    cnt   = reports['cnt'] if reports else 0
    score = _clamp(int(cnt / 4 * 15), 0, 15)
    return score, {'reports_this_year': cnt, 'target': 4}


def _score_alerts(store_ids):
    """
    Alert resolution dimension (10 pts):
      - Resolved alerts / total alerts × 10
    """
    if not store_ids:
        return 0, {}
    ph  = ','.join(['%s'] * len(store_ids))
    sid = list(store_ids)

    agg = query_db(
        f'SELECT COUNT(*) AS total, SUM(is_resolved) AS resolved '
        f'FROM alert WHERE store_id IN ({ph})',
        sid, one=True
    )
    total    = int(agg['total']    or 0)
    resolved = int(agg['resolved'] or 0)
    rate     = resolved / total * 100 if total > 0 else 100
    score    = _clamp(int(rate / 100 * 10), 0, 10)
    return score, {'total_alerts': total, 'resolved': resolved, 'resolution_rate': round(rate, 1)}


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@compliance_bp.route('/compliance')
@login_required
@role_required('admin', 'hq_manager', 'region_manager')
def compliance_page():
    return render_template('compliance.html')


@compliance_bp.route('/api/compliance/score')
@login_required
@role_required('admin', 'hq_manager', 'region_manager')
def compliance_score():
    """Calculate and return the ESG compliance scorecard."""
    store_ids  = get_accessible_store_ids()
    company_id = session['company_id']
    year       = int(request.args.get('year', datetime.now().year))

    c_score, c_detail = _score_carbon(store_ids, year)
    w_score, w_detail = _score_waste(store_ids, year)
    t_score, t_detail = _score_training(store_ids, year)
    r_score, r_detail = _score_reporting(company_id, year)
    a_score, a_detail = _score_alerts(store_ids)

    total = c_score + w_score + t_score + r_score + a_score

    if total >= 85:
        grade, grade_color = 'A', '#198754'
    elif total >= 70:
        grade, grade_color = 'B', '#0d6efd'
    elif total >= 55:
        grade, grade_color = 'C', '#ffc107'
    elif total >= 40:
        grade, grade_color = 'D', '#fd7e14'
    else:
        grade, grade_color = 'F', '#dc3545'

    return jsonify({
        'success': True,
        'year': year,
        'total': total,
        'grade': grade,
        'grade_color': grade_color,
        'dimensions': [
            {
                'name':   'Carbon Management',
                'icon':   'bi-cloud-haze',
                'color':  '#dc3545',
                'score':  c_score,
                'max':    30,
                'pct':    round(c_score / 30 * 100),
                'detail': c_detail
            },
            {
                'name':   'Waste & Recycling',
                'icon':   'bi-recycle',
                'color':  '#198754',
                'score':  w_score,
                'max':    25,
                'pct':    round(w_score / 25 * 100),
                'detail': w_detail
            },
            {
                'name':   'Staff Training',
                'icon':   'bi-mortarboard',
                'color':  '#6f42c1',
                'score':  t_score,
                'max':    20,
                'pct':    round(t_score / 20 * 100),
                'detail': t_detail
            },
            {
                'name':   'Reporting Frequency',
                'icon':   'bi-file-earmark-text',
                'color':  '#0d6efd',
                'score':  r_score,
                'max':    15,
                'pct':    round(r_score / 15 * 100),
                'detail': r_detail
            },
            {
                'name':   'Alert Resolution',
                'icon':   'bi-bell-fill',
                'color':  '#fd7e14',
                'score':  a_score,
                'max':    10,
                'pct':    round(a_score / 10 * 100),
                'detail': a_detail
            },
        ]
    })
