# PersonaliziRai Location Occupancy Tracker 📦

**Real-time warehouse location occupancy tracking for PR-1 zone**

![Status](https://img.shields.io/badge/status-90%25%20complete-green)
![Phase](https://img.shields.io/badge/phase-3%20in%20progress-blue)
![Odoo](https://img.shields.io/badge/odoo-13-purple)

---

## 🎯 Overview

Interactive grid dashboard for monitoring **131 PR-1 warehouse locations** with real-time occupancy status visualization.

**Key Features:**
- 🎨 **Color-coded grid** (🟢 Free / 🟡 Reserved / 🔴 Occupied)
- 🔄 **Auto-refresh** every 60 seconds
- 📊 **Real-time summary** stats
- 🖱️ **Click for details** (order, customer, duration)
- 📱 **Responsive design** (works on tablet)

---

## 🚀 Current Status (Phase 3)

### ✅ Working Features (90% Complete)

**Backend:**
- ✅ Real-time occupancy status computation
- ✅ Batch-optimized database queries
- ✅ JSON API endpoint (`/occupancy/grid_data`)
- ✅ Correct PR-1 location filtering

**Frontend:**
- ✅ Interactive grid dashboard
- ✅ Color-coded locations (green/yellow/red)
- ✅ Click to view order details
- ✅ Auto-refresh (60s interval)
- ✅ Summary statistics
- ✅ Manual refresh button

**Data:**
- 131 PR-1 locations tracked
- 3 status types: Free / Reserved / Occupied
- Location format: A-A-01, B-C-05 (Row-Level-Column)

### ⚠️ In Progress (10% Remaining)

**Grid Layout Optimization:**
- Need to match physical warehouse layout
- Current: Sorted by Row → Level → Column
- Target: Visual representation of physical structure

---

## 📚 Documentation

- **[PHASE3_PROGRESS.md](PHASE3_PROGRESS.md)** - Current progress & next steps
- **[PHASE3_READY.md](PHASE3_READY.md)** - Implementation plan
- **[PHASE3_COMPLETE.md](PHASE3_COMPLETE.md)** - Deployment guide
- **[PHASE1_2_COMPLETE.md](PHASE1_2_COMPLETE.md)** - Backend implementation
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

---

## 🏗️ Architecture

### Physical Warehouse Structure

```
PR-1 Warehouse:
├─ Row A (Редица A)
│  ├─ Level A (Ниво A - най-долу)
│  ├─ Level B (Ниво B)
│  ├─ Level C (Ниво C)
│  ├─ Level D (Ниво D)
│  └─ Level E (Ниво E - най-горе)
└─ Row B (Редица B)
   ├─ Level A
   ├─ Level B
   ├─ Level C
   ├─ Level D
   └─ Level E

Location Format: [Row]-[Level]-[Column]
Example: B-C-05 = Row B, Level C, Column 5
```

### Technical Stack

```
┌──────────────────────────────────────┐
│  Browser (Grid Dashboard)            │
│  ├─ JavaScript Widget (Odoo 13)      │
│  ├─ QWeb Templates                   │
│  └─ CSS Grid Layout                  │
└──────────────┬───────────────────────┘
               │ AJAX (JSON)
               │ Every 60s
┌──────────────▼───────────────────────┐
│  Odoo Backend                        │
│  ├─ Python Controller                │
│  ├─ stock.location model             │
│  └─ Computed fields (batch queries)  │
└──────────────────────────────────────┘
```

---

## 💻 Installation

### Requirements

- Odoo 13
- PostgreSQL
- Python 3.8+

### Steps

```bash
# 1. Clone repository
cd /odoo/custom/addons
git clone https://github.com/sprite931/personalizirai_location_occupancy.git

# 2. Restart Odoo
sudo systemctl restart odoo

# 3. Install module
# Go to Apps → Search "PersonaliziRai Location Occupancy" → Install

# 4. Access dashboard
# Inventory → Location Occupancy → Occupancy Grid 📊
```

---

## 🎨 Screenshots

**Grid Dashboard:**
- Header with summary stats (Free: 85, Reserved: 46, Occupied: 0)
- Single "📦 PR-1" zone with 131 positions
- Color-coded boxes (green/yellow/red)
- Auto-refresh every 60 seconds
- Click for detailed modal

**Location Details Modal:**
- Status badge (Free/Reserved/Occupied)
- Order number
- Customer name
- Duration in days
- Contextual alerts

---

## 🔧 Development

### File Structure

```
personalizirai_location_occupancy/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── main.py                    # Grid data API
├── models/
│   ├── __init__.py
│   └── stock_location.py          # Computed fields
├── static/src/
│   ├── js/
│   │   └── occupancy_grid_widget.js
│   ├── css/
│   │   └── occupancy_grid.css
│   └── xml/
│       └── occupancy_grid_templates.xml
├── views/
│   ├── assets.xml
│   ├── occupancy_grid_view.xml
│   ├── location_occupancy_views.xml
│   └── location_occupancy_menu.xml
└── security/
    └── ir.model.access.csv
```

### Key Files

**Backend:**
- `models/stock_location.py` - Occupancy status computation
- `controllers/main.py` - JSON API endpoint

**Frontend:**
- `static/src/js/occupancy_grid_widget.js` - Main widget
- `static/src/css/occupancy_grid.css` - Styling
- `static/src/xml/occupancy_grid_templates.xml` - HTML templates

### Local Development

```bash
# Edit files
nano controllers/main.py

# Commit changes
git add -A
git commit -m "Your message"
git push origin main

# Deploy to production
cd /odoo/custom/addons/personalizirai_location_occupancy
git pull origin main
sudo systemctl restart odoo
```

---

## 📊 Performance

**Metrics:**
- Initial load: <2 seconds (131 locations)
- Refresh: <1 second
- Database queries: 2 batch queries (optimized)
- Memory: ~50-100MB browser
- Network: ~20-30KB per refresh

**Optimization:**
- ✅ Batch database queries
- ✅ Computed field caching
- ✅ Efficient DOM updates
- ✅ CSS hardware acceleration
- ✅ Concurrent request prevention

---

## 🐛 Troubleshooting

### Grid Not Loading

```bash
# Check Odoo logs
tail -f /var/log/odoo/byi_print_live.log

# Restart Odoo
sudo systemctl restart odoo

# Hard refresh browser
Ctrl+Shift+R
```

### No Colors Showing

```bash
# Verify assets loaded
# Browser → F12 → Network tab → Look for 404s

# Check CSS file accessible
curl http://yourserver/personalizirai_location_occupancy/static/src/css/occupancy_grid.css

# Clear browser cache
Ctrl+Shift+R
```

### Data Not Updating

```bash
# Test API endpoint manually
# Browser → F12 → Console → Type:
odoo.__DEBUG__.services['web.ajax'].jsonRpc('/occupancy/grid_data', 'call', {})

# Check computed fields
# Inventory → Locations → Open a PR-1 location → Check "Occupancy Status"
```

---

## 🚦 Status Definitions

| Status | Color | Meaning | Database Logic |
|--------|-------|---------|----------------|
| 🟢 **Free** | Green | Location is empty and available | No stock quants, no assigned order |
| 🟡 **Reserved** | Yellow | Location is assigned but empty | No stock quants, order assigned |
| 🔴 **Occupied** | Red | Location has physical inventory | Stock quants exist |

---

## 🎯 Roadmap

### Phase 1-2: Backend ✅ (Complete)
- [x] Computed occupancy status
- [x] Batch-optimized queries
- [x] Zone classification
- [x] Order tracking

### Phase 3: Grid Dashboard 🚧 (90% Complete)
- [x] Visual grid with colors
- [x] Auto-refresh (60s)
- [x] Click for details
- [x] Summary statistics
- [ ] Physical layout optimization

### Phase 4: Advanced Features 📅 (Future)
- [ ] Search/filter locations
- [ ] History tracking
- [ ] Analytics dashboard
- [ ] Assignment wizard
- [ ] Notifications (long occupancy)
- [ ] Export/print functionality

---

## 🤝 Contributing

This is a private project for PersonaliziRai.bg warehouse operations.

---

## 📄 License

LGPL-3

---

## 👨‍💻 Author

**PersonaliziRai.bg**  
Built with ❤️ by Claude (AI Assistant)

---

## 📞 Support

For issues or questions:
- Check documentation in `/docs` folder
- Review `PHASE3_PROGRESS.md` for current status
- See `CHANGELOG.md` for version history

---

**Last Updated:** November 13, 2025  
**Version:** 1.0.0  
**Status:** 🟢 Working with Colors | ⚠️ Layout Optimization Pending
