/**
 * Report page logic
 */

let currentReportId = null;

document.addEventListener('DOMContentLoaded', function () {
    // Set default dates (last 30 days)
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(today.getDate() - 30);
    document.getElementById('date_to').value = today.toISOString().substring(0, 10);
    document.getElementById('date_from').value = thirtyDaysAgo.toISOString().substring(0, 10);

    loadReports();
    document.getElementById('reportForm').addEventListener('submit', generateReport);
});

async function loadReports() {
    const data = await apiFetch('/api/report/list');
    if (!data || !data.success) return;

    const tbody = document.getElementById('reportsBody');
    if (data.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No reports yet. Generate your first sustainability report.</td></tr>';
        return;
    }

    const statusBadge = {
        draft: 'bg-secondary',
        generated: 'bg-success',
        exported: 'bg-primary'
    };

    tbody.innerHTML = data.data.map(r => {
        const isAi = r.comment_source === 'ai';
        const isTpl = r.comment_source === 'template';
        const sourceBadge = isAi
            ? '<span class="badge bg-warning text-dark ms-1" title="AI-generated evaluation"><i class="bi bi-stars"></i></span>'
            : isTpl
                ? '<span class="badge bg-secondary ms-1" title="Rule-based evaluation"><i class="bi bi-list-check"></i></span>'
                : '';
        return `
        <tr>
            <td><strong>${r.title}</strong>${sourceBadge}</td>
            <td><span class="badge bg-info">${r.report_type}</span></td>
            <td><small>${formatDate(r.date_from)} ~ ${formatDate(r.date_to)}</small></td>
            <td><span class="badge ${statusBadge[r.status] || 'bg-secondary'}">${r.status}</span></td>
            <td><small class="text-muted">${formatDate(r.created_at)}</small></td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="viewReport(${r.id})" title="View">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-outline-success" onclick="exportPdf(${r.id})" title="Export PDF">
                        <i class="bi bi-file-pdf"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteReport(${r.id})" title="Delete">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `;
    }).join('');
}

// Render the evaluation block (title, icon, badge, content) based on comment_source.
function renderEvaluation({ ai_comment_html, ai_comment, comment_source, ai_fallback_to_template }) {
    const section = document.getElementById('aiCommentSection');
    const titleEl = document.getElementById('aiCommentTitle');
    const iconEl  = document.getElementById('aiCommentIcon');
    const badgeEl = document.getElementById('aiSourceBadge');
    const content = document.getElementById('aiCommentContent');
    const btnEl   = document.getElementById('aiCommentBtn');

    if (!ai_comment_html && !ai_comment) {
        section.classList.add('d-none');
        return;
    }

    content.innerHTML = ai_comment_html || ai_comment;

    if (comment_source === 'template') {
        titleEl.textContent = 'Rule-based ESG Evaluation';
        iconEl.className = 'bi bi-list-check text-secondary fs-5';
        badgeEl.textContent = ai_fallback_to_template ? 'AI unavailable — template fallback' : 'Template';
        badgeEl.className = 'badge bg-secondary';
        badgeEl.classList.remove('d-none');
        if (btnEl) {
            btnEl.innerHTML = '<i class="bi bi-stars me-1"></i>Upgrade to AI Analysis';
            btnEl.classList.remove('d-none');
        }
    } else {
        titleEl.textContent = 'AI ESG Analysis';
        iconEl.className = 'bi bi-stars text-warning fs-5';
        badgeEl.textContent = 'AI · DeepSeek';
        badgeEl.className = 'badge bg-warning text-dark';
        badgeEl.classList.remove('d-none');
        if (btnEl) {
            btnEl.innerHTML = '<i class="bi bi-stars me-1"></i>Re-generate AI Analysis';
            btnEl.classList.remove('d-none');
        }
    }

    section.classList.remove('d-none');
}

async function generateReport(e) {
    e.preventDefault();
    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Generating...';

    const useAi = document.getElementById('useAi').checked;
    const payload = {
        title: document.getElementById('title').value.trim(),
        report_type: document.getElementById('report_type').value,
        date_from: document.getElementById('date_from').value,
        date_to: document.getElementById('date_to').value,
        use_ai: useAi
    };

    btn.innerHTML = useAi
        ? '<span class="spinner-border spinner-border-sm me-1"></span>Generating + calling AI...'
        : '<span class="spinner-border spinner-border-sm me-1"></span>Generating...';

    const data = await apiFetch('/api/report/generate', {
        method: 'POST',
        body: JSON.stringify(payload)
    });

    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-file-earmark-plus me-1"></i>Generate Report';

    if (data && data.success) {
        const d = data.data || {};
        let msg = 'Report generated successfully!';
        if (d.ai_fallback_to_template) {
            msg = 'Report generated, but AI service was unavailable — used rule-based template instead.';
        }
        showAlert('reportAlert', msg, d.ai_fallback_to_template ? 'warning' : 'success');
        // Preserve form values; only reset the title so the user can quickly chain reports if needed
        document.getElementById('title').value = '';
        loadReports();

        // Show preview with evaluation already filled in
        if (d.content) {
            currentReportId = d.id;
            document.getElementById('reportContent').textContent = d.content;
            document.getElementById('previewCard').classList.remove('d-none');
            renderEvaluation(d);
            document.getElementById('previewCard').scrollIntoView({ behavior: 'smooth' });
        }
    } else {
        showAlert('reportAlert', (data && data.message) || 'Failed to generate report');
    }
}

async function viewReport(id) {
    const data = await apiFetch(`/api/report/${id}`);
    if (!data || !data.success) return;

    currentReportId = id;
    document.getElementById('reportContent').textContent = data.data.content || 'No content available.';
    document.getElementById('previewCard').classList.remove('d-none');

    renderEvaluation({
        ai_comment: data.data.ai_comment,
        ai_comment_html: data.data.ai_comment_html,
        comment_source: data.data.comment_source,
        ai_fallback_to_template: false
    });

    document.getElementById('previewCard').scrollIntoView({ behavior: 'smooth' });
}

async function generateAiComment() {
    if (!currentReportId) return;
    const btn = document.getElementById('aiCommentBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Analysing...';

    const data = await apiFetch(`/api/report/${currentReportId}/ai-comment`, { method: 'POST' });

    btn.disabled = false;

    if (!data || !data.success) {
        btn.innerHTML = '<i class="bi bi-stars me-1"></i>Re-generate AI Analysis';
        alert('Failed to generate AI analysis.');
        return;
    }

    renderEvaluation({
        ai_comment: data.ai_comment,
        ai_comment_html: data.ai_comment_html,
        comment_source: data.comment_source,
        ai_fallback_to_template: (data.comment_source === 'template')
    });
    loadReports();
}

function exportPdf(id) {
    window.open(`/api/report/${id}/export-pdf`, '_blank');
}

async function deleteReport(id) {
    if (!confirm('Are you sure you want to delete this report?')) return;

    const data = await apiFetch(`/api/report/${id}/delete`, { method: 'DELETE' });
    if (data && data.success) {
        loadReports();
        document.getElementById('previewCard').classList.add('d-none');
    } else {
        alert((data && data.message) || 'Failed to delete report');
    }
}
