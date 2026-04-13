"""
backend/utils/alert_checker.py
Real-time alert checking called after every carbon / waste record insertion.
"""

from backend.utils.db import query_db, execute_db
from backend.utils.mail import send_alert_email


def _already_alerted(company_id, store_id, metric_type, year, month):
    """Return True if an unread alert for the same store/metric/month already exists."""
    row = query_db(
        'SELECT id FROM alert_log '
        'WHERE company_id = %s AND store_id = %s AND metric_type = %s '
        'AND YEAR(triggered_at) = %s AND MONTH(triggered_at) = %s '
        'AND is_read = 0 LIMIT 1',
        (company_id, store_id, metric_type, year, month), one=True
    )
    return row is not None


def _insert_alert(company_id, store_id, threshold_id, metric_type,
                  current_value, threshold_value):
    execute_db(
        'INSERT INTO alert_log '
        '(company_id, store_id, threshold_id, metric_type, current_value, threshold_value) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (company_id, store_id, threshold_id, metric_type,
         round(float(current_value), 2), round(float(threshold_value), 2))
    )

    # Send email notification (mock if SMTP not configured)
    try:
        store_row = query_db('SELECT name FROM store WHERE id = %s', (store_id,), one=True)
        store_name = store_row['name'] if store_row else f'Store #{store_id}'
        if threshold_id:
            t_row = query_db(
                'SELECT notify_email FROM alert_threshold WHERE id = %s', (threshold_id,), one=True
            )
            if t_row and t_row.get('notify_email'):
                recipients = [e.strip() for e in t_row['notify_email'].split(',') if e.strip()]
                send_alert_email(recipients, metric_type, store_name,
                                 float(current_value), float(threshold_value))
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error('[alert_checker] email error: %s', exc)


def check_alerts_for_store(company_id, store_id):
    """
    Check all active thresholds against the current store's latest data.
    Called after every carbon_record or waste_record INSERT.
    Inserts into alert_log when a threshold is breached (deduplicates per month).
    """
    thresholds = query_db(
        'SELECT id, metric_type, scope, scope_id, threshold_value, comparison '
        'FROM alert_threshold '
        'WHERE company_id = %s AND is_active = 1',
        (company_id,)
    )

    for t in thresholds:
        metric   = t['metric_type']
        tid      = t['id']
        tval     = float(t['threshold_value'])
        cmp      = t['comparison']
        scope    = t['scope']
        scope_id = t['scope_id']

        # Scope filtering: skip if threshold is for a different store/region
        if scope == 'store' and scope_id and scope_id != store_id:
            continue
        if scope == 'region':
            store_row = query_db(
                'SELECT region_id FROM store WHERE id = %s', (store_id,), one=True
            )
            if store_row and scope_id and store_row['region_id'] != scope_id:
                continue

        if metric == 'waste_recycling_rate':
            _check_waste_recycling_rate(company_id, store_id, tid, tval, cmp)

        elif metric == 'carbon_mom_growth':
            _check_carbon_mom_growth(company_id, store_id, tid, tval, cmp)

        elif metric == 'waste_weight_daily':
            _check_waste_weight_daily(company_id, store_id, tid, tval, cmp)


def _check_waste_recycling_rate(company_id, store_id, threshold_id,
                                threshold_value, comparison):
    """Recycling rate = SUM(recycled_kg) / SUM(weight_kg) for the current month."""
    row = query_db(
        'SELECT YEAR(CURDATE()) AS y, MONTH(CURDATE()) AS m, '
        'SUM(weight_kg) AS total_kg, SUM(recycled_kg) AS recycled_kg '
        'FROM waste_record '
        'WHERE store_id = %s AND YEAR(record_date) = YEAR(CURDATE()) '
        'AND MONTH(record_date) = MONTH(CURDATE())',
        (store_id,), one=True
    )
    if not row or not row['total_kg']:
        return

    rate = float(row['recycled_kg'] or 0) / float(row['total_kg']) * 100
    year, month = row['y'], row['m']

    breached = (comparison == 'lt' and rate < threshold_value) or \
               (comparison == 'gt' and rate > threshold_value)

    if breached and not _already_alerted(
            company_id, store_id, 'waste_recycling_rate', year, month):
        _insert_alert(company_id, store_id, threshold_id,
                      'waste_recycling_rate', rate, threshold_value)


def _check_carbon_mom_growth(company_id, store_id, threshold_id,
                             threshold_value, comparison):
    """MoM carbon growth = (this_month - last_month) / last_month * 100."""
    rows = query_db(
        'SELECT YEAR(record_date) AS y, MONTH(record_date) AS m, '
        'SUM(total_carbon) AS total_carbon '
        'FROM carbon_record '
        'WHERE store_id = %s '
        'AND record_date >= DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), "%%Y-%%m-01") '
        'GROUP BY y, m ORDER BY y, m',
        (store_id,)
    )
    if len(rows) < 2:
        return

    last_month  = float(rows[-2]['total_carbon'] or 0)
    this_month  = float(rows[-1]['total_carbon'] or 0)
    if last_month == 0:
        return

    growth_pct = (this_month - last_month) / last_month * 100
    year  = rows[-1]['y']
    month = rows[-1]['m']

    breached = (comparison == 'gt' and growth_pct > threshold_value) or \
               (comparison == 'lt' and growth_pct < threshold_value)

    if breached and not _already_alerted(
            company_id, store_id, 'carbon_mom_growth', year, month):
        _insert_alert(company_id, store_id, threshold_id,
                      'carbon_mom_growth', growth_pct, threshold_value)


def _check_waste_weight_daily(company_id, store_id, threshold_id,
                              threshold_value, comparison):
    """Daily waste total for today."""
    row = query_db(
        'SELECT COALESCE(SUM(weight_kg), 0) AS total_kg '
        'FROM waste_record WHERE store_id = %s AND record_date = CURDATE()',
        (store_id,), one=True
    )
    if not row:
        return

    total = float(row['total_kg'])
    from datetime import date
    today = date.today()

    breached = (comparison == 'gt' and total > threshold_value) or \
               (comparison == 'lt' and total < threshold_value)

    if breached and not _already_alerted(
            company_id, store_id, 'waste_weight_daily', today.year, today.month):
        _insert_alert(company_id, store_id, threshold_id,
                      'waste_weight_daily', total, threshold_value)
