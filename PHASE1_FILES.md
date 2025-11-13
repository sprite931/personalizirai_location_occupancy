# Phase 1: Foundation Files

Complete code for Phase 1 - Basic Models & Logic (2-3 hours)

---

## File 1: `__manifest__.py`

```python
{
    'name': 'PersonaliziRai Location Occupancy',
    'version': '1.0.0',
    'category': 'Warehouse',
    'summary': 'Real-time PR-1 location occupancy tracking',
    'description': '''
        Interactive grid dashboard for monitoring warehouse location occupancy.
        
        Features:
        - Real-time status: Free/Reserved/Occupied
        - 167 PR-1 locations tracked
        - Auto-refresh every 60 seconds
        - Assignment wizard
        - Historical analytics
        
        Solves the race condition problem where locations appear occupied
        but are physically empty (reserved for orders in production).
    ''',
    'author': 'PersonaliziRai',
    'website': 'https://personalizirai.bg',
    'depends': [
        'base',
        'stock',
        'sale',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        # Views will be added in Phase 2
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
```

---

## File 2: `__init__.py` (root)

```python
# -*- coding: utf-8 -*-
from . import models
```

---

## File 3: `models/__init__.py`

```python
# -*- coding: utf-8 -*-
from . import stock_location
```

---

## File 4: `models/stock_location.py`

**CRITICAL:** This is the main file with all logic!

```python
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
       help=\"Real-time location occupancy status\")
    
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
        help=\"How long location has been in current status\")
    
    # ============================================
    # STATISTICS - 7 Day History (Phase 4)
    # ============================================
    
    occupancy_rate_7d = fields.Float(
        string='7-Day Utilization %', 
        compute='_compute_occupancy_stats', 
        store=False,
        help=\"Percentage of time occupied in last 7 days\")
    
    occupancy_avg_duration = fields.Float(
        string='Avg Duration (Hours)', 
        compute='_compute_occupancy_stats', 
        store=False,
        help=\"Average occupation duration\")
    
    occupancy_times_used_7d = fields.Integer(
        string='Times Used (7d)', 
        compute='_compute_occupancy_stats', 
        store=False,
        help=\"Number of times location was used in last 7 days\")
    
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
        help=\"True if location is child of PR-1 warehouse\")
    
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
        \"\"\"Check if location is child of PR-1 (location_id = 19)\"\"\"
        for location in self:
            # Check if parent is PR-1 or if this is PR-1
            location.is_pr1_location = (
                location.location_id.id == 19 or 
                location.id == 19
            )
    
    def _search_is_pr1_location(self, operator, value):
        \"\"\"Enable searching by is_pr1_location\"\"\"
        if operator == '=' and value:
            return [('location_id', '=', 19)]
        elif operator == '=' and not value:
            return [('location_id', '!=', 19)]
        else:
            return []
    
    @api.depends('name', 'complete_name')
    def _compute_pr1_zone(self):
        \"\"\"Determine which PR-1 zone this location belongs to\"\"\"
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
        \"\"\"
        Compute real-time occupancy status:
        - OCCUPIED: Has physical stock (stock.quant.quantity > 0)
        - RESERVED: Assigned to order (sale_order.source_location_id)
        - FREE: Neither of above
        \"\"\"
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
                _logger.error(f\"Error computing occupancy for {location.name}: {str(e)}\")
                location.occupancy_status = 'free'
                location.occupancy_order_id = False
                location.occupancy_order_name = False
                location.occupancy_magento_id = False
                location.occupancy_customer = False
                location.occupancy_since = False
                location.occupancy_duration_hours = 0.0
    
    def _populate_order_info(self, order):
        \"\"\"Helper to populate order-related fields\"\"\"
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
        \"\"\"
        Compute 7-day statistics from location.occupancy.history
        
        TODO: Implement in Phase 4 after history model is created
        \"\"\"
        for location in self:
            # Placeholder - Phase 4
            location.occupancy_rate_7d = 0.0
            location.occupancy_avg_duration = 0.0
            location.occupancy_times_used_7d = 0
            location.occupancy_last_order = False
            location.occupancy_last_freed = False
```

---

## File 5: `security/ir.model.access.csv`

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_location_occupancy_user,location.occupancy.user,stock.model_stock_location,base.group_user,1,0,0,0
access_location_occupancy_manager,location.occupancy.manager,stock.model_stock_location,stock.group_stock_manager,1,1,1,1
```

---

## Installation Steps

### 1. Create Directory Structure

```bash
cd /odoo/custom/addons
git clone https://github.com/sprite931/personalizirai_location_occupancy.git
cd personalizirai_location_occupancy

# Create directories
mkdir -p models views static/src/{js,css,xml} security data

# Create __init__.py files
touch __init__.py models/__init__.py
```

### 2. Copy Files

Copy each file above to its location:
- `__manifest__.py` → root
- `__init__.py` → root  
- `models/__init__.py` → models/
- `models/stock_location.py` → models/
- `security/ir.model.access.csv` → security/

### 3. Set Permissions

```bash
sudo chown -R odoo:odoo /odoo/custom/addons/personalizirai_location_occupancy
```

### 4. Restart Odoo

```bash
sudo systemctl restart odoo

# Monitor logs
tail -f /var/log/odoo/byi_print_live.log
```

### 5. Install Module

```
Apps → Update Apps List → Search \"Location Occupancy\" → Install
```

---

## Testing Phase 1

### Test 1: Module Installation

```bash
# Check module loaded
sudo -u postgres psql byi_print_staging_personalizirai_stenik_cloud -c \"
SELECT name, state, latest_version 
FROM ir_module_module 
WHERE name = 'personalizirai_location_occupancy';
\"
```

Expected: `state = 'installed'`

### Test 2: PR-1 Location Detection

```python
sudo -u odoo python3 << 'EOF'
import sys
sys.path.insert(0, '/odoo/odoo-server')
import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo/byi_print_staging_personalizirai_stenik_cloud.conf'])
db_name = 'byi_print_staging_personalizirai_stenik_cloud'

with api.Environment.manage():
    registry = odoo.registry(db_name)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Count PR-1 locations
        locations = env['stock.location'].search([('is_pr1_location', '=', True)])
        print(f\"Total PR-1 locations: {len(locations)}\")
        
        # Expected: 167 (or close to it)
        
        cr.rollback()
EOF
```

### Test 3: Zone Detection

```python
# Same setup as above, then:
malak = locations.filtered(lambda l: l.pr1_zone == 'malak_sklad')
calandar = locations.filtered(lambda l: l.pr1_zone == 'calandar')
teniski = locations.filtered(lambda l: l.pr1_zone == 'teniski')

print(f\"Малък Склад: {len(malak)} (expect ~100)\")
print(f\"Calandar: {len(calandar)} (expect ~30)\")
print(f\"Teniski: {len(teniski)} (expect ~37)\")
```

### Test 4: Status Computation

```python
# Print first 5 locations with details
for loc in locations[:5]:
    print(f\"\\n{'='*50}\")
    print(f\"Location: {loc.name}\")
    print(f\"Zone: {loc.pr1_zone}\")
    print(f\"Status: {loc.occupancy_status}\")
    
    if loc.occupancy_order_id:
        print(f\"Order: {loc.occupancy_order_name}\")
        print(f\"Customer: {loc.occupancy_customer}\")
        print(f\"Duration: {loc.occupancy_duration_hours:.1f}h\")
```

### Test 5: Status Breakdown

```python
free = locations.filtered(lambda l: l.occupancy_status == 'free')
reserved = locations.filtered(lambda l: l.occupancy_status == 'reserved')
occupied = locations.filtered(lambda l: l.occupancy_status == 'occupied')

print(f\"\\n{'='*50}\")
print(f\"STATUS BREAKDOWN:\")
print(f\"{'='*50}\")
print(f\"🟢 Free: {len(free)} ({len(free)*100/len(locations):.1f}%)\")
print(f\"🟡 Reserved: {len(reserved)} ({len(reserved)*100/len(locations):.1f}%)\")
print(f\"🔴 Occupied: {len(occupied)} ({len(occupied)*100/len(locations):.1f}%)\")
```

---

## Expected Output

```
Total PR-1 locations: 167

Малък Склад: 100
Calandar: 30
Teniski: 37

==================================================
Location: M-001
Zone: malak_sklad
Status: free

==================================================
Location: M-002
Zone: malak_sklad
Status: reserved
Order: S43156
Customer: Иван Петров
Duration: 2.5h

==================================================
Location: M-003
Zone: malak_sklad
Status: occupied
Order: S43089
Customer: Public user
Duration: 18.3h

==================================================
STATUS BREAKDOWN:
==================================================
🟢 Free: 54 (32.3%)
🟡 Reserved: 68 (40.7%)
🔴 Occupied: 45 (27.0%)
```

---

## Phase 1 Checklist

- [ ] All files created
- [ ] Permissions set correctly
- [ ] Module installs without errors
- [ ] 167 PR-1 locations detected
- [ ] Zones identified correctly
- [ ] Status logic works (free/reserved/occupied)
- [ ] Order info populated correctly
- [ ] Duration calculated correctly
- [ ] No errors in logs

---

## Next Steps

After Phase 1 is complete and tested:

→ **Move to Phase 2:** Basic Views (PHASE2_FILES.md)

---

**Phase 1 Complete!** 🎉
