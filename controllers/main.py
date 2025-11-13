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
    organized by physical warehouse structure (Rows & Levels).
    """

    @http.route('/occupancy/grid_data', type='json', auth='user', methods=['POST'])
    def get_grid_data(self):
        """
        Returns location occupancy data organized by physical structure
        
        Endpoint: /occupancy/grid_data
        Method: POST (JSON-RPC)
        Auth: Requires logged-in user
        
        Response format:
        {
            "summary": {
                "total": 131,
                "free": 85,
                "reserved": 46,
                "occupied": 0
            },
            "rows": [
                {
                    "name": "A",
                    "label": "РЕДИЦА A",
                    "count": 70,
                    "column_numbers": ["01", "02", ..., "14"],
                    "levels": [
                        {
                            "name": "E",
                            "label": "Ниво E (Горе)",
                            "locations": [...]
                        },
                        ...
                    ]
                },
                {
                    "name": "B",
                    "label": "РЕДИЦА B",
                    "count": 61,
                    "column_numbers": ["01", "02", ..., "13"],
                    "levels": [...]
                }
            ]
        }
        """
        try:
            _logger.info("🎨 Grid data request received")
            
            # Get location model
            Location = request.env['stock.location']
            
            # Query all PR-1 locations (location_id = 19)
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
                'occupancy_transport_unit',  # NEW: Transport box info
                'pr1_zone'
            ])
            
            # Initialize summary counters
            summary = {
                'total': len(location_data),
                'free': 0,
                'reserved': 0,
                'occupied': 0
            }
            
            # Group locations by Row and Level
            # Structure: rows[row_name][level_name] = [locations]
            rows_data = {
                'A': {'E': [], 'D': [], 'C': [], 'B': [], 'A': []},
                'B': {'E': [], 'D': [], 'C': [], 'B': [], 'A': []}
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
                
                # Parse location name: A-E-05 → Row=A, Level=E, Column=05
                try:
                    parts = loc['name'].split('-')
                    if len(parts) >= 3:
                        row = parts[0]      # A or B
                        level = parts[1]    # A, B, C, D, E
                        col_num = int(parts[2])  # 01, 02, 03...
                        
                        # Format location data for frontend
                        location_item = {
                            'id': loc['id'],
                            'name': loc['name'],
                            'display_name': f"{row}-{level}-{parts[2]}",  # Keep leading zeros
                            'row': row,
                            'level': level,
                            'column': col_num,
                            'column_label': parts[2],  # "01", "02" with leading zeros
                            'status': status,
                            'order': loc['occupancy_order_name'] or None,
                            'customer': loc['occupancy_customer'] or None,
                            'duration': round((loc['occupancy_duration_hours'] or 0) / 24, 1),
                            'transport_unit': loc['occupancy_transport_unit'] or None  # NEW
                        }
                        
                        # Add to appropriate row and level
                        if row in rows_data and level in rows_data[row]:
                            rows_data[row][level].append(location_item)
                        else:
                            _logger.warning(f"⚠️ Unknown row/level: {loc['name']}")
                    else:
                        _logger.warning(f"⚠️ Invalid name format: {loc['name']}")
                except Exception as e:
                    _logger.error(f"❌ Error parsing location {loc.get('name')}: {e}")
            
            # Sort locations within each level by column number
            for row in rows_data:
                for level in rows_data[row]:
                    rows_data[row][level].sort(key=lambda x: x['column'])
            
            # Build response structure
            # Level order: E (top) → D → C → B → A (bottom)
            level_order = ['E', 'D', 'C', 'B', 'A']
            level_labels = {
                'E': 'Ниво E (Горе)',
                'D': 'Ниво D',
                'C': 'Ниво C',
                'B': 'Ниво B',
                'A': 'Ниво A (Долу)'
            }
            
            rows = []
            for row_name in ['A', 'B']:
                # Count locations in this row
                row_count = sum(len(rows_data[row_name][lvl]) for lvl in level_order)
                
                # Determine max columns for this row
                max_col = 0
                for level in level_order:
                    for loc in rows_data[row_name][level]:
                        if loc['column'] > max_col:
                            max_col = loc['column']
                
                # Generate column numbers array
                column_numbers = [f"{i:02d}" for i in range(1, max_col + 1)]
                
                # Build levels array
                levels = []
                for level_name in level_order:
                    levels.append({
                        'name': level_name,
                        'label': level_labels[level_name],
                        'count': len(rows_data[row_name][level_name]),
                        'locations': rows_data[row_name][level_name]
                    })
                
                rows.append({
                    'name': row_name,
                    'label': f'РЕДИЦА {row_name}',
                    'emoji': '📦',
                    'count': row_count,
                    'column_numbers': column_numbers,
                    'levels': levels
                })
            
            response = {
                'success': True,
                'summary': summary,
                'rows': rows
            }
            
            _logger.info(f"✅ Grid data prepared: {summary}")
            _logger.info(f"   Row A: {rows[0]['count']} locations, {len(rows[0]['column_numbers'])} columns")
            _logger.info(f"   Row B: {rows[1]['count']} locations, {len(rows[1]['column_numbers'])} columns")
            
            return response
            
        except Exception as e:
            _logger.error(f"❌ Error fetching grid data: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'summary': {'total': 0, 'free': 0, 'reserved': 0, 'occupied': 0},
                'rows': []
            }
