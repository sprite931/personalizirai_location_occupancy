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
        Compute real-time occupancy status:
        - OCCUPIED: Has physical stock (stock.quant.quantity > 0)
        - RESERVED: Assigned to order (sale_order.source_location_id)
        - FREE: Neither of above
        """
        for location in self:
            # Only compute for PR-1 locations
            if not location.is_pr1_location:
                location.occupancy_status = False
                location.occupancy_order_id = False
                location.occupancy_order_name = False
                location.occupancy_magento_id = False
                location.occupancy_customer = False
                location.occupancy_since = False
                location.occupancy_duration_hours = 0.0
                continue
            
            try:
                # Check 1: Physical stock (OCCUPIED)
                quants = self.env['stock.quant'].search([
                    ('location_id', '=', location.id),
                    ('quantity', '>', 0)
                ], limit=1)
                
                if quants:
                    location.occupancy_status = 'occupied'
                    
                    # Try to find associated order
                    order = self.env['sale.order'].search([
                        ('source_location_id', '=', location.id),
                        ('state', 'in', ['manufactured', 'ready_package', 'ready_picking'])
                    ], limit=1)
                    
                    if order:
                        location._populate_order_info(order)
                    else:
                        # Occupied but no order found
                        location.occupancy_order_id = False
                        location.occupancy_order_name = 'Unknown'
                        location.occupancy_magento_id = False
                        location.occupancy_customer = 'Unknown'
                        location.occupancy_since = False
                        location.occupancy_duration_hours = 0.0
                    continue
                
                # Check 2: Reserved (assigned but no stock)
                order = self.env['sale.order'].search([
                    ('source_location_id', '=', location.id),
                    ('state', 'in', ['manufactured', 'ready_package', 'ready_picking'])
                ], limit=1)
                
                if order:
                    location.occupancy_status = 'reserved'
                    location._populate_order_info(order)
                    continue
                
                # Otherwise: FREE
                location.occupancy_status = 'free'
                location.occupancy_order_id = False
                location.occupancy_order_name = False
                location.occupancy_magento_id = False
                location.occupancy_customer = False
                location.occupancy_since = False
                location.occupancy_duration_hours = 0.0
                
            except Exception as e:
                _logger.error(f"Error computing occupancy for {location.name}: {str(e)}")
                location.occupancy_status = 'free'
                location.occupancy_order_id = False
                location.occupancy_order_name = False
                location.occupancy_magento_id = False
                location.occupancy_customer = False
                location.occupancy_since = False
                location.occupancy_duration_hours = 0.0
    
    def _populate_order_info(self, order):
        """Helper to populate order-related fields"""
        self.occupancy_order_id = order.id
        self.occupancy_order_name = order.name
        
        # Try to get Magento ID if field exists
        try:
            self.occupancy_magento_id = order.magento_id if hasattr(order, 'magento_id') else False
        except:
            self.occupancy_magento_id = False
        
        self.occupancy_customer = order.partner_id.name if order.partner_id else 'Unknown'
        
        # Find when order entered current state
        # Look in mail.tracking.value for state changes
        tracking = self.env['mail.tracking.value'].search([
            ('mail_message_id.model', '=', 'sale.order'),
            ('mail_message_id.res_id', '=', order.id),
            ('field', '=', 'state'),
            ('new_value_char', 'in', ['Manufactured', 'Ready for Picking', 'Ready for Package'])
        ], order='create_date desc', limit=1)
        
        if tracking and tracking.mail_message_id:
            self.occupancy_since = tracking.mail_message_id.date
        else:
            # Fallback to order write_date
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
