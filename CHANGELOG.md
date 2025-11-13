# Changelog - PersonaliziRai Location Occupancy

## [1.1.0] - 2025-11-13

### ✅ Phase 3: Interactive Grid Dashboard (90% Complete)

#### Added
- **Visual Grid Dashboard**
  - Color-coded location boxes (🟢 Green = Free, 🟡 Yellow = Reserved, 🔴 Red = Occupied)
  - Interactive grid with 131 PR-1 locations
  - Real-time summary statistics (Free: 85, Reserved: 46, Occupied: 0)
  - Auto-refresh every 60 seconds
  - Manual refresh button
  - Last update timestamp display

- **JavaScript Widget** (`static/src/js/occupancy_grid_widget.js`)
  - Odoo 13 AbstractAction-based widget
  - AJAX data fetching (`/occupancy/grid_data`)
  - Auto-refresh with proper cleanup (prevent memory leaks)
  - Click handlers for location details
  - Error handling with user-friendly messages

- **QWeb Templates** (`static/src/xml/occupancy_grid_templates.xml`)
  - Main dashboard template (LocationOccupancyGrid)
  - Zone template (LocationOccupancyZone)
  - Location details modal (LocationDetailsModal)
  - Proper XML encoding (Unicode symbols instead of entities)

- **CSS Styling** (`static/src/css/occupancy_grid.css`)
  - Responsive grid layout
  - Status color classes (.status-free, .status-reserved, .status-occupied)
  - Hover effects with scale transform
  - Tooltip styling
  - Modal styling
  - Mobile/tablet responsive breakpoints

- **Backend Controller** (`controllers/main.py`)
  - JSON-RPC endpoint: `/occupancy/grid_data`
  - Single PR-1 zone (removed Малък Склад/Calandar/Teniski zones)
  - Physical location sorting: Row (A/B) → Level (A-E) → Column (01-14)
  - Batch-optimized queries (2 queries for 131 locations)
  - Error handling with graceful fallbacks

- **Location Details Modal**
  - Status badge with color
  - Order number (if occupied/reserved)
  - Customer name (if occupied/reserved)
  - Duration in days
  - Contextual alerts (free/reserved/occupied messages)
  - Warning for long-term occupancy (>7 days)

#### Changed
- **Zone Structure Simplified**
  - From: 3 zones (Малък Склад, Calandar, Teniski)
  - To: Single PR-1 zone (all locations)
  - Reason: All locations are in PR-1 warehouse, zone names were confusing

- **Location Naming**
  - Display full names: A-A-01, B-C-05 (not shortened)
  - Format: [Row]-[Level]-[Column]
  - Physical structure: 2 rows, 5 levels, ~14 columns

- **Data Fields**
  - Fixed field mapping: `occupancy_customer` (not `occupancy_customer_name`)
  - Fixed field mapping: `occupancy_duration_hours` (not `occupancy_duration_days`)
  - Fixed field mapping: `pr1_zone` (not `occupancy_zone`)
  - Duration conversion: hours → days with rounding

#### Fixed
- **XML Entity Error**
  - Issue: `&times;` entity not recognized by XML parser
  - Fix: Replaced with Unicode symbol `×`
  - Impact: QWeb templates loading correctly

- **CSS Classes Not Applied**
  - Issue: `t-att-class` overwrites entire class attribute
  - Fix: Changed to `t-attf-class` with template syntax
  - Result: Color classes now properly applied

- **Field Name Mismatches**
  - Issue: Controller requesting non-existent fields
  - Fix: Updated to match model field names
  - Files: `controllers/main.py` (lines 66-71, 106-121)

- **Zone Template Header**
  - Issue: Wrong emoji logic for zone names
  - Fix: Simplified to single "📦 PR-1" header
  - File: `static/src/xml/occupancy_grid_templates.xml` (line 64)

#### Performance
- Initial load: <2 seconds (131 locations)
- Refresh: <1 second
- Memory: ~50-100MB browser RAM
- Network: ~20-30KB per refresh
- Database: 2 batch queries (optimized)
- Auto-refresh: Every 60 seconds with concurrent request prevention

#### Known Limitations
- **Grid Layout**: Current sorting doesn't match physical warehouse layout perfectly
  - Current: Linear sort (A-A-01, A-A-02... A-B-01...)
  - Needed: Visual 2D representation matching physical structure
  - Status: 10% remaining work for Phase 3

#### Testing Results
- ✅ Grid renders all 131 locations
- ✅ Colors work (green/yellow/red)
- ✅ Click shows modal with details
- ✅ Auto-refresh works (60s)
- ✅ Manual refresh works
- ✅ Summary stats accurate
- ✅ No console errors
- ✅ Responsive on desktop/tablet
- ⚠️ Grid layout needs physical optimization

#### Deployment
- **Server:** personaliziraibyi.ns1.bg
- **Module Path:** /odoo/custom/addons/personalizirai_location_occupancy
- **Status:** ✅ Working with colors
- **Version:** 1.1.0
- **Deployment Date:** November 13, 2025

#### Files Modified
1. `controllers/main.py` - Backend API endpoint
2. `static/src/js/occupancy_grid_widget.js` - Frontend widget
3. `static/src/css/occupancy_grid.css` - Styling
4. `static/src/xml/occupancy_grid_templates.xml` - HTML templates
5. `views/occupancy_grid_view.xml` - Client action
6. `views/assets.xml` - Asset loading
7. `__init__.py` - Import controllers
8. `__manifest__.py` - Register new files

#### Documentation Added
- `PHASE3_PROGRESS.md` - Current status and next steps
- `PHASE3_READY.md` - Implementation plan
- `PHASE3_COMPLETE.md` - Deployment guide
- Updated `README.md` - Current features

---

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
  - ✅ Resolved in Phase 3 with Grid Dashboard

---

## 🚀 Next: Grid Layout Optimization

Remaining work:
- Optimize grid layout to match physical warehouse structure
- Visual 2D representation
- Row/Level grouping
- Physical location indicators

See `PHASE3_PROGRESS.md` for details.

---

## Commit History (Nov 13, 2025)

**Phase 3 Commits:**
- `0f1ad2c` - Update README with current Phase 3 status
- `9d55996` - Phase 3 Progress documentation
- `9cb70ac` - Debug: current state of grid dashboard
- `efacfc6` - Fix XML entity error - replace &times; with × symbol
- `6f5e4b9` - Add assets.xml to load JS and CSS in Odoo 13
- `9b576a5` - Update __manifest__.py with grid view and assets
- `49cc922` - Update __init__.py to import controllers
- `204f00c` - Add view XML for grid dashboard action and menu
- `d1b4567` - Add QWeb templates for dashboard and modal
- `278dbfb` - Add CSS styles for responsive grid layout
- `fbf4c74` - Add JavaScript widget for interactive grid dashboard

**Phase 1-2 Commits:**
- `541f7cc` - Phase 1: Basic models and logic
- `680c059` - Phase 2: Basic views and menu
- `92f06f4` - Fix: Odoo 13 compatibility
- `c917d4a` - Critical fix: Optimize computed fields
- `ff2d2a1` - Fix: Minimal views for Odoo 13
- `2187492` - Fix: Force custom view to load
- `9a5e4dd` - Try fix: Add invisible="0"

---

**Total Development Time:** ~8 hours  
**Lines of Code:** ~1,200 lines  
**Current Status:** 🟢 90% Complete - Grid works with colors!
