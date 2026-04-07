/**
 * Common utilities for the Sustainability Platform
 */

// Sidebar toggle
document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    if (toggle && sidebar) {
        toggle.addEventListener('click', function () {
            if (window.innerWidth <= 768) {
                sidebar.classList.toggle('show');
            } else {
                sidebar.classList.toggle('collapsed');
            }
        });
    }
});

/**
 * Helper: fetch JSON from API
 */
async function apiFetch(url, options = {}) {
    const defaults = {
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin'
    };
    const resp = await fetch(url, { ...defaults, ...options });
    if (resp.status === 401) {
        window.location.href = '/login';
        return null;
    }
    return resp.json();
}

/**
 * Show alert message in a target element
 */
function showAlert(elementId, message, type = 'danger') {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.className = `alert alert-${type}`;
    el.textContent = message;
    el.classList.remove('d-none');
    setTimeout(() => el.classList.add('d-none'), 5000);
}

/**
 * Format date string for display
 */
function formatDate(dateStr) {
    if (!dateStr) return '-';
    return dateStr.substring(0, 10);
}

/**
 * Format number with thousand separators
 */
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined) return '-';
    return Number(num).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Set today as default date for date inputs
 */
function setDefaultDate(inputId) {
    const el = document.getElementById(inputId);
    if (el && !el.value) {
        el.value = new Date().toISOString().substring(0, 10);
    }
}

/**
 * Load unread alert count and update sidebar + topbar badges.
 * Silently skips if the badge elements don't exist (store_staff has no badge).
 */
async function loadAlertBadge() {
    const sidebar = document.getElementById('sidebarAlertBadge');
    const topbar  = document.getElementById('topbarAlertBadge');
    if (!sidebar && !topbar) return;

    const data = await apiFetch('/api/alert/unread-count');
    if (!data || !data.success) return;

    const count = data.data.count || 0;
    [sidebar, topbar].forEach(el => {
        if (!el) return;
        el.textContent = count > 99 ? '99+' : count;
        el.classList.toggle('d-none', count === 0);
    });
}

// Poll alert badge every 60 seconds after page load
document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('sidebarAlertBadge') ||
        document.getElementById('topbarAlertBadge')) {
        loadAlertBadge();
        setInterval(loadAlertBadge, 60000);
    }
});
