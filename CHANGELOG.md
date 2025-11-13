# Changelog - PersonaliziRai Location Occupancy

## [1.0.0] - 2024-11-13

### ✅ COMPLETED: Phase 1 + Phase 2 (Basic Models & Views)

#### Added
- **Stock Location Model Extensions**
  - `occupancy_status` computed field (free/reserved/occupied)
  - `occupancy_order_id` - linked sale order
  - `occupancy_order_name` - order number
  - `occupancy_magento_id` - Magento order ID
  - `occupancy_customer` - customer name
  - `occupancy_since` - timestamp when status changed
  - `occupancy_duration_hours` - how long in current status
  - `is_pr1_location` - boolean to identify PR-1 child locations
  - `pr1_zone` - zone classification (Малък Склад/Calandar/Teniski)
  - Placeholder fields for Phase 4 statistics

- **Batch Optimization**
  - Single query for all quants (instead of per-location)
  - Single query for all orders (instead of per-location)
  - Performance: 500+ queries reduced to 2 queries
  - Prevents database locks during module install

- **Views**
  - Tree view with custom columns (Location, Zone, Status, Order, Customer, Duration)
  - Search view with filters by status and zone
  - Group By functionality (Status, Zone)
  - Menu: Inventory → Warehouse → Location Occupancy → PR-1 Locations

- **Security**
  - Read access for base.group_user
  - Full access for stock.group_stock_manager

#### Fixed
- **XML Validation Errors** (Multiple iterations)
  - Removed unsupported `widget="badge"` for Odoo 13
  - Removed unsupported `widget="percentage"` for Odoo 13
  - Removed emoji from filter labels (XML encoding issues)
  - Simplified view structure for Odoo 13 compatibility

- **Performance Issues**
  - Fixed computed field causing 500+ SQL queries
  - Implemented batch query optimization
  - Fixed database lock during module installation
  - Reduced page load time to <2 seconds

- **View Loading Issues**
  - Added explicit `view_id` reference in action
  - Set `priority=1` on custom views
  - Fixed default view override

#### Known Issues
- **Row Colors Not Working**
  - `decoration-*` attributes don't work with `store=False` computed fields in Odoo 13
  - Data displays correctly, but no visual color coding
  - Will be resolved in Phase 3 with Grid Dashboard (colored boxes)

#### Technical Details
- **Module Structure:**
  ```
  personalizirai_location_occupancy/
  ├── __init__.py
  ├── __manifest__.py
  ├── models/
  │   ├── __init__.py
  │   └── stock_location.py (400+ lines)
  ├── views/
  │   ├── location_occupancy_views.xml
  │   └── location_occupancy_menu.xml
  └── security/
      └── ir.model.access.csv
  ```

- **Database Impact:**
  - No new tables created (inherit existing stock.location)
  - All fields are computed (no storage overhead)
  - 2 additional queries per page load (optimized batch queries)

- **Dependencies:**
  - base
  - stock
  - sale
  - web

#### Testing Results
- ✅ Module installs without errors
- ✅ 167 PR-1 locations detected correctly
- ✅ Zones identified correctly (M-*, C-*, T-*)
- ✅ Status computation works (free/reserved/occupied)
- ✅ Order info populated correctly
- ✅ Duration calculated correctly
- ✅ Filters work (Free, Reserved, Occupied)
- ✅ Group By works (Status, Zone)
- ✅ Performance <2 seconds page load
- ❌ Row decoration colors not working (known Odoo 13 limitation)

#### Deployment
- **Server:** personaliziraibyi.ns1.bg
- **Database:** byi_print_staging_personalizirai_stenik_cloud
- **Module Path:** /odoo/custom/addons/personalizirai_location_occupancy
- **Status:** ✅ Installed and functional
- **Version:** 1.0.0

---

## 🚀 Next: Phase 3 - Interactive Grid Dashboard

See `PHASE3_READY.md` for next steps.

---

## Commit History (Nov 13, 2024)

- `541f7cc` - Phase 1: Basic models and logic - Foundation files
- `680c059` - Phase 2: Basic views and menu
- `92f06f4` - Fix: Odoo 13 compatibility - remove unsupported widgets
- `c917d4a` - Critical fix: Optimize computed fields with batch queries
- `ff2d2a1` - Fix: Minimal views for Odoo 13 compatibility
- `2187492` - Fix: Force custom view to load with explicit view_id reference
- `9a5e4dd` - Try fix: Add invisible="0" to force status field evaluation

---

**Total Development Time:** ~3 hours
**Lines of Code:** ~500 lines
**SQL Queries Optimized:** 500+ → 2
