"""LLM-backed insight generator for the AI Data Anomaly Detection module.

Reuses the same DeepSeek HTTP integration pattern as routes/report.py and
adds two responsibilities:

    1. Build a JSON-output prompt that asks DeepSeek to analyse a *batch*
       of statistical anomalies in one round-trip (cheap + low latency).
    2. Always return a usable result — if DeepSeek is unreachable, the
       LLM key is missing, or the JSON parse fails, fall back to a
       deterministic rule-based insight so the UI still works offline.

Public entry point:
    generate_anomaly_insights(anomalies: list[dict], top_n: int = 10) -> dict
        {
            "summary":            "<one-sentence overall finding>",
            "used_llm":           bool,   # True if DeepSeek answered
            "per_record_insight": {record_id: {"risk_category", "insight_markdown"}}
        }
"""
import os
import json
import ssl
import urllib.request
import urllib.error


# ──────────────────────────────────────────────
# DeepSeek HTTP call (mirrors routes/report.py)
# ──────────────────────────────────────────────

def _call_deepseek(prompt, max_tokens=700, timeout=30):
    """POST to DeepSeek chat completions. Return text or None on any error."""
    api_key = os.getenv('DEEPSEEK_API_KEY', '')
    if not api_key:
        return None

    try:
        try:
            import certifi
            ssl_context = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            ssl_context = ssl.create_default_context()

        payload = json.dumps({
            'model':       'deepseek-chat',
            'messages':    [{'role': 'user', 'content': prompt}],
            'max_tokens':  max_tokens,
            'temperature': 0.4,
        }).encode('utf-8')

        req = urllib.request.Request(
            'https://api.deepseek.com/v1/chat/completions',
            data=payload,
            headers={
                'Content-Type':  'application/json',
                'Authorization': f'Bearer {api_key}',
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result['choices'][0]['message']['content'].strip()
    except Exception:
        return None


# ──────────────────────────────────────────────
# Prompt construction
# ──────────────────────────────────────────────

def _build_anomaly_prompt(anomalies):
    """Build a strict JSON-output prompt for DeepSeek."""
    items = json.dumps(anomalies, ensure_ascii=False, indent=2, default=str)
    return (
        'You are an ESG data audit assistant for a retail sustainability platform. '
        'Below is a JSON array of statistical anomalies detected in carbon-emission '
        'or waste-disposal records. For EACH anomaly, generate a concise root-cause '
        'hypothesis and recommended audit actions.\n\n'
        f'Anomalies:\n{items}\n\n'
        'Respond with ONLY a JSON object (no markdown fences, no preamble) of the form:\n'
        '{\n'
        '  "summary": "<one sentence overall finding referencing counts and dominant pattern>",\n'
        '  "insights": [\n'
        '    {\n'
        '      "record_id": <int matching the input>,\n'
        '      "risk_category": "Data Quality" | "Operational Issue" | "Fraud Signal",\n'
        '      "insight_markdown": "<markdown string>"\n'
        '    }\n'
        '  ]\n'
        '}\n\n'
        'Each "insight_markdown" must use EXACTLY this structure (UK English, '
        'TOTAL <= 35 words across all three sections):\n'
        '### \U0001f50d Likely Cause\n'
        '<one short clause, max 12 words, referencing value & z-score>\n\n'
        '### \u26a0\ufe0f Risk Category\n'
        '**<Data Quality | Operational Issue | Fraud Signal>** \u2014 <max 6 words justification>\n\n'
        '### \u2705 Recommended Actions\n'
        '1. <imperative, max 8 words>\n'
        '2. <imperative, max 8 words>\n'
        'Keep summary <= 20 words. Do not exceed token budgets \u2014 brevity matters.\n'
    )


# ──────────────────────────────────────────────
# Deterministic fallback (no LLM)
# ──────────────────────────────────────────────

def _fallback_insight(a):
    """Generate a sensible insight without calling any LLM."""
    direction = a.get('direction', 'above')
    value     = a.get('value')
    mean      = a.get('mean')
    z         = a.get('z_score')
    note      = a.get('note')

    if note:
        cause   = note
        risk    = 'Data Quality'
        actions = [
            'Verify the source receipt or meter reading.',
            'Correct or remove the invalid value.',
            'Add input validation at the data-entry stage to prevent recurrence.',
        ]
    elif z is not None and direction == 'above' and abs(z) >= 3:
        cause = (f'Value {value} is {z:+.1f}\u03c3 above the {mean} category mean \u2014 '
                 f'most likely a unit / decimal-place data-entry error or an equipment spike.')
        risk = 'Data Quality'
        actions = [
            'Confirm the unit of measure and decimal placement.',
            'Cross-check meter or weighing-scale logs for that date.',
            'Compare with neighbouring stores during the same week.',
        ]
    elif z is not None and direction == 'above':
        cause = (f'Value {value} is {z:+.1f}\u03c3 above the {mean} category mean \u2014 '
                 f'a possible operational excursion (extended runtime, event, deep clean).')
        risk = 'Operational Issue'
        actions = [
            'Review equipment runtime and store occupancy for that day.',
            'Check whether unusual activities occurred (events, cleaning).',
            'Flag the store manager to investigate within 7 days.',
        ]
    elif z is not None and direction == 'below':
        cause = (f'Value {value} is {z:+.1f}\u03c3 below the {mean} category mean \u2014 '
                 f'possible under-reporting or a missing data submission.')
        risk = 'Data Quality'
        actions = [
            'Confirm whether the store was operating that day.',
            'Check for missing entries on adjacent dates.',
            'Verify with store staff that data was submitted on time.',
        ]
    else:
        cause   = 'This record violates a hard validation rule.'
        risk    = 'Data Quality'
        actions = ['Manually review and correct or remove the record.']

    md = (
        '### \U0001f50d Likely Cause\n'
        f'{cause}\n\n'
        '### \u26a0\ufe0f Risk Category\n'
        f'**{risk}** \u2014 inferred from z-score magnitude, direction and rule flags.\n\n'
        '### \u2705 Recommended Actions\n'
        + '\n'.join(f'{i + 1}. {act}' for i, act in enumerate(actions))
    )
    return {'risk_category': risk, 'insight_markdown': md}


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def generate_anomaly_insights(anomalies, top_n=5):
    """Analyse the top-N anomalies with DeepSeek; fill the rest with a fallback.

    Always returns a dict; never raises. Keys preserve the original
    record_id type (str or int).
    """
    by_id      = {}
    summary    = ''
    used_llm   = False
    top        = anomalies[:top_n] if anomalies else []

    if top:
        prompt = _build_anomaly_prompt(top)
        raw    = _call_deepseek(prompt)
        if raw:
            # DeepSeek occasionally wraps JSON in ```json fences \u2014 strip them.
            cleaned = raw.strip()
            if cleaned.startswith('```'):
                cleaned = cleaned.strip('`')
                if cleaned.lower().startswith('json'):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip()
            try:
                parsed  = json.loads(cleaned)
                summary = (parsed.get('summary') or '').strip()
                for item in parsed.get('insights', []):
                    rid = item.get('record_id')
                    if rid is None:
                        continue
                    # Preserve raw id (string like 'c-123' or plain int).
                    by_id[rid if isinstance(rid, str) else int(rid)] = {
                        'risk_category':    (item.get('risk_category') or '').strip(),
                        'insight_markdown': (item.get('insight_markdown') or '').strip(),
                    }
                used_llm = bool(by_id)
            except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                used_llm = False

    # Fill any anomaly that did not get an LLM insight with a deterministic one.
    for a in anomalies:
        rid = a.get('record_id')
        if rid is None or rid in by_id:
            continue
        by_id[rid] = _fallback_insight(a)

    if not summary:
        n_total = len(anomalies)
        n_high  = sum(1 for a in anomalies if a.get('severity') == 'high')
        if n_total == 0:
            summary = 'No anomalies detected in the selected period \u2014 data quality looks healthy.'
        else:
            dq_count = sum(1 for a in anomalies if a.get('note'))
            pattern = ('data-quality issues (zero / negative values, recycling exceeding total weight)'
                       if dq_count else 'values deviating significantly from category baselines')
            summary = (f'Detected **{n_total}** anomalies in the selected window '
                       f'(**{n_high}** high severity). The dominant pattern is {pattern}.')

    return {
        'summary':            summary,
        'used_llm':           used_llm,
        'per_record_insight': by_id,
    }
