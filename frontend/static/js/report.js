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

    tbody.innerHTML = data.data.map(r => `
        <tr>
            <td><strong>${r.title}</strong></td>
            <td><span class="badge bg-info">${r.report_type}</span></td>
            <td><small>${formatDate(r.date_from)} ~ ${formatDate(r.date_to)}</small></td>
            <td><span class="badge ${statusBadge[r.status] || 'bg-secondary'}">${r.status}</span></td>
            <td><small class="text-muted">${formatDate(r.created_at)}</small></td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="viewReport(${r.id})" title="View">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-outline-warning" onclick="viewReport(${r.id}, true)" title="AI Analysis">
                        <i class="bi bi-stars"></i>
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
    `).join('');
}

async function generateReport(e) {
    e.preventDefault();
    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Generating...';

    const payload = {
        title: document.getElementById('title').value.trim(),
        report_type: document.getElementById('report_type').value,
        date_from: document.getElementById('date_from').value,
        date_to: document.getElementById('date_to').value
    };

    const data = await apiFetch('/api/report/generate', {
        method: 'POST',
        body: JSON.stringify(payload)
    });

    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-file-earmark-plus me-1"></i>Generate Report';

    if (data && data.success) {
        showAlert('reportAlert', 'Report generated successfully!', 'success');
        document.getElementById('reportForm').reset();
        loadReports();

        // Show preview
        if (data.data && data.data.content) {
            currentReportId = data.data.id;
            document.getElementById('reportContent').textContent = data.data.content;
            document.getElementById('previewCard').classList.remove('d-none');
            // Hide stale AI section from any previously viewed report
            document.getElementById('aiCommentSection').classList.add('d-none');
        }
    } else {
        showAlert('reportAlert', (data && data.message) || 'Failed to generate report');
    }
}

async function viewReport(id, triggerAi = false) {
    const data = await apiFetch(`/api/report/${id}`);
    if (!data || !data.success) return;

    currentReportId = id;
    document.getElementById('reportContent').textContent = data.data.content || 'No content available.';
    document.getElementById('previewCard').classList.remove('d-none');

    // Reset AI section
    const aiSection = document.getElementById('aiCommentSection');
    const aiContent = document.getElementById('aiCommentContent');
    const aiBadge   = document.getElementById('aiMockBadge');
    if (data.data.ai_comment) {
        aiContent.innerHTML = data.data.ai_comment_html || data.data.ai_comment;
        aiBadge.classList.toggle('d-none', !data.data.ai_comment.includes('Mock Mode'));
        aiSection.classList.remove('d-none');
    } else {
        aiSection.classList.add('d-none');
    }

    document.getElementById('previewCard').scrollIntoView({ behavior: 'smooth' });
    if (triggerAi && !data.data.ai_comment) {
        generateAiComment();
    }
}

async function generateAiComment() {
    if (!currentReportId) return;
    const btn = document.getElementById('aiCommentBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Analysing...';

    const data = await apiFetch(`/api/report/${currentReportId}/ai-comment`, { method: 'POST' });

    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-stars me-1"></i>Re-generate AI Analysis';

    if (!data || !data.success) {
        alert('Failed to generate AI analysis.');
        return;
    }

    const aiSection = document.getElementById('aiCommentSection');
    const aiContent = document.getElementById('aiCommentContent');
    const aiBadge   = document.getElementById('aiMockBadge');

    aiContent.innerHTML = data.ai_comment_html || data.ai_comment;
    aiBadge.classList.toggle('d-none', !data.is_mock);
    aiSection.classList.remove('d-none');
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
