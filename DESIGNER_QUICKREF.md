# Kitchen Designer - Quick Reference

## 🚀 Access
**URL**: `/kitchen/<kitchen_id>/designer/`  
**Button**: Kitchen detail page → "Designer" (blue button)

## 🎨 Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│  ← Back  │  Undo  Redo  │  Save  3D View  │  ● Saved       │ TOOLBAR
├─────────────────────────────────────────────────────────────┤
│          │                                 │                 │
│ CATALOG  │          CANVAS                │  PROPERTIES     │
│          │                                 │                 │
│ Search   │  ┌─────────────────────┐       │  📦 Object Info │
│ [......] │  │                     │       │  Name: Cabinet  │
│          │  │   Kitchen Floor     │       │  Type: Base     │
│ Filters: │  │                     │       │                 │
│ [All]    │  │   ╔═══════════╗     │       │  📍 Position    │
│ [Base]   │  │   ║ Cabinet   ║     │       │  X: [1.5] m     │
│ [Wall]   │  │   ╚═══════════╝     │       │  Y: [2.0] m     │
│ ...      │  │                     │       │                 │
│          │  │   Grid (0.5m)       │       │  📏 Dimensions  │
│ ┌──────┐ │  └─────────────────────┘       │  Width:  [0.6]m │
│ │ 📦   │ │                                 │  Depth:  [0.6]m │
│ │Base  │ │  Zoom: [-][====|====][+] 100%  │  Height: [0.85]m│
│ └──────┘ │  [Fit to View]                 │                 │
│          │                                 │  🔄 Rotation    │
│ ┌──────┐ │  Kitchen: 5m × 4m               │  [0°] [90°]     │
│ │ 🧊   │ │  Drag to place • Wheel to zoom  │  [180°] [270°]  │
│ │Fridge│ │                                 │                 │
│ └──────┘ │                                 │  ⚙️ Actions     │
│ ...      │                                 │  [📋 Duplicate] │
│          │                                 │  [🗑️ Delete]    │
└──────────┴─────────────────────────────────┴─────────────────┘
```

## 🎯 Quick Actions

### Place Furniture
1. Find object in catalog (search/filter)
2. **Drag** from catalog → **Drop** on canvas
3. Object appears at drop location

### Move Object
- **Click & Drag** object on canvas
- OR use Position fields in Properties panel

### Resize Object
- Select object
- Use **sliders** in Properties panel
- Respects min/max constraints

### Rotate Object
- Select object
- Click rotation button (0°, 90°, 180°, 270°)
- OR press `R` key

### Delete Object
- Select object
- Click **Delete** button
- OR press `Delete` key

### Duplicate Object
- Select object  
- Click **Duplicate** button
- OR press `Ctrl+D`

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Delete` | Delete selected |
| `Ctrl+D` | Duplicate |
| `R` | Rotate 90° |
| `Esc` | Deselect |
| `Ctrl+S` | Save |

## 🖱️ Mouse Controls

| Action | Control |
|--------|---------|
| **Place** | Drag from catalog → Drop on canvas |
| **Move** | Click & drag object |
| **Select** | Click object |
| **Deselect** | Click empty area or press Esc |
| **Zoom In** | Mouse wheel up |
| **Zoom Out** | Mouse wheel down |
| **Pan** | Drag canvas background |

## 📐 Object Types

### Wall-Mounted (Snaps to walls)
- Base Cabinets (60cm, 90cm)
- Wall Cabinets  
- Tall Cabinets
- Refrigerator
- Oven/Range
- Dishwasher

### Free-Standing
- Kitchen Island
- Dining Table
- Dining Chair
- Sink (can be wall-mounted)

## 💾 Saving

- **Auto-save**: Every 30 seconds (configurable)
- **Manual save**: Click Save button or `Ctrl+S`
- **Status**: Watch indicator in toolbar (● Saved / ⏳ Saving / ⚠ Error)

## 🎨 Visual Guides

- **Blue outline**: Kitchen boundary
- **Light blue zones**: Valid wall placement areas (0.8m from walls)
- **Grid**: 0.5m intervals (major lines every 1m)
- **Gray rectangles**: Placed furniture objects
- **Blue corners**: Selected object handles

## 🔧 Settings (Admin Panel)

Navigate to: Admin → Designer Settings

- **Grid Snap Size**: 0.1m (snap precision)
- **Max Wall Depth**: 0.8m (how far from wall objects can go)
- **Object Spacing**: 0.05m (minimum gap between objects)
- **Show Guides**: On/Off (blue wall zones)
- **Snap to Grid**: On/Off
- **Snap to Wall**: On/Off (auto-align to walls)
- **Auto-save**: 30s interval

## 📦 Adding Custom Furniture (Admin)

1. Go to Admin → Furniture Objects
2. Click "Add Furniture Object"
3. Fill in:
   - Name, Description, Type
   - Upload GLB file
   - Upload thumbnail (optional)
   - Set default dimensions (width, height, depth)
   - Set min/max constraints
   - Choose wall placement options
4. Mark as Active
5. Save

## 🎬 Typical Workflow

```
1. Open Designer
   ↓
2. Browse Catalog (search/filter)
   ↓
3. Drag & Drop furniture
   ↓
4. Position & Arrange
   ↓
5. Resize if needed (sliders)
   ↓
6. Rotate if needed (buttons or R key)
   ↓
7. Save (auto or manual)
   ↓
8. View in 3D (click 3D View button)
```

## 🐛 Troubleshooting

**Objects won't place?**
- Check if outside kitchen bounds
- Verify wall requirements (some objects require walls)
- Check collision with existing objects

**Can't resize?**
- Objects have min/max constraints
- Check FurnitureObject settings in admin

**Auto-save not working?**
- Check DesignerSettings in admin
- Verify interval is > 0

**3D View doesn't show furniture?**
- Ensure GLB files exist at correct paths
- Check media/furniture_objects/ directory
- Verify FurnitureObject.glb_file paths

## 📊 Limitations

- **Rotation**: 90° increments only (no free rotation)
- **Height**: Currently Z=0 (floor level) for most objects
- **GLB Files**: Placeholder paths (need actual 3D models)
- **Overlap**: Basic validation (full collision detection TBD)

## 🎓 Tips

1. **Use Search**: Faster than scrolling catalog
2. **Use Grid**: Enable snap-to-grid for alignment
3. **Use Properties**: For precise positioning
4. **Save Often**: Manual save before leaving
5. **Start with Walls**: Place wall cabinets first
6. **Center Island Last**: Add island after perimeter
7. **Check 3D**: Preview in 3D view regularly
8. **Use Keyboard**: Shortcuts speed up workflow

## 📞 Support

- **Documentation**: See `kitchen/DESIGNER_README.md`
- **Summary**: See `DESIGNER_SUMMARY.md`
- **Code**: Check `kitchen/views.py`, `kitchen/models.py`
- **Issues**: Check Django error logs

---

**Version**: 1.0  
**Last Updated**: 2025-01-24  
**Compatible with**: Django 4.x, Python 3.11+
