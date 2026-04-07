/**
 * Waste Management page logic
 */

let accessibleStores = [];

document.addEventListener('DOMContentLoaded', function () {
    setDefaultDate('record_date');
    loadStoreSelector();
    loadCategories();
    loadRecords();
    loadStats();

    document.getElementById('wasteForm').addEventListener('submit', addRecord);
});

async function loadStoreSelector() {
    const data = await apiFetch('/api/dashboard/accessible-stores');
    if (!data || !data.success) return;
    accessibleStores = data.data;

    const storeRow  = document.getElementById('storeSelectRow');
    const filterRow = document.getElementById('filterStoreWrapper');
    if (accessibleStores.length <= 1) return;

    const buildOptions = (includeAll) => {
        let opts = includeAll ? '<option value="">All stores</option>' : '<option value="">Select store...</option>';
        accessibleStores.forEach(s => {
            opts += `<option value="${s.id}">${s.region_name} · ${s.name}</option>`;
        });
        return opts;
    };

    const formSel = document.getElementById('store_id');
    if (formSel && storeRow) {
        formSel.innerHTML = buildOptions(false);
        storeRow.classList.remove('d-none');
    }
    const filterSel = document.getElementById('filterStore');
    if (filterSel && filterRow) {
        filterSel.innerHTML = buildOptions(true);
        filterRow.classList.remove('d-none');
    }
}

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
    const dateFrom    = document.getElementById('filterFrom')   ? document.getElementById('filterFrom').value   : '';
    const dateTo      = document.getElementById('filterTo')     ? document.getElementById('filterTo').value     : '';
    const filterStore = document.getElementById('filterStore')  ? document.getElementById('filterStore').value  : '';
    let url = '/api/waste/list?';
    if (dateFrom)    url += `date_from=${dateFrom}&`;
    if (dateTo)      url += `date_to=${dateTo}&`;
    if (filterStore) url += `store_id=${filterStore}&`;

    const data = await apiFetch(url);
    if (!data || !data.success) return;

    const tbody = document.getElementById('recordsBody');
    const showStore = accessibleStores.length > 1;
    const thStore = document.getElementById('thStore');
    if (thStore) thStore.classList.toggle('d-none', !showStore);

    if (data.data.length === 0) {
        const cols = showStore ? 9 : 8;
        tbody.innerHTML = `<tr><td colspan="${cols}" class="text-center text-muted py-4">No records found.</td></tr>`;
        return;
    }

    tbody.innerHTML = data.data.map(r => {
        const recycRate = r.weight_kg > 0
            ? Math.round((r.recycled_kg || 0) / r.weight_kg * 100) : 0;
        const rateColor = recycRate >= 30 ? 'success' : 'danger';
        return `
        <tr>
            <td>${formatDate(r.record_date)}</td>
            ${showStore ? `<td><small class="text-muted">${r.store_name || '-'}</small></td>` : ''}
            <td>${r.category_name}</td>
            <td><span class="badge bg-light text-dark">${r.source_type || '-'}</span></td>
            <td>${formatNumber(r.weight_kg)}</td>
            <td>${formatNumber(r.recycled_kg || 0)}
                <span class="badge bg-${rateColor} ms-1">${recycRate}%</span></td>
            <td><small>${r.disposal_method || '-'}</small></td>
            <td><small class="text-muted">${r.recorded_by || '-'}</small></td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteRecord(${r.id})" title="Delete">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        </tr>`;
    }).join('');
}

async function addRecord(e) {
    e.preventDefault();
    const btn = document.getElementById('submitBtn');
    btn.disabled = true;

    const storeEl = document.getElementById('store_id');
    const payload = {
        category_id:     parseInt(document.getElementById('category_id').value),
        weight_kg:       parseFloat(document.getElementById('weight_kg').value),
        recycled_kg:     parseFloat(document.getElementById('recycled_kg').value || 0),
        source_type:     document.getElementById('source_type').value,
        disposal_method: document.getElementById('disposal_method').value,
        record_date:     document.getElementById('record_date').value,
        note:            document.getElementById('note').value
    };
    if (storeEl && storeEl.value) payload.store_id = parseInt(storeEl.value);

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
    const recycVals = data.data.map(r => r.total_recycled_kg);
    const rateVals  = data.data.map(r => r.recovery_rate_pct);

    const chart = echarts.init(document.getElementById('chartWasteStats'));
    chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['Total (kg)', 'Recycled (kg)', 'Rate (%)'], bottom: 0 },
        grid: { left: '3%', right: '8%', bottom: '15%', containLabel: true },
        xAxis: { type: 'category', data: months },
        yAxis: [
            { type: 'value', name: 'kg' },
            { type: 'value', name: '%', max: 100, axisLabel: { formatter: '{value}%' } }
        ],
        series: [
            { name: 'Total (kg)',    type: 'bar',  data: totalVals, yAxisIndex: 0, itemStyle: { color: '#ffc107', borderRadius: [4,4,0,0] } },
            { name: 'Recycled (kg)', type: 'bar',  data: recycVals, yAxisIndex: 0, itemStyle: { color: '#198754', borderRadius: [4,4,0,0] } },
            { name: 'Rate (%)',      type: 'line', data: rateVals,  yAxisIndex: 1, smooth: true,
              lineStyle: { color: '#0dcaf0' }, itemStyle: { color: '#0dcaf0' } }
        ]
    });
    window.addEventListener('resize', () => chart.resize());
}
