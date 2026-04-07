/**
 * Carbon Tracking page logic
 */

let allFactors = [];
let accessibleStores = [];

document.addEventListener('DOMContentLoaded', function () {
    setDefaultDate('record_date');
    loadStoreSelector();
    loadFactors();
    loadRecords();

    document.getElementById('carbonForm').addEventListener('submit', addRecord);
    document.getElementById('category').addEventListener('change', filterFactors);
    document.getElementById('factor_id').addEventListener('change', updateFactorInfo);
});

async function loadStoreSelector() {
    const data = await apiFetch('/api/dashboard/accessible-stores');
    if (!data || !data.success) return;
    accessibleStores = data.data;

    const storeRow = document.getElementById('storeSelectRow');
    const filterRow = document.getElementById('filterStoreWrapper');
    if (!storeRow && !filterRow) return;

    if (accessibleStores.length <= 1) {
        if (storeRow) storeRow.classList.add('d-none');
        if (filterRow) filterRow.classList.add('d-none');
        return;
    }

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
    const thStore = document.getElementById('thStore');
    if (thStore) thStore.classList.remove('d-none');
}

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
    const dateFrom   = document.getElementById('filterFrom') ? document.getElementById('filterFrom').value : '';
    const dateTo     = document.getElementById('filterTo')   ? document.getElementById('filterTo').value   : '';
    const filterStore = document.getElementById('filterStore') ? document.getElementById('filterStore').value : '';
    let url = '/api/carbon/list?';
    if (dateFrom)    url += `date_from=${dateFrom}&`;
    if (dateTo)      url += `date_to=${dateTo}&`;
    if (filterStore) url += `store_id=${filterStore}&`;

    const data = await apiFetch(url);
    if (!data || !data.success) return;

    const tbody = document.getElementById('recordsBody');
    const showStore = accessibleStores.length > 1;
    if (data.data.length === 0) {
        const cols = showStore ? 8 : 7;
        tbody.innerHTML = `<tr><td colspan="${cols}" class="text-center text-muted py-4">No records found.</td></tr>`;
        return;
    }

    tbody.innerHTML = data.data.map(r => `
        <tr>
            <td>${formatDate(r.record_date)}</td>
            ${showStore ? `<td><small class="text-muted">${r.store_name || '-'}</small></td>` : ''}
            <td><span class="badge bg-secondary">${r.category}</span></td>
            <td>${r.sub_type || '-'}</td>
            <td>${formatNumber(r.activity_value)} ${r.unit || ''}</td>
            <td><strong>${formatNumber(r.total_carbon)}</strong> kgCO2e</td>
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

    const storeEl = document.getElementById('store_id');
    const payload = {
        factor_id:      parseInt(document.getElementById('factor_id').value),
        activity_value: parseFloat(document.getElementById('activity_value').value),
        record_date:    document.getElementById('record_date').value,
        note:           document.getElementById('note').value
    };
    if (storeEl && storeEl.value) payload.store_id = parseInt(storeEl.value);

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

async function scanBill(input) {
    const statusEl = document.getElementById('ocrStatus');
    if (!input.files || !input.files[0]) return;

    const file = input.files[0];
    statusEl.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Scanning bill…';

    const formData = new FormData();
    formData.append('file', file);

    let resp;
    try {
        resp = await fetch('/api/ocr/scan-bill', {
            method: 'POST',
            body: formData
        });
    } catch (err) {
        statusEl.innerHTML = '<span class="text-danger"><i class="bi bi-x-circle me-1"></i>Network error.</span>';
        return;
    }

    const result = await resp.json();
    if (!result.success) {
        statusEl.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle me-1"></i>${result.message || 'OCR failed.'}</span>`;
        return;
    }

    const d = result.data;
    const isMock = d.source === 'mock';
    const label  = isMock ? 'Demo values applied' : 'Bill scanned successfully';

    // Pre-fill category
    if (d.category) {
        const catSel = document.getElementById('category');
        for (const opt of catSel.options) {
            if (opt.value === d.category) { catSel.value = d.category; break; }
        }
        filterFactors();

        // After factors load, try to pick best matching factor
        if (d.category === 'electricity') {
            setTimeout(() => {
                const factSel = document.getElementById('factor_id');
                for (const opt of factSel.options) {
                    if (opt.text.toLowerCase().includes('grid')) { factSel.value = opt.value; break; }
                }
                updateFactorInfo();
            }, 100);
        } else if (d.category === 'fuel') {
            setTimeout(() => {
                const factSel = document.getElementById('factor_id');
                for (const opt of factSel.options) {
                    if (opt.text.toLowerCase().includes('natural_gas')) { factSel.value = opt.value; break; }
                }
                updateFactorInfo();
            }, 100);
        }
    }

    // Pre-fill activity value
    if (d.activity_value) {
        document.getElementById('activity_value').value = d.activity_value;
    }

    // Pre-fill date
    if (d.record_date) {
        document.getElementById('record_date').value = d.record_date;
    }

    // Pre-fill note
    if (d.note) {
        document.getElementById('note').value = d.note;
    }

    const badgeClass = isMock ? 'text-warning' : 'text-success';
    const icon = isMock ? 'bi-exclamation-circle' : 'bi-check-circle';
    statusEl.innerHTML = `<span class="${badgeClass}"><i class="bi ${icon} me-1"></i>${label}${isMock ? ' (mock – upload a real bill for OCR)' : ''}. Please verify before submitting.</span>`;

    // Reset file input so the same file can be re-scanned
    input.value = '';
}
