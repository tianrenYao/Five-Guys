/**
 * Dashboard page logic
 */
document.addEventListener('DOMContentLoaded', function () {
    loadSummary();
    loadCarbonTrend();
    loadCarbonByCategory();
    loadWasteComposition();
    loadSDG12();

    // Role-specific loaders
    const role = window.userRole || '';
    if (role === 'store_staff')           loadStaffView();
    else if (role === 'region_manager')   loadRegionLeaderboard();
    if (role === 'hq_manager' || role === 'admin') loadRiskWatch();
    if (role === 'admin')                 loadSystemHealth();
});

async function loadSummary() {
    const data = await apiFetch('/api/dashboard/summary');
    if (!data || !data.success) return;
    const d = data.data;
    document.getElementById('carbonTotal').textContent = formatNumber(d.carbon_total_kg);
    document.getElementById('wasteTotal').textContent = formatNumber(d.waste_total_kg);
    document.getElementById('recyclingRate').textContent = formatNumber(d.recycling_rate, 1);
    document.getElementById('reportCount').textContent = d.report_count;
}

let _carbonTrendMonths = [];

async function loadCarbonTrend() {
    const data = await apiFetch('/api/dashboard/carbon-trend');
    if (!data || !data.success) return;

    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    _carbonTrendMonths = data.data.months;
    const months = data.data.months.map(m => monthNames[m - 1] || m);
    const values = data.data.values;

    const chart = echarts.init(document.getElementById('chartCarbonTrend'));
    chart.setOption({
        tooltip: { trigger: 'axis', formatter: '{b}: {c} kgCO2e' },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: { type: 'category', data: months, boundaryGap: false },
        yAxis: { type: 'value', name: 'kgCO2e' },
        series: [{
            name: 'Carbon Emissions',
            type: 'line',
            data: values,
            smooth: true,
            areaStyle: { opacity: 0.15 },
            lineStyle: { width: 3 },
            itemStyle: { color: '#dc3545' },
            symbolSize: 8
        }]
    });
    chart.on('click', params => {
        const idx = params.dataIndex;
        const monthNum = _carbonTrendMonths[idx];
        if (monthNum) openDrilldown('carbon_month', null, monthNum);
    });
    window.addEventListener('resize', () => chart.resize());
}

async function loadCarbonByCategory() {
    const data = await apiFetch('/api/dashboard/carbon-by-category');
    if (!data || !data.success) return;

    const colors = {
        electricity: '#ffc107',
        transport: '#0d6efd',
        fuel: '#dc3545',
        commute: '#198754'
    };

    const chartData = data.data.map(d => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: colors[d.name] || '#6c757d' }
    }));

    const chart = echarts.init(document.getElementById('chartCarbonCategory'));
    chart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} kgCO2e ({d}%)' },
        series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: true,
            itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
            label: { show: true, formatter: '{b}\n{d}%' },
            data: chartData.length > 0 ? chartData : [{ name: 'No Data', value: 1, itemStyle: { color: '#e9ecef' } }]
        }]
    });
    chart.on('click', params => { if (params.name !== 'No Data') openDrilldown('carbon_category', params.name); });
    window.addEventListener('resize', () => chart.resize());
}

async function loadWasteComposition() {
    const data = await apiFetch('/api/dashboard/waste-composition');
    if (!data || !data.success) return;

    const colors = ['#198754', '#ffc107', '#dc3545', '#6f42c1', '#0dcaf0'];
    const chartData = data.data.map((d, i) => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: colors[i % colors.length] }
    }));

    const chart = echarts.init(document.getElementById('chartWasteComposition'));
    chart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} kg ({d}%)' },
        series: [{
            type: 'pie',
            radius: '70%',
            itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
            label: { show: true, formatter: '{b}\n{d}%' },
            data: chartData.length > 0 ? chartData : [{ name: 'No Data', value: 1, itemStyle: { color: '#e9ecef' } }]
        }]
    });
    chart.on('click', params => { if (params.name !== 'No Data') openDrilldown('waste_category', params.name); });
    window.addEventListener('resize', () => chart.resize());
}

async function loadSDG12() {
    const data = await apiFetch('/api/dashboard/sdg12');
    if (!data || !data.success) return;
    const d = data.data;

    const bars = [
        { bar: 'sdg12Bar1', val: 'sdg12Val1', score: d.recovery,  label: d.rate_raw != null ? d.rate_raw + '%' : d.recovery + '%' },
        { bar: 'sdg12Bar2', val: 'sdg12Val2', score: d.carbon,    label: d.carbon + ' / 100' },
        { bar: 'sdg12Bar3', val: 'sdg12Val3', score: d.reporting, label: (d.report_count || 0) + ' reports' },
        { bar: 'sdg12Bar4', val: 'sdg12Val4', score: d.coverage,  label: d.coverage + '%' },
    ];
    bars.forEach(({ bar, val, score, label }) => {
        const barEl = document.getElementById(bar);
        const valEl = document.getElementById(val);
        if (barEl) barEl.style.width = score + '%';
        if (valEl) valEl.textContent = label;
    });
}

async function openDrilldown(type, category = null, month = null) {
    const params = new URLSearchParams({ type });
    if (category) params.append('category', category);
    if (month)    params.append('month', month);

    const data = await apiFetch('/api/dashboard/drilldown?' + params);
    if (!data || !data.success || !data.data.length) {
        alert('No drilldown data available.'); return;
    }

    document.getElementById('drilldownTitle').textContent = data.title;
    const modal = new bootstrap.Modal(document.getElementById('drilldownModal'));
    modal.show();

    setTimeout(() => {
        const el    = document.getElementById('chartDrilldown');
        const chart = echarts.init(el);
        const stores = data.data.map(d => d.store);
        const values = data.data.map(d => d.value);
        chart.setOption({
            tooltip: { trigger: 'axis', formatter: `{b}: {c} ${data.unit}` },
            grid: { left: '2%', right: '6%', bottom: '3%', containLabel: true },
            xAxis: { type: 'value', name: data.unit },
            yAxis: { type: 'category', data: stores, axisLabel: { width: 120, overflow: 'truncate' } },
            series: [{
                type: 'bar',
                data: values,
                itemStyle: { color: '#0d6efd', borderRadius: [0, 4, 4, 0] },
                label: { show: true, position: 'right', formatter: p => p.data.toFixed(1) }
            }]
        });
        window.addEventListener('resize', () => chart.resize());
    }, 350);
}

// ─────────────────────────────────────────────────────────────────────
// Role-specific widget loaders
// ─────────────────────────────────────────────────────────────────────

async function loadStaffView() {
    const data = await apiFetch('/api/dashboard/staff-view');
    if (!data || !data.success) return;
    const d = data.data;

    document.getElementById('staffStoreName').textContent = d.store_name || 'My Store';
    document.getElementById('staffStoreCity').textContent = d.store_city || '';
    document.getElementById('staffCarbonNow').textContent  = formatNumber(d.carbon_this_month);
    document.getElementById('staffWasteNow').textContent   = formatNumber(d.waste_this_month);
    document.getElementById('staffRecycleRate').textContent =
        d.recycle_rate > 0 ? `Recycling rate: ${d.recycle_rate}%` : 'No waste recorded yet';

    const momEl = document.getElementById('staffCarbonMoM');
    if (d.carbon_mom_pct === null || d.carbon_mom_pct === undefined) {
        momEl.innerHTML = '<span class="text-muted">No prior month data</span>';
    } else if (d.carbon_mom_pct > 0) {
        momEl.innerHTML = `<span class="text-danger"><i class="bi bi-arrow-up"></i> ${d.carbon_mom_pct}% vs last month</span>`;
    } else {
        momEl.innerHTML = `<span class="text-success"><i class="bi bi-arrow-down"></i> ${Math.abs(d.carbon_mom_pct)}% vs last month</span>`;
    }

    document.getElementById('staffAlertsCount').textContent = d.open_alerts_count;
    const listEl = document.getElementById('staffAlertsList');
    if (!d.recent_alerts || d.recent_alerts.length === 0) {
        listEl.innerHTML = '<li class="list-group-item text-center text-success py-3"><i class="bi bi-check-circle me-1"></i>No open alerts — great job!</li>';
    } else {
        listEl.innerHTML = d.recent_alerts.map(a => `
            <li class="list-group-item d-flex justify-content-between align-items-start">
                <div>
                    <div class="fw-semibold small">${a.alert_type.replaceAll('_', ' ')}</div>
                    <div class="text-muted small">${a.created_at}</div>
                </div>
                <span class="badge bg-danger">${a.actual_value}</span>
            </li>`).join('');
    }
}

async function loadRegionLeaderboard() {
    const data = await apiFetch('/api/dashboard/region-leaderboard');
    if (!data || !data.success) return;
    const { recycling, carbon } = data.data;

    const recyclingEl = document.getElementById('regionRecyclingBody');
    if (recycling.length === 0) {
        recyclingEl.innerHTML = '<tr><td colspan="3" class="text-center text-muted py-3">No data</td></tr>';
    } else {
        recyclingEl.innerHTML = recycling.map((r, i) => {
            const colour = r.rate >= 60 ? 'success' : r.rate >= 40 ? 'warning' : 'danger';
            return `<tr>
                <td class="text-muted">${i + 1}</td>
                <td>${r.store_name}<br><small class="text-muted">${r.region_name || ''}</small></td>
                <td class="text-end"><span class="badge bg-${colour}">${r.rate}%</span></td>
            </tr>`;
        }).join('');
    }

    const carbonEl = document.getElementById('regionCarbonBody');
    if (carbon.length === 0) {
        carbonEl.innerHTML = '<tr><td colspan="3" class="text-center text-muted py-3">No data</td></tr>';
    } else {
        carbonEl.innerHTML = carbon.map((c, i) => `
            <tr>
                <td class="text-muted">${i + 1}</td>
                <td>${c.store_name}<br><small class="text-muted">${c.region_name || ''}</small></td>
                <td class="text-end">${formatNumber(c.total_carbon)}</td>
            </tr>`).join('');
    }
}

async function loadRiskWatch() {
    const data = await apiFetch('/api/dashboard/risk-watch');
    if (!data || !data.success) return;
    const { high_alert_stores, silent_stores, spike_stores } = data.data;

    const renderEmpty = (el, message, ok) => {
        const cls = ok ? 'text-success' : 'text-muted';
        const icon = ok ? 'bi-check-circle' : 'bi-info-circle';
        el.innerHTML = `<li class="list-group-item text-center ${cls} py-3"><i class="bi ${icon} me-1"></i>${message}</li>`;
    };

    const highEl = document.getElementById('riskHighAlertList');
    if (!high_alert_stores.length) renderEmpty(highEl, 'No store has 3+ open alerts', true);
    else highEl.innerHTML = high_alert_stores.map(s => `
        <li class="list-group-item d-flex justify-content-between">
            <div><div class="fw-semibold small">${s.store_name}</div><small class="text-muted">${s.region_name || ''}</small></div>
            <span class="badge bg-danger align-self-center">${s.open_alerts}</span>
        </li>`).join('');

    const spikeEl = document.getElementById('riskSpikeList');
    if (!spike_stores.length) renderEmpty(spikeEl, 'No major carbon spikes detected', true);
    else spikeEl.innerHTML = spike_stores.map(s => `
        <li class="list-group-item">
            <div class="d-flex justify-content-between">
                <div class="fw-semibold small">${s.store_name}</div>
                <span class="badge bg-warning text-dark">+${s.change_pct}%</span>
            </div>
            <small class="text-muted">${s.last_month.toFixed(0)} → ${s.this_month.toFixed(0)} kgCO2e</small>
        </li>`).join('');

    const silentEl = document.getElementById('riskSilentList');
    if (!silent_stores.length) renderEmpty(silentEl, 'All stores reporting this month', true);
    else silentEl.innerHTML = silent_stores.map(s => `
        <li class="list-group-item">
            <div class="fw-semibold small">${s.store_name}</div>
            <small class="text-muted">${s.region_name || ''}</small>
        </li>`).join('');
}

async function loadSystemHealth() {
    const data = await apiFetch('/api/dashboard/system-health');
    if (!data || !data.success) return;
    const d = data.data;

    document.getElementById('shUsers').innerHTML =
        `${d.users_active_30d} <small class="text-muted">/ ${d.users_total}</small>`;
    document.getElementById('shStores').textContent = d.stores_total;
    document.getElementById('shRecords').innerHTML =
        `${d.carbon_today + d.waste_today} <small class="text-muted">(C ${d.carbon_today} / W ${d.waste_today})</small>`;

    const svc = document.getElementById('shServices');
    const aiBadge   = d.ai_configured   ? '<span class="badge bg-success">AI</span>'   : '<span class="badge bg-secondary">AI off</span>';
    const mailBadge = d.mail_configured ? '<span class="badge bg-success">Mail</span>' : '<span class="badge bg-secondary">Mail mock</span>';
    svc.innerHTML = aiBadge + mailBadge;

    const auditEl = document.getElementById('shAuditList');
    if (!d.recent_audit || !d.recent_audit.length) {
        auditEl.innerHTML = '<li class="list-group-item text-center text-muted py-2">No audit entries yet</li>';
    } else {
        const actionColor = a => ({
            CREATE: 'bg-success', UPDATE: 'bg-primary', DELETE: 'bg-danger',
            EXPORT: 'bg-info', LOGIN: 'bg-secondary'
        }[a] || 'bg-secondary');
        auditEl.innerHTML = d.recent_audit.map(a => `
            <li class="list-group-item d-flex justify-content-between align-items-center py-2">
                <div class="small">
                    <span class="badge ${actionColor(a.action)} me-1">${a.action}</span>
                    <strong>${a.actor || 'system'}</strong>
                    ${a.target_type ? `→ <span class="text-muted">${a.target_type}</span>` : ''}
                    ${a.detail ? `<div class="text-muted" style="font-size:0.78rem;">${a.detail}</div>` : ''}
                </div>
                <small class="text-muted">${a.created_at}</small>
            </li>`).join('');
    }
}
