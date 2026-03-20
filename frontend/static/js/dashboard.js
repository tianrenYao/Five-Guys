/**
 * Dashboard page logic
 */
document.addEventListener('DOMContentLoaded', function () {
    loadSummary();
    loadCarbonTrend();
    loadCarbonByCategory();
    loadWasteComposition();
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

async function loadCarbonTrend() {
    const data = await apiFetch('/api/dashboard/carbon-trend');
    if (!data || !data.success) return;

    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
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
    window.addEventListener('resize', () => chart.resize());
}
