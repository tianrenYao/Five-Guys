/**
 * Carbon Tracking page logic
 */

let allFactors = [];

document.addEventListener('DOMContentLoaded', function () {
    setDefaultDate('record_date');
    loadFactors();
    loadRecords();

    document.getElementById('carbonForm').addEventListener('submit', addRecord);
    document.getElementById('category').addEventListener('change', filterFactors);
    document.getElementById('factor_id').addEventListener('change', updateFactorInfo);
});

async function loadFactors() {
    const data = await apiFetch('/api/carbon/factors');
    if (!data || !data.success) return;
    allFactors = data.data;

    // Populate category dropdown with unique categories
    const categories = [...new Set(allFactors.map(f => f.category))];
    const catSelect = document.getElementById('category');
    categories.forEach(cat => {
        const opt = document.createElement('option');
        opt.value = cat;
        opt.textContent = cat.charAt(0).toUpperCase() + cat.slice(1);
        catSelect.appendChild(opt);
    });
}

function filterFactors() {
    const category = document.getElementById('category').value;
    const factorSelect = document.getElementById('factor_id');
    factorSelect.innerHTML = '<option value="">Select source...</option>';
    document.getElementById('unitLabel').textContent = 'unit';
    document.getElementById('factorInfo').textContent = '';

    const filtered = allFactors.filter(f => f.category === category);
    filtered.forEach(f => {
        const opt = document.createElement('option');
        opt.value = f.id;
        opt.textContent = `${f.sub_type} (${f.factor} kgCO2e/${f.unit})`;
        opt.dataset.unit = f.unit;
        opt.dataset.factor = f.factor;
        opt.dataset.source = f.source || '';
        factorSelect.appendChild(opt);
    });
}

function updateFactorInfo() {
    const sel = document.getElementById('factor_id');
    const opt = sel.options[sel.selectedIndex];
    if (opt && opt.dataset.unit) {
        document.getElementById('unitLabel').textContent = opt.dataset.unit;
        document.getElementById('factorInfo').textContent =
            `Factor: ${opt.dataset.factor} kgCO2e/${opt.dataset.unit} (${opt.dataset.source})`;
    }
}

async function loadRecords() {
    const dateFrom = document.getElementById('filterFrom').value;
    const dateTo = document.getElementById('filterTo').value;
    let url = '/api/carbon/list?';
    if (dateFrom) url += `date_from=${dateFrom}&`;
    if (dateTo) url += `date_to=${dateTo}&`;

    const data = await apiFetch(url);
    if (!data || !data.success) return;

    const tbody = document.getElementById('recordsBody');
    if (data.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">No records found. Add your first carbon emission record.</td></tr>';
        return;
    }

    tbody.innerHTML = data.data.map(r => `
        <tr>
            <td>${formatDate(r.record_date)}</td>
            <td><span class="badge bg-secondary">${r.category}</span></td>
            <td>${r.sub_type || '-'}</td>
            <td>${formatNumber(r.activity_value)} ${r.unit || ''}</td>
            <td><strong>${formatNumber(r.total_carbon)}</strong></td>
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
        factor_id: parseInt(document.getElementById('factor_id').value),
        activity_value: parseFloat(document.getElementById('activity_value').value),
        record_date: document.getElementById('record_date').value,
        note: document.getElementById('note').value
    };

    if (!payload.factor_id) {
        showAlert('carbonAlert', 'Please select an emission source.');
        btn.disabled = false;
        return;
    }

    const data = await apiFetch('/api/carbon/add', {
        method: 'POST',
        body: JSON.stringify(payload)
    });

    btn.disabled = false;

    if (data && data.success) {
        showAlert('carbonAlert', `Record added! Carbon: ${data.data.total_carbon} kgCO2e`, 'success');
        document.getElementById('carbonForm').reset();
        setDefaultDate('record_date');
        loadRecords();
    } else {
        showAlert('carbonAlert', (data && data.message) || 'Failed to add record');
    }
}

async function deleteRecord(id) {
    if (!confirm('Are you sure you want to delete this record?')) return;

    const data = await apiFetch(`/api/carbon/delete/${id}`, { method: 'DELETE' });
    if (data && data.success) {
        loadRecords();
    } else {
        alert((data && data.message) || 'Failed to delete record');
    }
}
