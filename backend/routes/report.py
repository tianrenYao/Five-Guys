import os
import io
from datetime import datetime
from flask import Blueprint, request, session, render_template, jsonify, send_file
from backend.utils.db import query_db, execute_db, insert_db
from backend.utils.auth_helper import login_required, role_required, get_accessible_store_ids

report_bp = Blueprint('report', __name__)


@report_bp.route('/report')
@login_required
def report_page():
    return render_template('report.html')


@report_bp.route('/api/report/list')
@login_required
def report_list():
    """Get all reports for the current company."""
    company_id = session['company_id']
    rows = query_db(
        'SELECT r.id, r.title, r.report_type, r.date_from, r.date_to, '
        'r.status, r.pdf_path, r.created_at, u.display_name AS created_by '
        'FROM report r '
        'LEFT JOIN `user` u ON u.id = r.user_id '
        'WHERE r.company_id = %s ORDER BY r.created_at DESC',
        (company_id,)
    )
    for r in rows:
        r['date_from'] = str(r['date_from']) if r['date_from'] else None
        r['date_to'] = str(r['date_to']) if r['date_to'] else None
        r['created_at'] = str(r['created_at']) if r['created_at'] else None
    return jsonify({'success': True, 'data': rows})


@report_bp.route('/api/report/generate', methods=['POST'])
@login_required
@role_required('hq_manager', 'region_manager', 'admin')
def report_generate():
    """Generate a sustainability report based on date range."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'}), 400

    title = data.get('title', '').strip()
    report_type = data.get('report_type', 'monthly')
    date_from = data.get('date_from')
    date_to = data.get('date_to')

    if not all([title, date_from, date_to]):
        return jsonify({'success': False, 'message': 'title, date_from, and date_to are required'}), 400

    if report_type not in ('monthly', 'quarterly', 'annual', 'custom'):
        return jsonify({'success': False, 'message': 'Invalid report_type'}), 400

    company_id = session['company_id']
    store_ids  = get_accessible_store_ids()

    if not store_ids:
        return jsonify({'success': False, 'message': 'No accessible stores found'}), 403

    ph = ','.join(['%s'] * len(store_ids))
    sid = list(store_ids)

    # Gather carbon data
    carbon_data = query_db(
        'SELECT category, SUM(activity_value) AS total_activity, '
        'SUM(total_carbon) AS total_carbon, COUNT(*) AS record_count '
        'FROM carbon_record '
        f'WHERE store_id IN ({ph}) AND record_date BETWEEN %s AND %s '
        'GROUP BY category',
        sid + [date_from, date_to]
    )

    # Gather waste data
    waste_data = query_db(
        'SELECT wc.name AS category, SUM(wr.weight_kg) AS total_kg, '
        'SUM(wr.recycled_kg) AS recycled_kg '
        'FROM waste_record wr '
        'JOIN waste_category wc ON wc.id = wr.category_id '
        f'WHERE wr.store_id IN ({ph}) AND wr.record_date BETWEEN %s AND %s '
        'GROUP BY wc.name',
        sid + [date_from, date_to]
    )

    # Calculate totals
    total_carbon   = sum(float(r['total_carbon'] or 0) for r in carbon_data)
    total_waste    = sum(float(r['total_kg']     or 0) for r in waste_data)
    total_recycled = sum(float(r['recycled_kg']  or 0) for r in waste_data)
    recovery_rate  = round(total_recycled / total_waste * 100, 1) if total_waste > 0 else 0

    # Build report content (kept as summary text for DB storage)
    content = _build_report_content(
        title, date_from, date_to, carbon_data, waste_data,
        total_carbon, total_waste, recovery_rate
    )

    report_id = insert_db(
        'INSERT INTO report (company_id, user_id, title, report_type, date_from, date_to, content, status) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
        (company_id, session['user_id'], title, report_type, date_from, date_to, content, 'generated')
    )

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'CREATE', 'report', report_id,
         f'Generated report: {title}', request.remote_addr)
    )

    return jsonify({
        'success': True,
        'message': 'Report generated successfully',
        'data': {'id': report_id, 'content': content}
    }), 201


@report_bp.route('/api/report/<int:report_id>')
@login_required
def report_detail(report_id):
    """Get a specific report."""
    report = query_db(
        'SELECT r.*, u.display_name AS created_by '
        'FROM report r LEFT JOIN `user` u ON u.id = r.user_id '
        'WHERE r.id = %s AND r.company_id = %s',
        (report_id, session['company_id']), one=True
    )
    if not report:
        return jsonify({'success': False, 'message': 'Report not found'}), 404

    report['date_from'] = str(report['date_from']) if report['date_from'] else None
    report['date_to'] = str(report['date_to']) if report['date_to'] else None
    report['created_at'] = str(report['created_at']) if report['created_at'] else None
    report['updated_at'] = str(report['updated_at']) if report['updated_at'] else None

    return jsonify({'success': True, 'data': report})


@report_bp.route('/api/report/<int:report_id>/export-pdf')
@login_required
def report_export_pdf(report_id):
    """Export a report as PDF using WeasyPrint + Jinja2 HTML template."""
    report = query_db(
        'SELECT * FROM report WHERE id = %s AND company_id = %s',
        (report_id, session['company_id']), one=True
    )
    if not report:
        return jsonify({'success': False, 'message': 'Report not found'}), 404

    try:
        from weasyprint import HTML
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        return jsonify({'success': False,
                        'message': 'WeasyPrint not installed. Run: pip install weasyprint'}), 500

    # Re-query aggregated data for the PDF template
    company_id = report['company_id']
    date_from  = str(report['date_from'])
    date_to    = str(report['date_to'])

    carbon_data = query_db(
        'SELECT category, SUM(activity_value) AS total_activity, '
        'SUM(total_carbon) AS total_carbon, COUNT(*) AS record_count '
        'FROM carbon_record '
        'WHERE company_id = %s AND record_date BETWEEN %s AND %s '
        'GROUP BY category',
        (company_id, date_from, date_to)
    )
    waste_data = query_db(
        'SELECT wc.name AS category, SUM(wr.weight_kg) AS total_kg, '
        'SUM(wr.recycled_kg) AS recycled_kg '
        'FROM waste_record wr '
        'JOIN waste_category wc ON wc.id = wr.category_id '
        'WHERE wr.company_id = %s AND wr.record_date BETWEEN %s AND %s '
        'GROUP BY wc.name',
        (company_id, date_from, date_to)
    )
    store_count = query_db(
        'SELECT COUNT(DISTINCT store_id) AS cnt FROM carbon_record '
        'WHERE company_id = %s AND record_date BETWEEN %s AND %s',
        (company_id, date_from, date_to), one=True
    )

    total_carbon   = sum(float(r['total_carbon'] or 0) for r in carbon_data)
    total_waste    = sum(float(r['total_kg']     or 0) for r in waste_data)
    total_recycled = sum(float(r['recycled_kg']  or 0) for r in waste_data)
    recovery_rate  = round(total_recycled / total_waste * 100, 1) if total_waste > 0 else 0

    # Convert Decimal → float for Jinja2
    for r in carbon_data:
        r['total_activity'] = float(r['total_activity'] or 0)
        r['total_carbon']   = float(r['total_carbon']   or 0)
    for r in waste_data:
        r['total_kg']    = float(r['total_kg']    or 0)
        r['recycled_kg'] = float(r['recycled_kg'] or 0)

    # Render HTML template
    templates_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'frontend', 'templates', 'pdf'
    )
    env = Environment(loader=FileSystemLoader(templates_path))
    template = env.get_template('report_template.html')
    html_str = template.render(
        report=report,
        carbon_data=carbon_data,
        waste_data=waste_data,
        total_carbon=total_carbon,
        total_waste=total_waste,
        total_recycled=total_recycled,
        recovery_rate=recovery_rate,
        store_count=store_count['cnt'] if store_count else 0,
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M')
    )

    # Convert to PDF
    pdf_bytes = HTML(string=html_str).write_pdf()

    # Save to disk and update DB
    reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    pdf_filename = f'report_{report_id}_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf'
    pdf_path = os.path.join(reports_dir, pdf_filename)
    with open(pdf_path, 'wb') as f:
        f.write(pdf_bytes)

    execute_db(
        'UPDATE report SET pdf_path = %s, status = %s WHERE id = %s',
        (pdf_path, 'exported', report_id)
    )

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{report["title"]}.pdf'
    )


@report_bp.route('/api/report/<int:report_id>/delete', methods=['DELETE'])
@login_required
@role_required('hq_manager', 'admin')
def report_delete(report_id):
    """Delete a report."""
    record = query_db(
        'SELECT id FROM report WHERE id = %s AND company_id = %s',
        (report_id, session['company_id']), one=True
    )
    if not record:
        return jsonify({'success': False, 'message': 'Report not found'}), 404

    execute_db('DELETE FROM report WHERE id = %s', (report_id,))

    execute_db(
        'INSERT INTO audit_log (user_id, action, target_type, target_id, detail, ip_address) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (session['user_id'], 'DELETE', 'report', report_id,
         f'Deleted report #{report_id}', request.remote_addr)
    )

    return jsonify({'success': True, 'message': 'Report deleted successfully'})


def _build_report_content(title, date_from, date_to, carbon_data, waste_data,
                          total_carbon, total_waste, recovery_rate):
    """Build the text content of a sustainability report."""
    lines = [
        f'Sustainability Report: {title}',
        f'Reporting Period: {date_from} to {date_to}',
        f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        '',
        '--- CARBON EMISSIONS SUMMARY ---',
        f'Total Carbon Emissions: {total_carbon:.2f} kgCO2e',
        '',
    ]

    if carbon_data:
        lines.append('Breakdown by Category:')
        for r in carbon_data:
            lines.append(f'  - {r["category"]}: {float(r["total_carbon"]):.2f} kgCO2e '
                         f'({int(r["record_count"])} records)')
    else:
        lines.append('No carbon emission data recorded in this period.')

    lines.extend([
        '',
        '--- WASTE MANAGEMENT SUMMARY ---',
        f'Total Waste: {total_waste:.2f} kg',
        f'Recycling Rate: {recovery_rate}%',
        '',
    ])

    if waste_data:
        lines.append('Breakdown by Category:')
        for r in waste_data:
            recyclable_tag = ' [Recyclable]' if r['is_recyclable'] else ''
            lines.append(f'  - {r["category"]}: {float(r["total_kg"]):.2f} kg{recyclable_tag}')
    else:
        lines.append('No waste data recorded in this period.')

    lines.extend([
        '',
        '--- SDG ALIGNMENT ---',
        'This report contributes to the following UN Sustainable Development Goals:',
        '  - SDG 9: Industry, Innovation and Infrastructure',
        '  - SDG 11: Sustainable Cities and Communities',
        '  - SDG 12: Responsible Consumption and Production',
        '  - SDG 13: Climate Action',
        '',
        '--- END OF REPORT ---',
    ])

    return '\n'.join(lines)
