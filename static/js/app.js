// Net Rate Decomposition Tool - JavaScript Application

// Global variables
let currentChart = null;

// Utility functions
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function formatNumber(value) {
    return new Intl.NumberFormat('en-US').format(value);
}

function formatPercent(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }).format(value / 100);
}

// API helper functions
async function apiRequest(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        showError('Failed to load data. Please try again.');
        throw error;
    }
}

// Error handling
function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function showSuccess(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

// Loading state management
function setLoadingState(element, isLoading) {
    if (isLoading) {
        element.classList.add('loading');
        const spinner = document.createElement('div');
        spinner.className = 'spinner-border spinner-border-sm me-2';
        spinner.setAttribute('role', 'status');
        element.insertBefore(spinner, element.firstChild);
    } else {
        element.classList.remove('loading');
        const spinner = element.querySelector('.spinner-border');
        if (spinner) {
            spinner.remove();
        }
    }
}

// Chart utilities
function createWaterfallChart(canvasId, data) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    if (currentChart) {
        currentChart.destroy();
    }
    
    const labels = [
        'Start Rate',
        'Payer Mix',
        'Allowed Rates', 
        'Units/Visit',
        'CPT Mix',
        'Copay Collection',
        'Write-offs/Denials',
        'Operational',
        'Documentation',
        'End Rate'
    ];
    
    const values = [
        data.start_net_rate,
        data.drivers.payer_mix,
        data.drivers.allowed_rates,
        data.drivers.units_per_visit,
        data.drivers.cpt_mix,
        data.drivers.copay_leakage,
        data.drivers.writeoffs_denials,
        data.drivers.operational_leakage,
        data.drivers.documentation_issues,
        data.end_net_rate
    ];
    
    // Calculate cumulative values for waterfall effect
    let cumulative = data.start_net_rate;
    const chartData = [{
        x: 0,
        y: [0, cumulative],
        backgroundColor: '#007bff'
    }];
    
    for (let i = 1; i < values.length - 1; i++) {
        const change = values[i];
        const newCumulative = cumulative + change;
        
        chartData.push({
            x: i,
            y: [cumulative, newCumulative],
            backgroundColor: change >= 0 ? '#28a745' : '#dc3545'
        });
        
        cumulative = newCumulative;
    }
    
    // End rate
    chartData.push({
        x: labels.length - 1,
        y: [0, data.end_net_rate],
        backgroundColor: '#007bff'
    });
    
    currentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Net Rate Change',
                data: chartData,
                backgroundColor: function(context) {
                    return chartData[context.dataIndex].backgroundColor;
                }
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'x',
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    },
                    title: {
                        display: true,
                        text: 'Net Rate ($)'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw.y;
                            if (Array.isArray(value)) {
                                const change = value[1] - value[0];
                                return `Change: ${formatCurrency(change)}`;
                            }
                            return `Net Rate: ${formatCurrency(value)}`;
                        }
                    }
                }
            },
            onClick: function(event, elements) {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    if (index > 0 && index < labels.length - 1) {
                        const driverMap = {
                            1: 'payer_mix',
                            2: 'allowed_rates',
                            3: 'units_per_visit',
                            4: 'cpt_mix',
                            5: 'copay_leakage',
                            6: 'writeoffs_denials',
                            7: 'operational_leakage',
                            8: 'documentation_issues'
                        };
                        
                        const driver = driverMap[index];
                        if (driver) {
                            window.location.href = `/drill-down/${driver}`;
                        }
                    }
                }
            }
        }
    });
    
    return currentChart;
}

// Date utilities
function getDateRange(period) {
    const now = new Date();
    const endDate = now.toISOString().split('T')[0];
    let startDate;
    
    switch (period) {
        case 'mtd':
            startDate = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0];
            break;
        case 'qtd':
            const quarter = Math.floor(now.getMonth() / 3);
            startDate = new Date(now.getFullYear(), quarter * 3, 1).toISOString().split('T')[0];
            break;
        case 'ytd':
            startDate = new Date(now.getFullYear(), 0, 1).toISOString().split('T')[0];
            break;
        case 'last_month':
            const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
            startDate = lastMonth.toISOString().split('T')[0];
            break;
        default:
            startDate = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate()).toISOString().split('T')[0];
    }
    
    return { startDate, endDate };
}

// Local storage utilities for tracking
function getTrackedItems() {
    const items = localStorage.getItem('trackedItems');
    return items ? JSON.parse(items) : [];
}

function addTrackedItem(item) {
    const items = getTrackedItems();
    items.push({
        ...item,
        id: Date.now().toString(),
        dateAdded: new Date().toISOString()
    });
    localStorage.setItem('trackedItems', JSON.stringify(items));
    return items;
}

function removeTrackedItem(id) {
    const items = getTrackedItems();
    const filtered = items.filter(item => item.id !== id);
    localStorage.setItem('trackedItems', JSON.stringify(filtered));
    return filtered;
}

// Export data utilities
function exportToCSV(data, filename) {
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    
    window.URL.revokeObjectURL(url);
}

function convertToCSV(data) {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvHeaders = headers.join(',');
    
    const csvRows = data.map(row => {
        return headers.map(header => {
            const value = row[header];
            return typeof value === 'string' ? `"${value}"` : value;
        }).join(',');
    });
    
    return [csvHeaders, ...csvRows].join('\n');
}

// Initialize tooltips and other Bootstrap components
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    showError('An unexpected error occurred. Please refresh the page.');
});

// Export for use in other scripts
window.NetRateApp = {
    formatCurrency,
    formatNumber,
    formatPercent,
    apiRequest,
    showError,
    showSuccess,
    setLoadingState,
    createWaterfallChart,
    getDateRange,
    getTrackedItems,
    addTrackedItem,
    removeTrackedItem,
    exportToCSV
};