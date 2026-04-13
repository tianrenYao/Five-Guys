/**
 * Dashboard page logic
 */
document.addEventListener('DOMContentLoaded', function () {
    loadSummary();
    loadCarbonTrend();
    loadCarbonByCategory();
    loadWasteComposition();
    loadSDG12();
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
