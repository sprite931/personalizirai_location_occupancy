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
            
            # Query all PR-1 locations (with computed fields)
            # Odoo 13: read() will trigger compute for all 167 locations
            locations = Location.search([
                ('usage', '=', 'internal'),
                ('barcode', 'like', 'PR-1-%')
            ], order='barcode')
            
            _logger.info(f"📦 Found {len(locations)} PR-1 locations")
            
            # Read all data in batch (efficient!)
            location_data = locations.read([
                'id', 'name', 'barcode',
                'occupancy_status',
                'occupancy_order_name',
                'occupancy_customer_name',
                'occupancy_duration_days',
                'occupancy_zone'
            ])
            
            # Initialize summary counters
            summary = {
                'total': len(location_data),
                'free': 0,
                'reserved': 0,
                'occupied': 0
            }
            
            # Group by zones
            zones_dict = {
                'malak_sklad': {
                    'name': 'malak_sklad',
                    'label': 'Малък Склад',
                    'count': 0,
                    'locations': []
                },
                'calandar': {
                    'name': 'calandar',
                    'label': 'Calandar',
                    'count': 0,
                    'locations': []
                },
                'teniski': {
                    'name': 'teniski',
                    'label': 'Teniski',
                    'count': 0,
                    'locations': []
                }
            }
            
            # Process each location
            for loc in location_data:
                status = loc['occupancy_status']
                zone = loc['occupancy_zone'] or 'malak_sklad'  # Default zone
                
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
                    'name': loc['barcode'] or loc['name'],  # Use barcode (M-001)
                    'status': status,
                    'order': loc['occupancy_order_name'] or None,
                    'customer': loc['occupancy_customer_name'] or None,
                    'duration': round(loc['occupancy_duration_days'] or 0, 1)
                }
                
                # Add to appropriate zone
                if zone in zones_dict:
                    zones_dict[zone]['locations'].append(location_item)
                    zones_dict[zone]['count'] += 1
            
            # Convert zones dict to list (preserve order)
            zones = [
                zones_dict['malak_sklad'],
                zones_dict['calandar'],
                zones_dict['teniski']
            ]
            
            response = {
                'success': True,
                'summary': summary,
                'zones': zones
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
