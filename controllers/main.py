# -*- coding: utf-8 -*-

import json
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class LocationOccupancyController(http.Controller):
    """
    HTTP Controller for Location Occupancy Grid Dashboard
    
    Provides JSON endpoint for real-time location status data
    optimized for 167 PR-1 locations across 3 zones.
    """

    @http.route('/occupancy/grid_data', type='json', auth='user', methods=['POST'])
    def get_grid_data(self):
        """
        Returns location occupancy data for grid dashboard
        
        Endpoint: /occupancy/grid_data
        Method: POST (JSON-RPC)
        Auth: Requires logged-in user
        
        Response format:
        {
            "summary": {
                "total": 167,
                "free": 54,
                "reserved": 68,
                "occupied": 45
            },
            "zones": [
                {
                    "name": "malak_sklad",
                    "label": "Малък Склад",
                    "count": 100,
                    "locations": [...]
                },
                ...
            ]
        }
        """
        try:
            _logger.info("🎨 Grid data request received")
            
            # Get location model
            Location = request.env['stock.location']
            
            # Odoo 13: read() will trigger compute for all 167 locations
            # Query all PR-1 locations (with computed fields)
            # Filter by parent location_id = 19 (PR-1 warehouse)
            locations = Location.search([
                ('usage', '=', 'internal'),
                ('location_id', '=', 19)
            ], order='name')
            
            _logger.info(f"📦 Found {len(locations)} PR-1 locations")
            
            # Read all data in batch (efficient!)
            location_data = locations.read([
                'id', 'name', 'barcode',
                'occupancy_status',
                'occupancy_order_name',
                'occupancy_customer',
                'occupancy_duration_hours',
                'pr1_zone'
            ])
            
            # Initialize summary counters
            summary = {
                'total': len(location_data),
                'free': 0,
                'reserved': 0,
                'occupied': 0
            }
            
            # Single zone - PR-1
            pr1_zone = {
                'name': 'pr1',
                'label': 'PR-1',
                'count': len(location_data),
                'locations': []
            }
            
            # Process each location
            for loc in location_data:
                status = loc['occupancy_status']
                
                # Update summary
                if status == 'free':
                    summary['free'] += 1
                elif status == 'reserved':
                    summary['reserved'] += 1
                elif status == 'occupied':
                    summary['occupied'] += 1
                
                # Format location data for frontend
                location_item = {
                    'id': loc['id'],
                    'name': loc['name'],  # Keep full name (A-A-01)
                    'status': status,
                    'order': loc['occupancy_order_name'] or None,
                    'customer': loc['occupancy_customer'] or None,
                    'duration': round((loc['occupancy_duration_hours'] or 0) / 24, 1)
                }
                
                pr1_zone['locations'].append(location_item)
            
            # Sort by physical location: Row (A/B) -> Level (A-E) -> Column (number)
            def sort_key(loc):
                name = loc['name']
                try:
                    parts = name.split('-')
                    row = parts[0]      # A or B
                    level = parts[1]    # A, B, C, D, E
                    col = int(parts[2]) # 01, 02, 03...
                    return (row, level, col)
                except:
                    return (name, '', 999)
            
            pr1_zone['locations'].sort(key=sort_key)
            
            response = {
                'success': True,
                'summary': summary,
                'zones': [pr1_zone]  # Single zone
            }
            
            _logger.info(f"✅ Grid data prepared: {summary}")
            return response
            
        except Exception as e:
            _logger.error(f"❌ Error fetching grid data: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'summary': {'total': 0, 'free': 0, 'reserved': 0, 'occupied': 0},
                'zones': []
            }
