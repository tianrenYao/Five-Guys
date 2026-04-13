/**
 * Alert Centre page logic
 */

document.addEventListener('DOMContentLoaded', function () {
    loadAlertLogs();
    if (document.getElementById('thresholdBody')) {
        loadThresholds();
    }
});

// ── Alert Logs ────────────────────────────────────────────

async function loadAlertLogs() {
    const data = await apiFetch('/api/alert/logs');
    if (!data || !data.success) return;

    const tbody = document.getElementById('alertLogsBody');
    if (!data.data.length) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">No alerts — all clear!</td></tr>';
        return;
    }

    const METRIC_LABELS = {
        waste_recycling_rate: 'Recycling Rate',
        carbon_mom_growth:    'Carbon MoM Growth',
        waste_weight_daily:   'Daily Waste'
    };
    const METRIC_UNITS = {
        waste_recycling_rate: '%',
        carbon_mom_growth:    '%',
        waste_weight_daily:   'kg'
    };

    tbody.innerHTML = data.data.map(r => {
        const label = METRIC_LABELS[r.metric_type] || r.metric_type;
        const unit  = METRIC_UNITS[r.metric_type]  || '';
        const readBadge = r.is_read
            ? '<span class="badge bg-secondary">Read</span>'
            : '<span class="badge bg-danger">Unread</span>';
        const ts = r.triggered_at ? r.triggered_at.substring(0, 16) : '-';
        return `
        <tr class="${r.is_read ? '' : 'table-warning'}">
            <td><small>${ts}</small></td>
            <td>${r.store_name || '-'}</td>
            <td><small class="text-muted">${r.region_name || '-'}</small></td>
            <td>${label}</td>
            <td><strong>${Number(r.current_value).toFixed(1)}${unit}</strong></td>
            <td>${Number(r.threshold_value).toFixed(1)}${unit}</td>
            <td>${readBadge}</td>
            <td>
                ${!r.is_read ? `<button class="btn btn-sm btn-outline-secondary" onclick="markRead(${r.id})" title="Mark read">
                    <i class="bi bi-check2"></i>
                </button>` : ''}
            </td>
        </tr>`;
    }).join('');

    // refresh badge counts after viewing
    loadAlertBadge();
}

async function markRead(logId) {
    const data = await apiFetch(`/api/alert/logs/${logId}/read`, { method: 'POST' });
    if (data && data.success) loadAlertLogs();
}

async function markAllRead() {
    if (!confirm('Mark all alerts as read?')) return;
    const data = await apiFetch('/api/alert/logs/read-all', { method: 'POST' });
    if (data && data.success) {
        loadAlertLogs();
        loadAlertBadge();
    }
}

// ── Thresholds ────────────────────────────────────────────

async function loadThresholds() {
    const data = await apiFetch('/api/alert/thresholds');
    if (!data || !data.success) return;

    const tbody = document.getElementById('thresholdBody');
    if (!data.data.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-3">No thresholds configured.</td></tr>';
        return;
    }

    const METRIC_LABELS = {
        waste_recycling_rate: 'Recycling Rate (%)',
        carbon_mom_growth:    'Carbon MoM Growth (%)',
        waste_weight_daily:   'Daily Waste (kg)'
    };

    tbody.innerHTML = data.data.map(t => `
        <tr>
            <td>${METRIC_LABELS[t.metric_type] || t.metric_type}</td>
            <td><span class="badge bg-light text-dark">${t.scope}</span></td>
            <td>${t.comparison === 'lt' ? 'Below (<)' : 'Above (>)'}</td>
            <td><strong>${Number(t.threshold_value).toFixed(1)}</strong></td>
            <td>
                ${t.is_active
                    ? '<span class="badge bg-success">Active</span>'
                    : '<span class="badge bg-secondary">Disabled</span>'}
            </td>
            <td><small class="text-muted">${t.notify_email
                ? `<i class="bi bi-envelope-check text-success me-1"></i>${t.notify_email}`
                : '<span class="text-muted">—</span>'}</small></td>
            <td><small class="text-muted">${t.created_by_name || '-'}</small></td>
            <td>
                <button class="btn btn-sm btn-outline-warning me-1" onclick="toggleThreshold(${t.id}, ${t.is_active})" title="${t.is_active ? 'Disable' : 'Enable'}">
                    <i class="bi bi-${t.is_active ? 'pause' : 'play'}"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteThreshold(${t.id})" title="Delete">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function saveThreshold() {
    const payload = {
        metric_type:     document.getElementById('metric_type').value,
        comparison:      document.getElementById('comparison').value,
        threshold_value: parseFloat(document.getElementById('threshold_value').value),
        scope:           document.getElementById('scope').value,
        notify_email:    (document.getElementById('notify_email').value || '').trim()
    };

    if (!payload.threshold_value) {
        showAlert('thresholdAlert', 'Please enter a threshold value.');
        return;
    }

    const data = await apiFetch('/api/alert/thresholds', {
        method: 'POST',
        body: JSON.stringify(payload)
    });

    if (data && data.success) {
        bootstrap.Modal.getInstance(document.getElementById('addThresholdModal')).hide();
        document.getElementById('thresholdForm').reset();
        loadThresholds();
    } else {
        showAlert('thresholdAlert', (data && data.message) || 'Failed to save threshold.');
    }
}

async function toggleThreshold(id, currentlyActive) {
    const data = await apiFetch(`/api/alert/thresholds/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ is_active: currentlyActive ? 0 : 1 })
    });
    if (data && data.success) loadThresholds();
}

async function deleteThreshold(id) {
    if (!confirm('Delete this threshold?')) return;
    const data = await apiFetch(`/api/alert/thresholds/${id}`, { method: 'DELETE' });
    if (data && data.success) loadThresholds();
}
