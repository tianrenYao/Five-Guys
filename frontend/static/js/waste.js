/**
 * Waste Management page logic
 */

document.addEventListener('DOMContentLoaded', function () {
    setDefaultDate('record_date');
    loadCategories();
    loadRecords();
    loadStats();

    document.getElementById('wasteForm').addEventListener('submit', addRecord);
});

async function loadCategories() {
    const data = await apiFetch('/api/waste/categories');
    if (!data || !data.success) return;

    const sel = document.getElementById('category_id');
    data.data.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = c.name + (c.is_recyclable ? ' ♻️' : '');
        sel.appendChild(opt);
    });
}

async function loadRecords() {
    const dateFrom = document.getElementById('filterFrom').value;
    const dateTo = document.getElementById('filterTo').value;
    let url = '/api/waste/list?';
    if (dateFrom) url += `date_from=${dateFrom}&`;
    if (dateTo) url += `date_to=${dateTo}&`;

    const data = await apiFetch(url);
    if (!data || !data.success) return;

    const tbody = document.getElementById('recordsBody');
    if (data.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No records found. Add your first waste record.</td></tr>';
        return;
    }

    tbody.innerHTML = data.data.map(r => `
        <tr>
            <td>${formatDate(r.record_date)}</td>
            <td>${r.category_name}</td>
            <td>${formatNumber(r.weight_kg)}</td>
            <td>${r.is_recyclable
                ? '<span class="badge bg-success">Yes</span>'
                : '<span class="badge bg-secondary">No</span>'}</td>
            <td><small class="text-muted">${r.recorded_by || '-'}</small></td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteRecord(${r.id})" title="Delete">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

async function addRecord(e) {
    e.preventDefault();
    const btn = document.getElementById('submitBtn');
    btn.disabled = true;

    const payload = {
        category_id: parseInt(document.getElementById('category_id').value),
        weight_kg: parseFloat(document.getElementById('weight_kg').value),
        record_date: document.getElementById('record_date').value,
        note: document.getElementById('note').value
    };

    if (!payload.category_id) {
        showAlert('wasteAlert', 'Please select a waste category.');
        btn.disabled = false;
        return;
    }

    const data = await apiFetch('/api/waste/add', {
        method: 'POST',
        body: JSON.stringify(payload)
    });

    btn.disabled = false;

    if (data && data.success) {
        showAlert('wasteAlert', 'Waste record added successfully!', 'success');
        document.getElementById('wasteForm').reset();
        setDefaultDate('record_date');
        loadRecords();
        loadStats();
    } else {
        showAlert('wasteAlert', (data && data.message) || 'Failed to add record');
    }
}

async function deleteRecord(id) {
    if (!confirm('Are you sure you want to delete this record?')) return;

    const data = await apiFetch(`/api/waste/delete/${id}`, { method: 'DELETE' });
    if (data && data.success) {
        loadRecords();
        loadStats();
    } else {
        alert((data && data.message) || 'Failed to delete record');
    }
}

async function loadStats() {
    const data = await apiFetch('/api/waste/stats');
    if (!data || !data.success || data.data.length === 0) {
        const el = document.getElementById('chartWasteStats');
        if (el) el.innerHTML = '<p class="text-center text-muted py-4">No data yet</p>';
        return;
    }

    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const months = data.data.map(r => monthNames[r.month - 1]);
    const totalVals = data.data.map(r => r.total_weight_kg);
    const recycVals = data.data.map(r => r.recyclable_kg);

    const chart = echarts.init(document.getElementById('chartWasteStats'));
    chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['Total', 'Recyclable'], bottom: 0 },
        grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
        xAxis: { type: 'category', data: months },
        yAxis: { type: 'value', name: 'kg' },
        series: [
            {
                name: 'Total',
                type: 'bar',
                data: totalVals,
                itemStyle: { color: '#ffc107', borderRadius: [4, 4, 0, 0] }
            },
            {
                name: 'Recyclable',
                type: 'bar',
                data: recycVals,
                itemStyle: { color: '#198754', borderRadius: [4, 4, 0, 0] }
            }
        ]
    });
    window.addEventListener('resize', () => chart.resize());
}
