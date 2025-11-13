# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class StockLocation(models.Model):
    _inherit = 'stock.location'
    
    # ============================================
    # COMPUTED FIELDS - Real-time Status
    # ============================================
    
    occupancy_status = fields.Selection([
        ('free', 'Free'),
        ('reserved', 'Reserved'),
        ('occupied', 'Occupied'),
    ], string='Occupancy Status', 
       compute='_compute_occupancy_status', 
       store=False,
       help="Real-time location occupancy status")
    
    occupancy_order_id = fields.Many2one(
        'sale.order', 
        string='Assigned Order',
        compute='_compute_occupancy_status', 
        store=False)
    
    occupancy_order_name = fields.Char(
        string='Order Number', 
        compute='_compute_occupancy_status', 
        store=False)
    
    occupancy_magento_id = fields.Char(
        string='Magento Order', 
        compute='_compute_occupancy_status', 
        store=False)
    
    occupancy_customer = fields.Char(
        string='Customer', 
        compute='_compute_occupancy_status', 
        store=False)
    
    occupancy_since = fields.Datetime(
        string='Occupied/Reserved Since', 
        compute='_compute_occupancy_status', 
        store=False)
    
    occupancy_duration_hours = fields.Float(
        string='Duration (Hours)', 
        compute='_compute_occupancy_status', 
        store=False,
        help="How long location has been in current status")
    
    occupancy_transport_unit = fields.Char(
        string='Transport Unit',
        compute='_compute_occupancy_status',
        store=False,
        help="Transport box/unit code")
    
    # ============================================
    # STATISTICS - 7 Day History (Phase 4)
    # ============================================
    
    occupancy_rate_7d = fields.Float(
        string='7-Day Utilization %', 
        compute='_compute_occupancy_stats', 
        store=False,
        help="Percentage of time occupied in last 7 days")
    
    occupancy_avg_duration = fields.Float(
        string='Avg Duration (Hours)', 
        compute='_compute_occupancy_stats', 
        store=False,
        help="Average occupation duration")
    
    occupancy_times_used_7d = fields.Integer(
        string='Times Used (7d)', 
        compute='_compute_occupancy_stats', 
        store=False,
        help="Number of times location was used in last 7 days")
    
    occupancy_last_order = fields.Char(
        string='Last Order', 
        compute='_compute_occupancy_stats', 
        store=False)
    
    occupancy_last_freed = fields.Datetime(
        string='Last Freed', 
        compute='_compute_occupancy_stats', 
        store=False)
    
    # ============================================
    # HELPER FIELDS
    # ============================================
    
    is_pr1_location = fields.Boolean(
        string='Is PR-1 Location', 
        compute='_compute_is_pr1_location', 
        store=False,
        search='_search_is_pr1_location',
        help="True if location is child of PR-1 warehouse")
    
    pr1_zone = fields.Selection([
        ('malak_sklad', 'Малък Склад'),
        ('calandar', 'Calandar'),
        ('teniski', 'Teniski'),
        ('other', 'Other'),
    ], string='PR-1 Zone', 
       compute='_compute_pr1_zone', 
       store=False)
    
    # ============================================
    # COMPUTE METHODS
    # ============================================
    
    @api.depends('name', 'location_id')
    def _compute_is_pr1_location(self):
        """Check if location is child of PR-1 (location_id = 19)"""
        for location in self:
            # Check if parent is PR-1 or if this is PR-1
            location.is_pr1_location = (
                location.location_id.id == 19 or 
                location.id == 19
            )
    
    def _search_is_pr1_location(self, operator, value):
        """Enable searching by is_pr1_location"""
        if operator == '=' and value:
            return [('location_id', '=', 19)]
        elif operator == '=' and not value:
            return [('location_id', '!=', 19)]
        else:
            return []
    
    @api.depends('name', 'complete_name')
    def _compute_pr1_zone(self):
        """Determine which PR-1 zone this location belongs to"""
        for location in self:
            if not location.is_pr1_location:
                location.pr1_zone = 'other'
                continue
            
            name = location.name or ''
            
            # Малък Склад: M-001 to M-100
            if name.startswith('M-'):
                location.pr1_zone = 'malak_sklad'
            # Calandar: C-01 to C-30
            elif name.startswith('C-'):
                location.pr1_zone = 'calandar'
            # Teniski: T-01 to T-37
            elif name.startswith('T-'):
                location.pr1_zone = 'teniski'
            else:
                location.pr1_zone = 'other'
    
    @api.depends('name')  # Dummy depend - will trigger on context reload
    def _compute_occupancy_status(self):
        """
        Compute real-time occupancy status with BATCH optimization.
        
        LOGIC:
        - OCCUPIED: Order has transport_unit_id (physical box assigned)
        - RESERVED: Order assigned but no transport_unit_id yet
        - FREE: No order assigned
        
        OPTIMIZED: Uses batch query instead of individual searches.
        """
        # Filter only PR-1 locations
        pr1_locations = self.filtered(lambda l: l.location_id.id == 19 or l.id == 19)
        other_locations = self - pr1_locations
        
        # Set defaults for non-PR-1 locations
        for location in other_locations:
            location._set_default_occupancy_values()
        
        if not pr1_locations:
            return
        
        try:
            # BATCH QUERY: Get all orders assigned to these locations
            # Including transport_unit_id for OCCUPIED detection
            location_ids = pr1_locations.ids
            orders = self.env['sale.order'].search([
                ('source_location_id', 'in', location_ids),
                ('state', 'in', ['manufactured', 'ready_package', 'ready_picking'])
            ])
            
            # Map: location_id -> order
            location_order_map = {o.source_location_id.id: o for o in orders}
            
            # Process each location with the cached data
            for location in pr1_locations:
                order = location_order_map.get(location.id)
                
                if order:
                    # Check if order has transport unit (box)
                    if order.transport_unit_id:
                        # OCCUPIED: Has physical box assigned
                        location.occupancy_status = 'occupied'
                        location._populate_order_info(order, has_transport_unit=True)
                        _logger.debug(f"🔴 Location {location.name} OCCUPIED - Order {order.name} has transport unit {order.transport_unit_id.name}")
                    else:
                        # RESERVED: Order assigned but no box yet
                        location.occupancy_status = 'reserved'
                        location._populate_order_info(order, has_transport_unit=False)
                        _logger.debug(f"🟡 Location {location.name} RESERVED - Order {order.name} waiting for transport unit")
                else:
                    # FREE: Not assigned
                    location.occupancy_status = 'free'
                    location._set_default_occupancy_values()
                    _logger.debug(f"🟢 Location {location.name} FREE")
                    
        except Exception as e:
            _logger.error(f"❌ Error in batch occupancy computation: {str(e)}", exc_info=True)
            # Set defaults for all on error
            for location in pr1_locations:
                location._set_default_occupancy_values()
    
    def _set_default_occupancy_values(self):
        """Helper to set default/empty values"""
        self.occupancy_status = 'free'
        self.occupancy_order_id = False
        self.occupancy_order_name = False
        self.occupancy_magento_id = False
        self.occupancy_customer = False
        self.occupancy_since = False
        self.occupancy_duration_hours = 0.0
        self.occupancy_transport_unit = False
    
    def _populate_order_info(self, order, has_transport_unit=False):
        """Helper to populate order-related fields"""
        self.occupancy_order_id = order.id
        self.occupancy_order_name = order.name
        
        # Try to get Magento ID if field exists
        try:
            self.occupancy_magento_id = order.magento_id if hasattr(order, 'magento_id') else False
        except:
            self.occupancy_magento_id = False
        
        self.occupancy_customer = order.partner_id.name if order.partner_id else 'Unknown'
        
        # Get transport unit info if exists
        if has_transport_unit and order.transport_unit_id:
            try:
                transport_unit = order.transport_unit_id
                self.occupancy_transport_unit = f"{transport_unit.name} ({transport_unit.code})"
            except:
                self.occupancy_transport_unit = "BOX-???"
        else:
            self.occupancy_transport_unit = False
        
        # Use order write_date as approximation (faster than tracking search)
        self.occupancy_since = order.write_date
        
        # Calculate duration
        if self.occupancy_since:
            try:
                duration = datetime.now() - self.occupancy_since
                self.occupancy_duration_hours = duration.total_seconds() / 3600.0
            except:
                self.occupancy_duration_hours = 0.0
        else:
            self.occupancy_duration_hours = 0.0
    
    @api.depends('name')  # Dummy depend - Phase 4 will implement
    def _compute_occupancy_stats(self):
        """
        Compute 7-day statistics from location.occupancy.history
        
        TODO: Implement in Phase 4 after history model is created
        """
        for location in self:
            # Placeholder - Phase 4
            location.occupancy_rate_7d = 0.0
            location.occupancy_avg_duration = 0.0
            location.occupancy_times_used_7d = 0
            location.occupancy_last_order = False
            location.occupancy_last_freed = False
