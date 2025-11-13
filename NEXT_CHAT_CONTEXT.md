# Next Chat Context - Location Occupancy Module

**Created:** 2024-11-13  
**Status:** 🚧 **READY FOR DEVELOPMENT**  
**Module Version:** 0.1.0 (not yet built)

---

## 🎯 MISSION: Build Real-Time Location Occupancy Dashboard

### Quick Context

We need to solve the **race condition problem** where locations appear "occupied" in the system but are physically empty because they're auto-reserved for orders still in production.

**The Solution:** Interactive grid dashboard showing real-time status of all 167 PR-1 locations:
- 🟢 **FREE** - Available for immediate use
- 🟡 **RESERVED** - Assigned to order in production
- 🔴 **OCCUPIED** - Physical box on location

---

## 📋 DEVELOPMENT ROADMAP

See full roadmap in separate document DEVELOPMENT_PHASES.md

**Quick Summary:**
- **Phase 1:** Basic models (2-3h)
- **Phase 2:** Simple views (1-2h)  
- **Phase 3:** Interactive grid (3-4h)
- **Phase 4:** History & assignment (2-3h)

**Total:** 8-12 hours for fully functional module

---

## 🚀 START HERE: Phase 1 Implementation

### Step 1: Clone & Structure (10 min)

```bash
cd /odoo/custom/addons
git clone https://github.com/sprite931/personalizirai_location_occupancy.git
cd personalizirai_location_occupancy

# Create directories
mkdir -p models views static/src/{js,css,xml} security data

# Create __init__.py files
touch __init__.py models/__init__.py
```

### Step 2: Core Files (30 min)

See detailed file contents in PHASE1_FILES.md

Key files to create:
1. `__manifest__.py`
2. `models/__init__.py`  
3. `models/stock_location.py`
4. `security/ir.model.access.csv`

### Step 3: Test Installation

```bash
# Set permissions
sudo chown -R odoo:odoo /odoo/custom/addons/personalizirai_location_occupancy

# Restart Odoo
sudo systemctl restart odoo

# Install via UI
Apps → Update Apps List → Search "Location Occupancy" → Install
```

### Step 4: Verify Computed Fields

```python
# Test in Odoo shell
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
        
        # Find PR-1 locations
        locations = env['stock.location'].search([('is_pr1_location', '=', True)])
        print(f"Found {len(locations)} PR-1 locations")
        
        # Test first 5
        for loc in locations[:5]:
            print(f"\n{loc.name}:")
            print(f"  Status: {loc.occupancy_status}")
            print(f"  Zone: {loc.pr1_zone}")
            if loc.occupancy_order_id:
                print(f"  Order: {loc.occupancy_order_name}")
        
        cr.rollback()
EOF
```

---

## 📊 Expected Results

### After Phase 1:
- ✅ Module installed successfully
- ✅ 167 PR-1 locations identified
- ✅ Computed fields show status (free/reserved/occupied)
- ✅ Zones detected (малък_склад, calandar, teniski)
- ✅ Order info populated for reserved/occupied

### After Phase 2:
- ✅ Menu appears under Sales
- ✅ Tree view with 167 locations
- ✅ Color-coded rows (green/yellow/red)
- ✅ Filters work

### After Phase 3:
- ✅ Interactive grid renders
- ✅ Organized by zones
- ✅ Auto-refresh working
- ✅ Responsive on tablet/laptop

---

## 🔑 Key Technical Decisions

### 1. Computed Fields (NOT Stored)
**Why:** Real-time data, changes frequently
```python
occupancy_status = fields.Selection([...], compute='...', store=False)
```

### 2. Status Detection Logic
```python
def _compute_occupancy_status(self):
    # 1. Check stock.quant → OCCUPIED
    # 2. Check sale_order.source_location_id → RESERVED  
    # 3. Otherwise → FREE
```

### 3. PR-1 Detection
```python
# Parent location ID = 19
location.location_id.id == 19
```

### 4. Zone Detection
```python
# By naming convention:
# M-XXX → малък_склад
# C-XX → calandar
# T-XX → teniski
```

---

## 🐛 Troubleshooting

### Module won't install
```bash
tail -f /var/log/odoo/byi_print_live.log
# Check for Python syntax errors
python3 -m py_compile models/stock_location.py
```

### Fields not computing
```python
# Force recompute
loc._compute_occupancy_status()
loc._compute_pr1_zone()
```

### Wrong location count
```sql
-- Check PR-1 structure
SELECT id, name, location_id 
FROM stock_location 
WHERE location_id = 19 OR id = 19;
```

---

## 📚 Reference Files

All detailed code is split into separate files for readability:

1. **PHASE1_FILES.md** - Complete code for Phase 1
2. **PHASE2_FILES.md** - Views & filters for Phase 2
3. **PHASE3_FILES.md** - JavaScript grid widget
4. **PHASE4_FILES.md** - History & assignment wizard

---

## 💡 Development Tips

### Test Early, Test Often
```bash
# After every change:
sudo systemctl restart odoo
# Then test in browser/shell
```

### Use Odoo Shell for Quick Tests
```python
# Faster than UI testing
env['stock.location'].search([...])._compute_occupancy_status()
```

### Browser Console is Your Friend
```javascript
// Check widget loaded
console.log(odoo.__DEBUG__);
// Check templates
console.log(Object.keys(QWeb.templates));
```

### Follow warehouse_monitoring Pattern
- Standalone views (no inheritance)
- Computed fields (no stored)
- Comprehensive logging
- Clear documentation

---

## 🎯 Success Metrics

### Operational Success:
- Operators save 2-3 min per assignment
- Zero "location occupied" errors for free locations
- 60-second refresh keeps data current

### Technical Success:
- Page loads < 2 seconds
- All 167 locations render correctly
- Responsive on tablet (5 columns) and laptop (10 columns)
- No JavaScript errors in console

### Business Success:
- Ready before peak season (Nov 15)
- Tested with real production data
- Staff trained and confident
- Rollback plan ready

---

## 📞 Questions & Support

**Common Questions:**

Q: Why not store computed fields?  
A: They change frequently, computed on-demand is more accurate

Q: Why not use list view only?  
A: Grid visualization is more intuitive for spatial warehouse layout

Q: Can we add more zones?  
A: Yes, just update `pr1_zone` selection and detection logic

Q: What about other warehouses?  
A: Easily extensible - just change parent location ID filter

**Need Help?**
- Check logs: `/var/log/odoo/byi_print_live.log`
- Review warehouse_monitoring module for patterns
- Test in Odoo shell before UI
- Use browser console for JavaScript debugging

---

## 🚀 Ready to Start!

Next steps:
1. Create file structure
2. Copy Phase 1 code from PHASE1_FILES.md
3. Test installation
4. Verify computed fields
5. Move to Phase 2

Good luck! 🎉

---

**Created for:** PersonaliziRai Development  
**Project:** Location Occupancy Dashboard  
**Timeline:** 8-12 hours development  
**Target:** Production deployment before Nov 15, 2024
