import io
import re
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from jinja2 import Environment, FileSystemLoader
from backend.utils.auth_helper import login_required
from backend.utils.native_libs import prepare_macos_weasyprint_runtime

ocr_bp = Blueprint('ocr', __name__)


def _generate_demo_bill():
    """Render the demo electricity bill as an HTML string (for download/print)."""
    templates_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'frontend', 'templates', 'pdf'
    )
    env = Environment(loader=FileSystemLoader(templates_path))
    template = env.get_template('bill_template.html')
    return template.render(
        invoice_no='INV-2026-03-0042',
        invoice_date='31 March 2026',
        customer_name='Luckin Coffee – Chaoyang Store',
        customer_address='12 Chaoyang Park Road, Beijing',
        account_no='LC-CHY-001',
        period_from='01 March 2026',
        period_to='31 March 2026',
        billing_days=31,
        meter_no='MTR-00421-X',
        meter_reading_prev=52400,
        meter_reading_curr=65900,
        consumption_kwh=13500,
        unit_rate=22.8,
        energy_charge='3,078.00',
        standing_charge='31.00',
        vat_amount='420.47',
        total_due='3,529.47',
        payment_due_date='14 April 2026',
    )


@ocr_bp.route('/ocr/demo-bill')
@login_required
def demo_bill():
    """Render the demo electricity bill as HTML (viewable in browser)."""
    html_str = _generate_demo_bill()
    return html_str, 200, {'Content-Type': 'text/html; charset=utf-8'}


@ocr_bp.route('/ocr/demo-bill/pdf')
@login_required
def demo_bill_pdf():
    """Export the demo electricity bill as a PDF for download."""
    try:
        from weasyprint import HTML
    except ImportError:
        return jsonify({'success': False, 'message': 'WeasyPrint not installed'}), 500
    except OSError as err:
        prepare_macos_weasyprint_runtime()
        try:
            from weasyprint import HTML
        except Exception:
            return jsonify({'success': False, 'message': f'WeasyPrint runtime error: {err}'}), 500

    html_str = _generate_demo_bill()
    pdf_bytes = HTML(string=html_str).write_pdf()
    return pdf_bytes, 200, {
        'Content-Type': 'application/pdf',
        'Content-Disposition': 'attachment; filename="demo_electricity_bill.pdf"'
    }


@ocr_bp.route('/api/ocr/scan-bill', methods=['POST'])
@login_required
def scan_bill():
    """
    OCR endpoint: accepts an uploaded image or PDF and extracts billing fields.
    Returns structured data to pre-fill the carbon record form.

    Tries pytesseract (real OCR) first; falls back to mock data if unavailable.
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'message': 'Empty filename'}), 400

    filename_lower = file.filename.lower()
    file_bytes = file.read()

    # --- Try real OCR with pytesseract ---
    extracted_text = None

    if filename_lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(io.BytesIO(file_bytes))
            extracted_text = pytesseract.image_to_string(img)
        except ImportError:
            extracted_text = None

    elif filename_lower.endswith('.pdf'):
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages = [p.extract_text() or '' for p in pdf.pages]
                extracted_text = '\n'.join(pages)
        except ImportError:
            extracted_text = None

    # --- Parse extracted text if available ---
    if extracted_text:
        result = _parse_bill_text(extracted_text)
        result['source'] = 'ocr'
        return jsonify({'success': True, 'data': result})

    # --- Fallback: mock response using demo bill values ---
    return jsonify({
        'success': True,
        'data': {
            'source': 'mock',
            'category': 'electricity',
            'activity_value': 13500,
            'record_date': '2026-03-31',
            'note': 'Mar electricity (scanned bill)',
            'invoice_no': 'INV-2026-03-0042',
            'supplier': 'CityGrid Energy',
        }
    })


def _parse_bill_text(text):
    """
    Extract structured fields from raw OCR text of a utility bill.
    Supports electricity, gas, and transport bills.
    """
    result = {}

    # --- Detect bill type ---
    text_lower = text.lower()
    if 'kwh' in text_lower or 'electricity' in text_lower or 'electric' in text_lower:
        result['category'] = 'electricity'
    elif 'natural gas' in text_lower or 'gas bill' in text_lower or 'cubic' in text_lower:
        result['category'] = 'fuel'
    elif 'fuel' in text_lower or 'diesel' in text_lower or 'petrol' in text_lower:
        result['category'] = 'fuel'
    elif 'transport' in text_lower or 'delivery' in text_lower or 'freight' in text_lower:
        result['category'] = 'transport'
    else:
        result['category'] = 'electricity'

    # --- Extract consumption value ---
    if result['category'] == 'electricity':
        # Match patterns like "13,500 kWh" or "13500kWh" or "Consumption 13500"
        m = re.search(r'consumption[^\d]*([0-9,]+(?:\.\d+)?)\s*kwh', text_lower)
        if not m:
            m = re.search(r'([0-9,]+(?:\.\d+)?)\s*kwh', text_lower)
        if m:
            result['activity_value'] = float(m.group(1).replace(',', ''))

    elif result['category'] == 'fuel':
        # Match cubic metres or litres
        m = re.search(r'([0-9,]+(?:\.\d+)?)\s*cubic\s*m', text_lower)
        if not m:
            m = re.search(r'([0-9,]+(?:\.\d+)?)\s*m3', text_lower)
        if m:
            result['activity_value'] = float(m.group(1).replace(',', ''))

    elif result['category'] == 'transport':
        # Match kilometres
        m = re.search(r'([0-9,]+(?:\.\d+)?)\s*km', text_lower)
        if m:
            result['activity_value'] = float(m.group(1).replace(',', ''))

    # --- Extract billing period end date (record date) ---
    # Formats: "31 March 2026", "2026-03-31", "03/31/2026"
    date_patterns = [
        r'(\d{1,2})\s+(january|february|march|april|may|june|july|august|'
        r'september|october|november|december)\s+(\d{4})',
        r'(\d{4})-(\d{2})-(\d{2})',
        r'(\d{2})/(\d{2})/(\d{4})',
    ]
    months = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12'
    }

    for pat in date_patterns:
        m = re.search(pat, text_lower)
        if m:
            g = m.groups()
            if len(g) == 3 and g[1] in months:
                result['record_date'] = f'{g[2]}-{months[g[1]]}-{g[0].zfill(2)}'
            elif len(g) == 3 and '-' in pat:
                result['record_date'] = f'{g[0]}-{g[1]}-{g[2]}'
            break

    # --- Extract invoice / reference number ---
    m = re.search(r'invoice\s*(?:no|number|#)?[.:\s]*([A-Z0-9\-]+)', text, re.IGNORECASE)
    if m:
        result['invoice_no'] = m.group(1).strip()

    # --- Extract supplier name (first non-empty line, heuristic) ---
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if lines:
        result['supplier'] = lines[0][:60]

    # --- Build note ---
    month_name = ''
    if 'record_date' in result:
        try:
            month_name = datetime.strptime(result['record_date'], '%Y-%m-%d').strftime('%b')
        except ValueError:
            pass
    category_label = {'electricity': 'electricity', 'fuel': 'natural gas', 'transport': 'delivery'}.get(
        result.get('category', 'electricity'), 'utility'
    )
    result['note'] = f'{month_name} {category_label} (scanned bill)'.strip()

    return result
