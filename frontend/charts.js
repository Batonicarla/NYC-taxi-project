/**
 * Chart Management for NYC Taxi Analysis Dashboard
 */

class ChartManager {
    constructor() {
        this.charts = {};
        this.readThemeColors();
    }
    
    readThemeColors() {
        const cs = getComputedStyle(document.documentElement);
        this.chartColors = {
            primary: cs.getPropertyValue('--primary-color').trim() || '#667eea',
            secondary: cs.getPropertyValue('--accent-color').trim() || '#22d3ee',
            success: cs.getPropertyValue('--success-color').trim() || '#27ae60',
            warning: cs.getPropertyValue('--warning-color').trim() || '#f39c12',
            danger: cs.getPropertyValue('--error-color').trim() || '#e74c3c',
            info: '#3498db',
            light: '#ecf0f1',
            dark: '#2c3e50'
        };
    }
    
    initializeAll(data) {
        console.log('Initializing charts with data:', data);
        
        try {
            // Destroy existing charts first
            this.destroyAll();
            
            this.createHourlyChart(data.hourly);
            this.createSpeedChart(data.speed);
            this.createDailyChart(data.daily);
            this.createEfficiencyChart(data.efficiency);
            
            console.log('All charts initialized successfully');
        } catch (error) {
            console.error('Error initializing charts:', error);
        }
    }
    
    retheme() {
        this.readThemeColors();
        // Rebuild charts with new colors
        const snapshot = {
            hourly: this.charts.hourly?.data ? {
                labels: this.charts.hourly.data.labels,
                tripCounts: this.charts.hourly.data.datasets[0].data,
                avgSpeeds: this.charts.hourly.data.datasets[1].data,
            } : null,
            speed: this.charts.speed?.data ? {
                labels: this.charts.speed.data.labels,
                counts: this.charts.speed.data.datasets[0].data,
            } : null,
            daily: this.charts.daily?.data ? {
                labels: this.charts.daily.data.labels,
                trips: this.charts.daily.data.datasets[0].data,
                distances: this.charts.daily.data.datasets[1].data,
            } : null,
            efficiency: this.charts.efficiency?.data ? {
                labels: this.charts.efficiency.data.labels,
                counts: this.charts.efficiency.data.datasets[0].data,
            } : null
        };
        this.destroyAll();
        if (snapshot.hourly) {
            // Recreate quickly using existing helpers by faking data structures
            const hours = snapshot.hourly.labels.map(l => ({ hour: parseInt(l), trip_count: 0 }));
        }
        // Simpler: just trigger a full reload via app if available
        if (window.dashboard) {
            window.dashboard.loadChartData();
        }
    }
    
    destroyAll() {
        Object.keys(this.charts).forEach(key => {
            if (this.charts[key] && this.charts[key].destroy) {
                this.charts[key].destroy();
            }
        });
        this.charts = {};
    }
    
    createHourlyChart(hourlyData) {
        const ctx = document.getElementById('hourlyChart');
        if (!ctx || !hourlyData) {
            console.warn('Hourly chart canvas or data not available');
            return;
        }
        
        // Sort data by hour
        const sortedData = hourlyData.sort((a, b) => a.hour - b.hour);
        
        const hours = sortedData.map(item => `${item.hour}:00`);
        const tripCounts = sortedData.map(item => item.trip_count);
        const avgSpeeds = sortedData.map(item => parseFloat(item.avg_speed || 0));
        
        this.charts.hourly = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: hours,
                datasets: [
                    {
                        label: 'Trip Count',
                        data: tripCounts,
                        backgroundColor: this.chartColors.primary + '80',
                        borderColor: this.chartColors.primary,
                        borderWidth: 2,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Avg Speed (km/h)',
                        data: avgSpeeds,
                        type: 'line',
                        backgroundColor: this.chartColors.warning + '20',
                        borderColor: this.chartColors.warning,
                        borderWidth: 3,
                        fill: false,
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Hourly Trip Volume and Average Speed',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                if (context.datasetIndex === 0) {
                                    return `${context.parsed.y.toLocaleString()} trips`;
                                } else {
                                    return `${context.parsed.y.toFixed(1)} km/h average speed`;
                                }
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Hour of Day'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Trip Count'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString();
                            }
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Average Speed (km/h)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(1) + ' km/h';
                            }
                        }
                    }
                }
            }
        });
    }
    
    createSpeedChart(speedData) {
        const ctx = document.getElementById('speedChart');
        if (!ctx || !speedData) {
            console.warn('Speed chart canvas or data not available');
            return;
        }
        
        const speedRanges = speedData.map(item => item.speed_range);
        const tripCounts = speedData.map(item => item.trip_count);
        
        // Create vibrant color palette for speed ranges
        const colorPalette = [
            'rgba(239, 68, 68, 0.8)',    // Red - Very slow (0-10)
            'rgba(251, 146, 60, 0.8)',   // Orange - Slow (10-20)
            'rgba(250, 204, 21, 0.8)',   // Yellow - Moderate (20-30)
            'rgba(34, 197, 94, 0.8)',    // Green - Good (30-40)
            'rgba(59, 130, 246, 0.8)',   // Blue - Fast (40-50)
            'rgba(147, 51, 234, 0.8)'    // Purple - Very fast (50+)
        ];
        
    const colors = colorPalette.slice(0, speedRanges.length);
        
        this.charts.speed = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: speedRanges,
                datasets: [{
                    label: 'Trip Count',
                    data: tripCounts,
                    backgroundColor: colors,
                    borderColor: colors.map(color => color.replace('0.8', '1')),
                    borderWidth: 2,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Trip Speed Distribution',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed.toLocaleString()} trips (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    createDailyChart(dailyData) {
        const ctx = document.getElementById('dailyChart');
        if (!ctx || !dailyData) {
            console.warn('Daily chart canvas or data not available');
            return;
        }
        
        // Sort data by date and take last 30 days
        const sortedData = dailyData
            .sort((a, b) => new Date(a.date) - new Date(b.date))
            .slice(-30);
        
        const dates = sortedData.map(item => {
            const date = new Date(item.date);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
        const tripCounts = sortedData.map(item => item.trip_count);
        const avgDistances = sortedData.map(item => parseFloat(item.avg_distance || 0));
        
        this.charts.daily = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Daily Trips',
                        data: tripCounts,
                        backgroundColor: this.chartColors.primary + '20',
                        borderColor: this.chartColors.primary,
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Avg Distance (km)',
                        data: avgDistances,
                        backgroundColor: this.chartColors.success + '20',
                        borderColor: this.chartColors.success,
                        borderWidth: 3,
                        fill: false,
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Daily Trip Trends (Last 30 Days)',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                if (context.datasetIndex === 0) {
                                    return `${context.parsed.y.toLocaleString()} trips on this day`;
                                } else {
                                    return `${context.parsed.y.toFixed(2)} km average distance`;
                                }
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Trip Count'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString();
                            }
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Average Distance (km)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(1) + ' km';
                            }
                        }
                    }
                }
            }
        });
    }
    
    createEfficiencyChart(efficiencyData) {
        const ctx = document.getElementById('efficiencyChart');
        if (!ctx || !efficiencyData) {
            console.warn('Efficiency chart canvas or data not available');
            return;
        }
        
        // Create efficiency distribution data
        const efficiencyRanges = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'];
        const totalTrips = efficiencyData.total_trips || 1;
        const highEfficiencyTrips = efficiencyData.high_efficiency_trips || 0;
        const lowEfficiencyTrips = efficiencyData.low_efficiency_trips || 0;
        
        // Estimate distribution (simplified)
        const distributionData = [
            Math.floor(lowEfficiencyTrips * 0.3),
            Math.floor(lowEfficiencyTrips * 0.7),
            Math.floor((totalTrips - highEfficiencyTrips - lowEfficiencyTrips) * 0.6),
            Math.floor((totalTrips - highEfficiencyTrips - lowEfficiencyTrips) * 0.4),
            highEfficiencyTrips
        ];
        
        this.charts.efficiency = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: efficiencyRanges,
                datasets: [{
                    label: 'Trip Count',
                    data: distributionData,
                    backgroundColor: [
                        this.chartColors.danger + '80',
                        this.chartColors.warning + '80',
                        this.chartColors.info + '80',
                        this.chartColors.success + '80',
                        this.chartColors.primary + '80'
                    ],
                    borderColor: [
                        this.chartColors.danger,
                        this.chartColors.warning,
                        this.chartColors.info,
                        this.chartColors.success,
                        this.chartColors.primary
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Trip Efficiency Score Distribution',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed.y / total) * 100).toFixed(1);
                                return `${context.parsed.y.toLocaleString()} trips (${percentage}%)`;
                            },
                            afterLabel: function(context) {
                                const range = context.label;
                                let description = '';
                                
                                switch(range) {
                                    case '0-20%':
                                        description = 'Very low efficiency - heavy traffic/delays';
                                        break;
                                    case '20-40%':
                                        description = 'Low efficiency - moderate traffic';
                                        break;
                                    case '40-60%':
                                        description = 'Average efficiency - normal conditions';
                                        break;
                                    case '60-80%':
                                        description = 'Good efficiency - light traffic';
                                        break;
                                    case '80-100%':
                                        description = 'Excellent efficiency - optimal conditions';
                                        break;
                                }
                                
                                return description;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Efficiency Score Range'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Number of Trips'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
        
        // Add efficiency metrics text
        this.addEfficiencyMetrics(efficiencyData);
    }
    
    addEfficiencyMetrics(efficiencyData) {
        const chartContainer = document.getElementById('efficiencyChart').parentElement;
        
        // Remove existing metrics if any
        const existingMetrics = chartContainer.querySelector('.efficiency-metrics');
        if (existingMetrics) {
            existingMetrics.remove();
        }
        
        const metricsDiv = document.createElement('div');
        metricsDiv.className = 'efficiency-metrics';
        metricsDiv.style.cssText = `
            margin-top: 1rem;
            padding: 1rem;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 8px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            font-size: 0.9rem;
        `;
        
        const avgEfficiency = parseFloat(efficiencyData.avg_efficiency || 0).toFixed(1);
        const medianEfficiency = parseFloat(efficiencyData.median_efficiency || 0).toFixed(1);
        const avgIdleTime = Math.floor(efficiencyData.avg_idle_time || 0);
        
        metricsDiv.innerHTML = `
            <div>
                <strong>Average Efficiency:</strong><br>
                <span style="color: ${this.chartColors.primary}; font-size: 1.2em; font-weight: bold;">${avgEfficiency}%</span>
            </div>
            <div>
                <strong>Median Efficiency:</strong><br>
                <span style="color: ${this.chartColors.success}; font-size: 1.2em; font-weight: bold;">${medianEfficiency}%</span>
            </div>
            <div>
                <strong>Avg Idle Time:</strong><br>
                <span style="color: ${this.chartColors.warning}; font-size: 1.2em; font-weight: bold;">${avgIdleTime}s</span>
            </div>
        `;
        
        chartContainer.appendChild(metricsDiv);
    }
    
    updateChart(chartId, newData) {
        if (this.charts[chartId]) {
            this.charts[chartId].data = newData;
            this.charts[chartId].update();
        }
    }
    
    destroyChart(chartId) {
        if (this.charts[chartId]) {
            this.charts[chartId].destroy();
            delete this.charts[chartId];
        }
    }
    
    destroyAll() {
        Object.keys(this.charts).forEach(chartId => {
            this.destroyChart(chartId);
        });
    }
    
    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.resize === 'function') {
                chart.resize();
            }
        });
    }
}

// Make ChartManager available globally
window.ChartManager = ChartManager;

// Handle window resize
window.addEventListener('resize', () => {
    if (window.dashboard && window.dashboard.chartManager) {
        window.dashboard.chartManager.resizeCharts();
    }
});
