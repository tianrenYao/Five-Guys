"""
backend/utils/mail.py
Email notification utility with Flask-Mail + mock fallback.
If MAIL_SERVER is not configured, emails are logged to console instead.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_mail = None

try:
    from flask_mail import Mail, Message
    _FLASK_MAIL_INSTALLED = True
except ImportError:
    _FLASK_MAIL_INSTALLED = False

METRIC_LABELS = {
    'waste_recycling_rate': 'Waste Recovery Rate',
    'carbon_mom_growth':    'Carbon MoM Growth',
    'waste_weight_daily':   'Daily Waste Weight',
}
METRIC_UNITS = {
    'waste_recycling_rate': '%',
    'carbon_mom_growth':    '%',
    'waste_weight_daily':   'kg',
}


def init_mail(app):
    """Call this inside create_app() to wire up Flask-Mail."""
    global _mail
    if not _FLASK_MAIL_INSTALLED:
        app.logger.warning('[Mail] flask-mail not installed — running in MOCK mode.')
        return
    if not app.config.get('MAIL_SERVER'):
        app.logger.warning('[Mail] MAIL_SERVER not configured — running in MOCK mode.')
        return
    _mail = Mail(app)
    app.logger.info('[Mail] Flask-Mail initialised (server=%s)', app.config['MAIL_SERVER'])


def send_alert_email(to_addresses, metric_type, store_name,
                     current_value, threshold_value, triggered_at=None):
    """
    Send an ESG alert notification email.
    Falls back to console logging (mock) when SMTP is not configured.

    Args:
        to_addresses : list[str]  – recipient email addresses
        metric_type  : str        – e.g. 'waste_recycling_rate'
        store_name   : str
        current_value: float
        threshold_value: float
        triggered_at : datetime | None
    """
    if not to_addresses:
        return

    ts     = (triggered_at or datetime.now()).strftime('%Y-%m-%d %H:%M')
    label  = METRIC_LABELS.get(metric_type, metric_type)
    unit   = METRIC_UNITS.get(metric_type, '')

    subject = f'[ESG Alert] {label} threshold breached — {store_name}'
    body = (
        f'ESG Alert Notification\n'
        f'======================\n'
        f'Store     : {store_name}\n'
        f'Metric    : {label}\n'
        f'Value     : {current_value:.2f}{unit}\n'
        f'Threshold : {threshold_value:.2f}{unit}\n'
        f'Time      : {ts}\n\n'
        f'Please log in to the ESG Management Platform to review and resolve this alert.\n'
    )

    if _mail is None:
        logger.warning(
            '[Mail MOCK] Would send to=%s | Subject: %s | Value=%.2f%s vs threshold=%.2f%s',
            to_addresses, subject, current_value, unit, threshold_value, unit
        )
        return

    try:
        msg = Message(subject=subject, recipients=to_addresses, body=body)
        _mail.send(msg)
        logger.info('[Mail] Alert email sent to %s', to_addresses)
    except Exception as exc:
        logger.error('[Mail] Failed to send alert email: %s', exc)
