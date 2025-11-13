odoo.define('personalizirai_location_occupancy.GridWidget', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var ajax = require('web.ajax');
    
    var _t = core._t;
    var QWeb = core.qweb;

    /**
     * Interactive Grid Dashboard Widget for Location Occupancy
     * 
     * Displays PR-1 locations organized by physical structure:
     * - Row A (Редица A) - 70 positions
     * - Row B (Редица B) - 61 positions
     * Each row has 5 levels: E (top) → D → C → B → A (bottom)
     * 
     * Features:
     * - Color-coded status (green/yellow/red)
     * - Click to view details
     * - Auto-refresh every 60 seconds
     * - Summary statistics
     * - Physical warehouse layout visualization
     */
    var OccupancyGridWidget = AbstractAction.extend({
        template: 'LocationOccupancyGrid',
        
        /**
         * Widget initialization
         */
        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.action = action;
            this.gridData = null;
            this.refreshInterval = null;
            this.isRefreshing = false;
        },

        /**
         * Widget startup - load data and start auto-refresh
         */
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                // Initial data load
                return self._fetchAndRenderGrid().then(function() {
                    // Start auto-refresh (60 seconds)
                    self._startAutoRefresh();
                    
                    // Bind manual refresh button
                    self.$('.js-refresh-btn').on('click', function(e) {
                        e.preventDefault();
                        self._manualRefresh();
                    });
                });
            });
        },

        /**
         * Widget cleanup - stop auto-refresh
         */
        destroy: function () {
            this._stopAutoRefresh();
            this._super.apply(this, arguments);
        },

        /**
         * Fetch data from backend and render grid
         */
        _fetchAndRenderGrid: function () {
            var self = this;
            
            if (this.isRefreshing) {
                return Promise.resolve(); // Prevent concurrent requests
            }
            
            this.isRefreshing = true;
            this._showLoading();

            return ajax.jsonRpc('/occupancy/grid_data', 'call', {})
                .then(function (result) {
                    if (result.success) {
                        self.gridData = result;
                        self._renderGrid();
                    } else {
                        self._showError(result.error || 'Unknown error');
                    }
                })
                .catch(function (error) {
                    console.error('Grid data fetch failed:', error);
                    self._showError('Failed to load grid data. Please refresh the page.');
                })
                .finally(function () {
                    self.isRefreshing = false;
                    self._hideLoading();
                });
        },

        /**
         * Render grid with current data
         */
        _renderGrid: function () {
            if (!this.gridData) return;

            var self = this;
            var $grid = this.$('.occupancy-grid-container');
            
            // Clear existing content
            $grid.empty();

            // Render summary
            this._renderSummary();

            // Render each row (Row A, Row B)
            if (this.gridData.rows) {
                this.gridData.rows.forEach(function(row) {
                    var $row = $(QWeb.render('LocationOccupancyRow', {
                        row: row
                    }));
                    
                    // Add click handlers to location boxes
                    $row.find('.location-box').on('click', function() {
                        var locationId = $(this).data('location-id');
                        self._showLocationDetails(locationId);
                    });
                    
                    $grid.append($row);
                });
            }

            // Update last refresh time
            this._updateRefreshTime();
        },

        /**
         * Render summary statistics
         */
        _renderSummary: function () {
            if (!this.gridData || !this.gridData.summary) return;

            var summary = this.gridData.summary;
            this.$('.summary-total').text(summary.total);
            this.$('.summary-free').text(summary.free);
            this.$('.summary-reserved').text(summary.reserved);
            this.$('.summary-occupied').text(summary.occupied);
        },

        /**
         * Show location details in modal
         */
        _showLocationDetails: function (locationId) {
            if (!this.gridData || !this.gridData.rows) return;

            // Find location in data (search through rows and levels)
            var location = null;
            this.gridData.rows.forEach(function(row) {
                if (location) return; // Already found
                
                row.levels.forEach(function(level) {
                    if (location) return; // Already found
                    
                    var found = level.locations.find(function(loc) {
                        return loc.id === locationId;
                    });
                    
                    if (found) location = found;
                });
            });

            if (!location) {
                console.error('Location not found:', locationId);
                return;
            }

            // Render modal with location details
            var $modal = $(QWeb.render('LocationDetailsModal', {
                location: location
            }));

            // Add to DOM
            this.$el.append($modal);

            // Show modal (using Odoo/Bootstrap modal)
            $modal.modal('show');

            // Remove from DOM when closed
            $modal.on('hidden.bs.modal', function() {
                $modal.remove();
            });
        },

        /**
         * Start auto-refresh timer (60 seconds)
         */
        _startAutoRefresh: function () {
            var self = this;
            this._stopAutoRefresh(); // Clear existing timer
            
            this.refreshInterval = setInterval(function() {
                console.log('🔄 Auto-refreshing grid data...');
                self._fetchAndRenderGrid();
            }, 60000); // 60 seconds
        },

        /**
         * Stop auto-refresh timer
         */
        _stopAutoRefresh: function () {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
                this.refreshInterval = null;
            }
        },

        /**
         * Manual refresh triggered by button
         */
        _manualRefresh: function () {
            console.log('🔄 Manual refresh triggered');
            this._fetchAndRenderGrid();
        },

        /**
         * Update last refresh timestamp
         */
        _updateRefreshTime: function () {
            var now = new Date();
            var timeString = now.toLocaleTimeString('bg-BG');
            this.$('.refresh-time').text(timeString);
        },

        /**
         * Show loading indicator
         */
        _showLoading: function () {
            this.$('.loading-spinner').removeClass('d-none');
            this.$('.js-refresh-btn').prop('disabled', true);
        },

        /**
         * Hide loading indicator
         */
        _hideLoading: function () {
            this.$('.loading-spinner').addClass('d-none');
            this.$('.js-refresh-btn').prop('disabled', false);
        },

        /**
         * Show error message
         */
        _showError: function (message) {
            var $error = $('<div class="alert alert-danger alert-dismissible fade show" role="alert">')
                .text(message)
                .append('<button type="button" class="close" data-dismiss="alert">&times;</button>');
            
            this.$('.error-container').empty().append($error);
            
            // Auto-dismiss after 5 seconds
            setTimeout(function() {
                $error.alert('close');
            }, 5000);
        }
    });

    // Register widget as client action
    core.action_registry.add('occupancy_grid_dashboard', OccupancyGridWidget);

    return OccupancyGridWidget;
});
