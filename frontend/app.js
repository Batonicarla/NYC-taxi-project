/**
 * NYC Taxi Analysis Dashboard - Main Application JavaScript
 */

class TaxiDashboard {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.currentFilters = {};
        this.currentPage = 1;
        this.pageSize = 50;
        this.charts = {};
        this.data = {
            trips: [],
            statistics: {},
            insights: []
        };
        
        this.init();
    }
    
    // Unified fetch with retry and cache-busting
    async fetchWithRetry(url, options = {}, retries = 2, delay = 500) {
        const withCacheBuster = (u) => {
            const sep = u.includes('?') ? '&' : '?';
            return `${u}${sep}_ts=${Date.now()}`; // avoid caches (and 304/stale)
        };

        const finalUrl = withCacheBuster(url);
        const finalOptions = {
            cache: 'no-store',
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                ...(options.headers || {})
            },
            ...options
        };

        let lastErr;
        for (let i = 0; i < Math.max(1, retries); i++) {
            try {
                const res = await fetch(finalUrl, finalOptions);
                if (!res.ok) {
                    const text = await res.text().catch(() => '');
                    lastErr = new Error(`HTTP ${res.status}: ${text || res.statusText}`);
                    if (i < retries - 1) {
                        await new Promise(r => setTimeout(r, delay));
                        continue;
                    }
                    throw lastErr;
                }
                // Attempt JSON parse
                return await res.json();
            } catch (err) {
                lastErr = err;
                if (i < retries - 1) {
                    await new Promise(r => setTimeout(r, delay));
                    continue;
                }
                throw lastErr;
            }
        }
    }

    init() {
        console.log('Initializing NYC Taxi Dashboard...');
        this.setupEventListeners();
        this.setupTheme();
        this.checkApiConnection();
        this.loadInitialData();
        // Collapse filters by default for a cleaner top area
        this.setFiltersCollapsed(true);
    }
    
    setupEventListeners() {
        // Filter controls
        const applyFilters = document.getElementById('applyFilters');
        if (applyFilters) {
            applyFilters.addEventListener('click', () => this.applyFilters());
        }
        
        const clearFilters = document.getElementById('clearFilters');
        if (clearFilters) {
            clearFilters.addEventListener('click', () => this.clearFilters());
        }
        
        const exportData = document.getElementById('exportData');
        if (exportData) {
            exportData.addEventListener('click', () => this.exportData());
        }
        
        const refreshData = document.getElementById('refreshData');
        if (refreshData) {
            refreshData.addEventListener('click', () => this.refreshData());
        }
        
        // Page size change
        const pageSize = document.getElementById('pageSize');
        if (pageSize) {
            pageSize.addEventListener('change', (e) => {
                this.pageSize = parseInt(e.target.value);
                this.currentPage = 1;
                this.loadTripsData();
            });
        }
        
        // Pagination controls
        const prevPage = document.getElementById('prevPage');
        if (prevPage) {
            prevPage.addEventListener('click', () => {
                if (this.currentPage > 1) {
                    this.currentPage--;
                    this.loadTripsData();
                }
            });
        }
        
        const nextPage = document.getElementById('nextPage');
        if (nextPage) {
            nextPage.addEventListener('click', () => {
                this.currentPage++;
                this.loadTripsData();
            });
        }
        
        // Modal controls
        const modalClose = document.getElementById('modalClose');
        if (modalClose) {
            modalClose.addEventListener('click', () => this.closeModal());
        }
        
        const modal = document.getElementById('modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target.id === 'modal') this.closeModal();
            });
        }
        
        // Footer links (if they exist)
        const aboutLink = document.getElementById('aboutLink');
        if (aboutLink) {
            aboutLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.showAboutModal();
            });
        }
        
        const methodologyLink = document.getElementById('methodologyLink');
        if (methodologyLink) {
            methodologyLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.showMethodologyModal();
            });
        }
        
        const dataSourceLink = document.getElementById('dataSourceLink');
        if (dataSourceLink) {
            dataSourceLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.showDataSourceModal();
            });
        }

        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        const toggleFilters = document.getElementById('toggleFilters');
        if (toggleFilters) {
            toggleFilters.addEventListener('click', () => {
                const panel = document.getElementById('filterPanel');
                const collapsed = !panel.classList.contains('collapsed');
                this.setFiltersCollapsed(collapsed);
            });
        }
    }

    setFiltersCollapsed(collapsed) {
        const panel = document.getElementById('filterPanel');
        const btn = document.getElementById('toggleFilters');
        if (!panel || !btn) return;
        if (collapsed) {
            panel.classList.add('collapsed');
            btn.setAttribute('aria-expanded', 'false');
            btn.textContent = 'Show';
        } else {
            panel.classList.remove('collapsed');
            btn.setAttribute('aria-expanded', 'true');
            btn.textContent = 'Hide';
        }
    }

    setupTheme() {
        try {
            const saved = localStorage.getItem('taxi_theme');
            if (saved === 'dark') {
                document.documentElement.classList.add('theme-dark');
            } else if (saved === 'light') {
                document.documentElement.classList.remove('theme-dark');
            }
        } catch {}
    }

    toggleTheme() {
        const root = document.documentElement;
        const dark = root.classList.toggle('theme-dark');
        try { localStorage.setItem('taxi_theme', dark ? 'dark' : 'light'); } catch {}
        this.showToast(dark ? 'Dark mode enabled' : 'Light mode enabled', 'success');
        // Allow charts to be recreated to apply theme colors if needed
        if (this.chartManager && this.chartManager.retheme) {
            this.chartManager.retheme();
        }
    }

    showToast(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        const el = document.createElement('div');
        el.className = `toast ${type}`;
        el.textContent = message;
        container.appendChild(el);
        setTimeout(() => {
            el.style.opacity = '0';
            el.style.transition = 'opacity 300ms ease';
            setTimeout(() => el.remove(), 350);
        }, 2500);
    }
    
    async checkApiConnection() {
        try {
            const data = await this.fetchWithRetry(`${this.apiBaseUrl}/health`, {}, 2, 300);
            this.updateApiStatus('connected', 'API Connected');
            console.log('API connection successful', data);
        } catch (error) {
            console.error('API connection failed:', error);
            this.updateApiStatus('error', 'API Connection Failed');
            this.showErrorMessage('Unable to connect to the backend API. Please ensure the server is running.');
        }
    }
    
    updateApiStatus(status, text) {
        const statusDot = document.getElementById('apiStatus');
        const statusText = document.getElementById('apiStatusText');
        
        statusDot.className = `status-dot ${status === 'error' ? 'error' : ''}`;
        statusText.textContent = text;
    }
    
    async loadInitialData() {
        this.showLoading(true);
        
        try {
            // Load each section independently - don't let one failure stop the others
            const results = await Promise.allSettled([
                this.loadStatistics(),
                this.loadTripsData(),
                this.loadInsights(),
                this.loadChartData()
            ]);
            
            // Log which sections loaded successfully
            const labels = ['Statistics', 'Trips Data', 'Insights', 'Chart Data'];
            results.forEach((result, index) => {
                if (result.status === 'fulfilled') {
                    console.log(`✓ ${labels[index]} loaded successfully`);
                } else {
                    console.warn(`✗ ${labels[index]} failed:`, result.reason);
                }
            });
            
            console.log('Dashboard initialization completed');
        } catch (error) {
            console.error('Error during dashboard initialization:', error);
        } finally {
            this.showLoading(false);
        }
    }
    
    async loadStatistics() {
        try {
            const data = await this.fetchWithRetry(`${this.apiBaseUrl}/stats/summary`, {}, 2, 300);
            this.data.statistics = data.statistics;
            this.updateStatisticsDisplay();
        } catch (error) {
            console.error('Error loading statistics:', error);
            this.showErrorInStats();
        }
    }
    
    updateStatisticsDisplay() {
        const stats = this.data.statistics;
        
        // Update stat cards with null checks
        const totalTripsEl = document.getElementById('totalTrips');
        if (totalTripsEl) totalTripsEl.textContent = this.formatNumber(stats.total_trips);
        
        const avgDurationEl = document.getElementById('avgDuration');
        if (avgDurationEl) avgDurationEl.textContent = this.formatDuration(stats.avg_duration);
        
        const avgDistanceEl = document.getElementById('avgDistance');
        if (avgDistanceEl) avgDistanceEl.textContent = `${parseFloat(stats.avg_distance || 0).toFixed(1)} km`;
        
        const avgSpeedEl = document.getElementById('avgSpeed');
        if (avgSpeedEl) avgSpeedEl.textContent = `${parseFloat(stats.avg_speed || 0).toFixed(1)} km/h`;
        
        const avgPassengersEl = document.getElementById('avgPassengers');
        if (avgPassengersEl) avgPassengersEl.textContent = parseFloat(stats.avg_passengers || 0).toFixed(1);
        
        // Calculate weekend ratio (if element exists)
        const weekendRatioEl = document.getElementById('weekendRatio');
        if (weekendRatioEl) {
            const weekendTrips = stats.weekend_trips || 0;
            const totalTrips = stats.total_trips || 1;
            const weekendRatio = (weekendTrips / totalTrips * 100).toFixed(1);
            weekendRatioEl.textContent = `${weekendRatio}%`;
        }
    }
    
    showErrorInStats() {
        const statValues = ['totalTrips', 'avgDuration', 'avgDistance', 'avgSpeed', 'avgPassengers', 'weekendRatio'];
        statValues.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = 'Error';
            }
        });
    }
    
    async loadTripsData() {
        try {
            const queryParams = new URLSearchParams({
                page: this.currentPage,
                limit: this.pageSize,
                ...this.currentFilters
            });
            const data = await this.fetchWithRetry(`${this.apiBaseUrl}/trips?${queryParams.toString()}`, {}, 2, 300);
            this.data.trips = data.trips;
            this.updateTripsTable(data);
            this.updatePagination(data);
        } catch (error) {
            console.error('Error loading trips data:', error);
            this.showErrorInTable('Error loading trip data');
            // Don't re-throw - let other sections load
        }
    }
    
    updateTripsTable(data) {
        const tbody = document.getElementById('tripsTableBody');
        
        if (!data.trips || data.trips.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="loading-cell">No trips found matching the current filters</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.trips.map(trip => `
            <tr onclick="dashboard.showTripDetails('${trip.trip_id}')" style="cursor: pointer;">
                <td>${trip.trip_id}</td>
                <td>${this.formatDateTime(trip.pickup_datetime)}</td>
                <td>${this.formatDuration(trip.trip_duration)}</td>
                <td>${parseFloat(trip.trip_distance || 0).toFixed(2)} km</td>
                <td>${parseFloat(trip.trip_speed || 0).toFixed(1)} km/h</td>
                <td>${trip.passenger_count}</td>
                <td>${trip.time_of_day}</td>
                <td>${parseFloat(trip.trip_efficiency || 0).toFixed(1)}%</td>
            </tr>
        `).join('');
    }
    
    updatePagination(data) {
        const infoEl = document.getElementById('paginationInfo');
        const controlsEl = document.querySelector('#paginationControls .pagination-controls');
        if (!infoEl || !controlsEl) {
            console.warn('Pagination info or controls container not found');
            return;
        }

        const totalPages = Math.max(1, data.total_pages || 1);
        const currentPage = Math.max(1, data.page || 1);
        const total = data.total_count || 0;
        const pageSize = data.limit || this.pageSize;
        const start = total === 0 ? 0 : (currentPage - 1) * pageSize + 1;
        const end = Math.min(total, currentPage * pageSize);

        infoEl.textContent = `Showing ${start}-${end} of ${total} trips`;

        let html = '';
        // Prev arrow
        html += `<button class="pagination-btn icon" ${currentPage <= 1 ? 'disabled' : ''} onclick="dashboard.goToPage(${currentPage - 1})">←</button>`;

        // Page numbers with ellipses
        const windowSize = 2;
        const startPage = Math.max(1, currentPage - windowSize);
        const endPage = Math.min(totalPages, currentPage + windowSize);

        if (startPage > 1) {
            html += `<button class="pagination-btn" onclick="dashboard.goToPage(1)">1</button>`;
            if (startPage > 2) html += `<span class="pagination-ellipsis">…</span>`;
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="pagination-btn${i === currentPage ? ' active' : ''}" onclick="dashboard.goToPage(${i})">${i}</button>`;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) html += `<span class="pagination-ellipsis">…</span>`;
            html += `<button class="pagination-btn" onclick="dashboard.goToPage(${totalPages})">${totalPages}</button>`;
        }

        // Next arrow
        html += `<button class="pagination-btn icon" ${currentPage >= totalPages ? 'disabled' : ''} onclick="dashboard.goToPage(${currentPage + 1})">→</button>`;

        controlsEl.innerHTML = html;
    }
    
    async loadInsights() {
        try {
            const data = await this.fetchWithRetry(`${this.apiBaseUrl}/insights/comprehensive`, {}, 2, 300);
            this.data.insights = data.insights;
            this.updateInsightsDisplay();
        } catch (error) {
            console.error('Error loading insights:', error);
            this.showErrorInInsights();
        }
    }
    
    updateInsightsDisplay() {
        const insightsGrid = document.getElementById('insightsGrid');
        if (!insightsGrid) {
            console.warn('Insights grid element not found');
            return;
        }
        
        if (!this.data.insights || this.data.insights.length === 0) {
            insightsGrid.innerHTML = `
                <div class="insight-card">
                    <div class="insight-header">
                        <h4>No Insights Available</h4>
                    </div>
                    <div class="insight-content">
                        <p>Unable to generate insights from the current data.</p>
                    </div>
                </div>
            `;
            return;
        }
        
        insightsGrid.innerHTML = this.data.insights.map(insight => `
            <div class="insight-card">
                <div class="insight-header">
                    <h4>${insight.title}</h4>
                    <span class="insight-category ${this.getInsightCategory(insight)}">${insight.insight_type}</span>
                </div>
                <div class="insight-content">
                    <p>${insight.description}</p>
                    ${this.formatInsightMetrics(insight.data)}
                </div>
            </div>
        `).join('');
    }
    
    getInsightCategory(insight) {
        if (insight.insight_type === 'performance_metric') return 'positive';
        if (insight.insight_type === 'temporal_pattern') return 'neutral';
        if (insight.insight_type === 'geographic_pattern') return 'concern';
        return 'neutral';
    }
    
    formatInsightMetrics(data) {
        if (!data) return '';
        
        let html = '<div class="insight-metrics">';
        
        Object.entries(data).forEach(([key, value]) => {
            if (typeof value === 'number') {
                html += `<span class="insight-metric">${key}: ${value.toFixed(1)}</span>`;
            } else if (typeof value === 'object' && value !== null) {
                // Handle nested objects
                Object.entries(value).forEach(([subKey, subValue]) => {
                    if (typeof subValue === 'number') {
                        html += `<span class="insight-metric">${subKey}: ${subValue.toFixed(1)}</span>`;
                    }
                });
            }
        });
        
        html += '</div>';
        return html;
    }
    
    showErrorInInsights() {
        const insightsGrid = document.getElementById('insightsGrid');
        insightsGrid.innerHTML = `
            <div class="insight-card">
                <div class="insight-header">
                    <h4>Error Loading Insights</h4>
                </div>
                <div class="insight-content">
                    <p>Unable to load data insights. Please try refreshing the page.</p>
                </div>
            </div>
        `;
    }
    
    async loadChartData() {
        const chartData = {
            hourly: [],
            speed: [],
            daily: [],
            efficiency: {}
        };

        // Use class-level fetchWithRetry

        // Load hourly stats with retry
        try {
            const data = await this.fetchWithRetry(`${this.apiBaseUrl}/stats/hourly`, {}, 2, 500);
            if (data && data.hourly_stats) {
                chartData.hourly = data.hourly_stats;
                console.log(`✓ Loaded ${chartData.hourly.length} hourly data points`);
            } else {
                console.error('Hourly data response invalid:', data);
            }
        } catch (error) {
            console.error('Failed to load hourly data:', error);
        }

        // Load speed distribution with retry
        try {
            const data = await this.fetchWithRetry(`${this.apiBaseUrl}/insights/speed`, {}, 2, 500);
            if (data && data.speed_distribution) {
                chartData.speed = data.speed_distribution;
                console.log(`✓ Loaded ${chartData.speed.length} speed distribution points`);
            } else {
                console.error('Speed data response invalid:', data);
            }
        } catch (error) {
            console.error('Failed to load speed data:', error);
        }

        // Load daily stats with retry
        try {
            const data = await this.fetchWithRetry(`${this.apiBaseUrl}/stats/daily?days=30`, {}, 2, 500);
            if (data && data.daily_stats) {
                chartData.daily = data.daily_stats;
                console.log(`✓ Loaded ${chartData.daily.length} daily data points`);
            } else {
                console.error('Daily data response invalid:', data);
            }
        } catch (error) {
            console.error('Failed to load daily data:', error);
        }

        // Load efficiency metrics with retry
        try {
            const data = await this.fetchWithRetry(`${this.apiBaseUrl}/insights/efficiency`, {}, 2, 500);
            if (data && data.efficiency_metrics) {
                chartData.efficiency = data.efficiency_metrics;
                console.log(`✓ Loaded efficiency metrics`);
            } else {
                console.error('Efficiency data response invalid:', data);
            }
        } catch (error) {
            console.error('Failed to load efficiency data:', error);
        }

        // Initialize charts with whatever data we managed to load
        console.log('Chart data loaded:', chartData);
        this.initializeCharts(chartData);
    }
    
    initializeCharts(data) {
        // Initialize charts using the separate charts.js file
        if (window.ChartManager) {
            this.chartManager = new ChartManager();
            this.chartManager.initializeAll(data);
        }
    }
    
    applyFilters() {
        // Collect filter values
        this.currentFilters = {};
        
        const filterIds = [
            'startDate', 'endDate', 'timeOfDay', 'isWeekend', 
            'vendorId', 'passengerCount', 'minDistance', 'maxDistance', 
            'minDuration', 'maxDuration'
        ];
        
        filterIds.forEach(id => {
            const element = document.getElementById(id);
            if (element && element.value) {
                let value = element.value;
                
                // Convert duration from minutes to seconds for API
                if (id === 'minDuration' || id === 'maxDuration') {
                    value = parseInt(value) * 60;
                }
                
                this.currentFilters[this.camelToSnake(id)] = value;
            }
        });
        
        // Reset to first page when applying new filters
        this.currentPage = 1;
        
        // Reload data with new filters
        this.loadTripsData();
        console.log('Filters applied:', this.currentFilters);
        this.showToast('Filters applied', 'success');
        // Optionally collapse after applying to save space
        this.setFiltersCollapsed(true);
    }
    
    clearFilters() {
        // Clear all filter inputs
        const filterIds = [
            'startDate', 'endDate', 'timeOfDay', 'isWeekend', 
            'vendorId', 'passengerCount', 'minDistance', 'maxDistance', 
            'minDuration', 'maxDuration'
        ];
        
        filterIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.value = '';
            }
        });
        
        // Clear current filters and reload data
        this.currentFilters = {};
        this.currentPage = 1;
        this.loadTripsData();
        
        console.log('Filters cleared');
        this.showToast('Filters cleared', 'warn');
    }
    
    goToPage(page) {
        if (page < 1) return;
        this.currentPage = page;
        this.loadTripsData();
    }
    
    async showTripDetails(tripId) {
        try {
            const data = await this.fetchWithRetry(`${this.apiBaseUrl}/trips/${tripId}`, {}, 2, 300);
            this.displayTripModal(data.trip);
        } catch (error) {
            console.error('Error loading trip details:', error);
            this.showErrorMessage('Error loading trip details');
        }
    }
    
    displayTripModal(trip) {
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');
        
        modalTitle.textContent = `Trip Details - ${trip.trip_id}`;
        
        modalBody.innerHTML = `
            <div class="trip-details">
                <div class="detail-section">
                    <h4>Trip Information</h4>
                    <p><strong>Trip ID:</strong> ${trip.trip_id}</p>
                    <p><strong>Vendor:</strong> ${trip.vendor_id === 1 ? 'Creative Mobile Technologies' : 'VeriFone Inc.'}</p>
                    <p><strong>Passengers:</strong> ${trip.passenger_count}</p>
                    <p><strong>Store & Forward:</strong> ${trip.store_and_fwd_flag}</p>
                </div>
                
                <div class="detail-section">
                    <h4>Time & Duration</h4>
                    <p><strong>Pickup Time:</strong> ${this.formatDateTime(trip.pickup_datetime)}</p>
                    <p><strong>Dropoff Time:</strong> ${this.formatDateTime(trip.dropoff_datetime)}</p>
                    <p><strong>Duration:</strong> ${this.formatDuration(trip.trip_duration)}</p>
                    <p><strong>Time Period:</strong> ${trip.time_of_day}</p>
                    <p><strong>Day of Week:</strong> ${trip.day_of_week}</p>
                    <p><strong>Weekend:</strong> ${trip.is_weekend ? 'Yes' : 'No'}</p>
                </div>
                
                <div class="detail-section">
                    <h4>Distance & Speed</h4>
                    <p><strong>Distance:</strong> ${parseFloat(trip.trip_distance || 0).toFixed(2)} km</p>
                    <p><strong>Average Speed:</strong> ${parseFloat(trip.trip_speed || 0).toFixed(1)} km/h</p>
                    <p><strong>Efficiency Score:</strong> ${parseFloat(trip.trip_efficiency || 0).toFixed(1)}%</p>
                    <p><strong>Idle Time:</strong> ${this.formatDuration(trip.idle_time || 0)}</p>
                </div>
                
                <div class="detail-section">
                    <h4>Locations</h4>
                    <p><strong>Pickup:</strong> ${parseFloat(trip.pickup_latitude).toFixed(4)}, ${parseFloat(trip.pickup_longitude).toFixed(4)}</p>
                    <p><strong>Dropoff:</strong> ${parseFloat(trip.dropoff_latitude).toFixed(4)}, ${parseFloat(trip.dropoff_longitude).toFixed(4)}</p>
                </div>
                
                <div class="detail-section">
                    <h4>Quality Metrics</h4>
                    <p><strong>Valid Trip:</strong> ${trip.is_valid ? 'Yes' : 'No'}</p>
                    <p><strong>Quality Score:</strong> ${trip.quality_score}/100</p>
                    <p><strong>Anomaly Flags:</strong> ${trip.anomaly_flags || 'None'}</p>
                </div>
            </div>
        `;
        
        this.openModal();
    }
    
    async exportData() {
        try {
            this.showLoading(true);
            
            // Get current filtered data for export
            const queryParams = new URLSearchParams({
                limit: 1000, // Export more records
                ...this.currentFilters
            });
            const data = await this.fetchWithRetry(`${this.apiBaseUrl}/trips?${queryParams.toString()}`, {}, 2, 300);
            this.downloadCSV(data.trips, 'nyc_taxi_trips.csv');
        } catch (error) {
            console.error('Error exporting data:', error);
            this.showErrorMessage('Error exporting data. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }
    
    downloadCSV(data, filename) {
        if (!data || data.length === 0) {
            this.showErrorMessage('No data to export');
            return;
        }
        
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(header => {
                const value = row[header] || '';
                return typeof value === 'string' && value.includes(',') ? `"${value}"` : value;
            }).join(','))
        ].join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        console.log(`Exported ${data.length} records to ${filename}`);
    }
    
    refreshData() {
        console.log('Refreshing dashboard data...');
        this.loadInitialData();
    }
    
    // Modal functions
    openModal() {
        document.getElementById('modal').style.display = 'block';
    }
    
    closeModal() {
        document.getElementById('modal').style.display = 'none';
    }
    
    showAboutModal() {
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');
        
        modalTitle.textContent = 'About This Dashboard';
        modalBody.innerHTML = `
            <h4>NYC Taxi Trip Analysis Dashboard</h4>
            <p>This dashboard provides comprehensive analysis of New York City taxi trip data, offering insights into urban mobility patterns and transportation efficiency.</p>
            
            <h4>Features</h4>
            <ul>
                <li>Interactive filtering and exploration of trip data</li>
                <li>Real-time statistical analysis and visualizations</li>
                <li>Advanced insights using custom algorithms</li>
                <li>Comprehensive data quality assessment</li>
            </ul>
            
            <h4>Technology Stack</h4>
            <ul>
                <li>Backend: Python Flask with PostgreSQL</li>
                <li>Frontend: HTML5, CSS3, JavaScript</li>
                <li>Visualizations: Chart.js</li>
                <li>Data Processing: Custom algorithms (no pandas/numpy)</li>
            </ul>
        `;
        this.openModal();
    }
    
    showMethodologyModal() {
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');
        
        modalTitle.textContent = 'Methodology';
        modalBody.innerHTML = `
            <h4>Data Processing Pipeline</h4>
            <ol>
                <li><strong>Data Cleaning:</strong> Removal of duplicates, handling missing values, coordinate validation</li>
                <li><strong>Feature Engineering:</strong> Trip distance calculation, speed analysis, temporal features</li>
                <li><strong>Quality Assessment:</strong> Outlier detection, efficiency scoring</li>
                <li><strong>Database Storage:</strong> Normalized schema with optimized indexing</li>
            </ol>
            
            <h4>Custom Algorithms</h4>
            <ul>
                <li>QuickSort implementation for data sorting</li>
                <li>Custom filtering without built-in functions</li>
                <li>Haversine distance calculation</li>
                <li>IQR-based outlier detection</li>
                <li>Statistical calculations (percentiles, distributions)</li>
            </ul>
            
            <h4>Derived Features</h4>
            <ul>
                <li><strong>Trip Distance:</strong> Calculated using Haversine formula</li>
                <li><strong>Trip Speed:</strong> Average speed during trip</li>
                <li><strong>Efficiency Score:</strong> Based on speed vs. optimal conditions</li>
                <li><strong>Idle Time:</strong> Estimated time spent in traffic/stops</li>
            </ul>
        `;
        this.openModal();
    }
    
    showDataSourceModal() {
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');
        
        modalTitle.textContent = 'Data Source';
        modalBody.innerHTML = `
            <h4>NYC Taxi & Limousine Commission (TLC)</h4>
            <p>This analysis uses official trip record data from the New York City Taxi and Limousine Commission.</p>
            
            <h4>Dataset Information</h4>
            <ul>
                <li><strong>Source:</strong> NYC TLC Trip Record Data</li>
                <li><strong>Records:</strong> ~1.45 million taxi trips</li>
                <li><strong>Time Period:</strong> 2016 data sample</li>
                <li><strong>Coverage:</strong> All five NYC boroughs</li>
            </ul>
            
            <h4>Data Fields</h4>
            <ul>
                <li>Pickup and dropoff timestamps</li>
                <li>Geographic coordinates</li>
                <li>Trip duration and passenger count</li>
                <li>Vendor information</li>
                <li>Various trip metadata</li>
            </ul>
            
            <h4>Data Quality</h4>
            <p>The raw data has been processed to handle missing values, remove duplicates, and validate geographic coordinates within NYC boundaries.</p>
        `;
        this.openModal();
    }
    
    // Utility functions
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            if (show) {
                overlay.classList.remove('hidden');
            } else {
                overlay.classList.add('hidden');
            }
        }
    }
    
    showErrorMessage(message) {
        alert(`Error: ${message}`); // Simple error display - could be enhanced with custom modal
    }
    
    showErrorInTable(message) {
        const tbody = document.getElementById('tripsTableBody');
        tbody.innerHTML = `<tr><td colspan="8" class="loading-cell">${message}</td></tr>`;
    }
    
    formatNumber(value) {
        if (value == null) return '0';
        return parseInt(value).toLocaleString();
    }
    
    formatDuration(seconds) {
        if (seconds == null || isNaN(seconds)) return '0s';

        // Ensure numeric and round seconds to avoid long decimals
        const total = Number(seconds);
        const hours = Math.floor(total / 3600);
        const minutes = Math.floor((total % 3600) / 60);
        const remainingSeconds = Math.round(total % 60);

        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${remainingSeconds}s`;
        } else {
            return `${remainingSeconds}s`;
        }
    }
    
    formatDateTime(dateTimeString) {
        if (!dateTimeString) return 'N/A';
        
        const date = new Date(dateTimeString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    camelToSnake(str) {
        return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new TaxiDashboard();
});
