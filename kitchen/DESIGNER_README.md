# Kitchen Designer Feature

## Overview

The Kitchen Designer is a comprehensive feature that allows users to place, position, resize, and arrange 3D furniture objects in their kitchen layouts using an interactive 2D canvas interface powered by Fabric.js.

## Features

### Core Functionality
- **Interactive 2D Canvas**: Drag-and-drop furniture placement with real-time visual feedback
- **Furniture Catalog**: Browsable catalog with search and filtering by object type
- **Object Manipulation**: 
  - Drag to reposition
  - Resize with min/max constraints
  - Rotate in 90° increments (0°, 90°, 180°, 270°)
  - Duplicate objects
  - Delete objects
- **Smart Placement**:
  - Snap-to-grid functionality
  - Auto-snap to walls for wall-mounted objects
  - Collision detection and overlap prevention
  - Visual placement guides showing valid wall zones
- **Properties Panel**: Real-time editing of position, dimensions, and rotation
- **Zoom & Pan**: Mouse wheel zoom, pan controls, and fit-to-view
- **Auto-save**: Configurable auto-save interval
- **Keyboard Shortcuts**: Full keyboard support for productivity

### Database Models

#### 1. FurnitureObject
Catalog of available furniture objects.

**Fields:**
- `name`: Object name
- `description`: Detailed description
- `object_type`: Category (base_cabinet, wall_cabinet, refrigerator, etc.)
- `glb_file`: 3D model file (GLB format)
- `thumbnail`: Preview image
- `default_width/height/depth`: Default dimensions in meters
- `min_width/height/depth`: Minimum allowed dimensions
- `max_width/height/depth`: Maximum allowed dimensions
- `can_place_on_wall`: Whether object can be placed against walls
- `requires_wall`: Whether object must be placed against a wall
- `is_active`: Whether object is available in catalog

#### 2. PlacedFurniture
Represents furniture placed in a specific kitchen.

**Fields:**
- `kitchen`: Foreign key to Kitchen
- `furniture_object`: Foreign key to FurnitureObject
- `position_x/y/z`: 3D position in meters
- `width/height/depth`: Custom dimensions (can differ from defaults)
- `rotation_angle`: Rotation in degrees (0, 90, 180, 270)
- `is_placed_on_wall`: Whether object is against a wall
- `wall_side`: Which wall (front, back, left, right, none)

**Validation:**
- Ensures objects stay within kitchen bounds
- Validates dimensions against furniture constraints
- Checks rotation and position validity
- Enforces wall requirements

#### 3. DesignerSettings
Global or user-specific designer configuration.

**Fields:**
- `user`: User (null for global settings)
- `max_placement_depth_from_wall`: Maximum depth for wall objects (0.8m default)
- `grid_snap_size`: Grid snap size (0.1m default)
- `default_object_spacing`: Minimum spacing between objects
- `allow_object_overlap`: Whether objects can overlap
- `show_placement_guides`: Show visual placement guides
- `enable_snap_to_grid`: Enable grid snapping
- `enable_snap_to_wall`: Enable wall snapping
- `auto_save_interval`: Auto-save interval in seconds (30s default)

### API Endpoints

All endpoints require authentication and ensure users can only access their own kitchens.

#### Catalog & Settings
- `GET /kitchen/api/furniture-catalog/`: Get furniture catalog (with optional type and search filters)
- `GET /kitchen/api/designer-settings/`: Get user's designer settings

#### Placed Furniture Operations
- `GET /kitchen/api/<kitchen_id>/placed-furniture/`: List all placed furniture in kitchen
- `POST /kitchen/api/<kitchen_id>/place-furniture/`: Place new furniture object
- `POST /kitchen/api/placed-furniture/<id>/position/`: Update position
- `POST /kitchen/api/placed-furniture/<id>/size/`: Update dimensions
- `POST /kitchen/api/placed-furniture/<id>/rotate/`: Rotate object
- `POST /kitchen/api/placed-furniture/<id>/delete/`: Delete placed furniture
- `POST /kitchen/api/placed-furniture/<id>/duplicate/`: Duplicate object

### User Interface

#### Layout
The designer uses a 3-panel layout:

1. **Left Sidebar (Catalog)**:
   - Search bar for filtering by name
   - Category filter buttons
   - Scrollable grid of furniture items with thumbnails
   - Drag-and-drop to canvas

2. **Center Canvas**:
   - Fabric.js canvas with kitchen floor plan
   - Grid overlay (0.5m intervals)
   - Kitchen boundary (blue outline)
   - Wall placement zones (light blue highlighted areas)
   - Placed furniture objects (draggable, resizable)
   - Zoom controls (buttons, slider, mouse wheel)
   - Pan support
   - Real-time dimension display

3. **Right Sidebar (Properties)**:
   - Selected object information
   - Position controls (X, Y with numeric inputs)
   - Size sliders (width, depth, height with min/max constraints)
   - Rotation buttons (0°, 90°, 180°, 270°)
   - Action buttons (Duplicate, Delete)

#### Toolbar
- Back button
- Undo/Redo buttons (with history tracking)
- Save button
- 3D View button (opens visualizer in new tab)
- Save status indicator

### Keyboard Shortcuts

- `Ctrl+Z`: Undo
- `Ctrl+Y`: Redo
- `Delete`: Delete selected object
- `Ctrl+D`: Duplicate selected object
- `R`: Rotate selected object 90°
- `Esc`: Deselect object
- `Ctrl+S`: Save design
- `Arrow Keys`: Fine-tune position (when implemented)

### Workflow

1. **Access Designer**: From kitchen detail page, click "Designer" button
2. **Browse Catalog**: Search or filter furniture by type
3. **Place Furniture**: Drag items from catalog onto canvas
4. **Position & Resize**: 
   - Drag to move
   - Use properties panel for precise positioning
   - Adjust size with sliders (respects min/max constraints)
5. **Rotate**: Use rotation buttons or 'R' key for 90° rotations
6. **Fine-tune**: Properties panel for exact values
7. **Save**: Automatic or manual save
8. **3D Preview**: Click "3D View" to see full 3D model with furniture

### Integration with Blender

The designer integrates with the existing Blender 3D generation system:

1. **JSON Export**: `Kitchen.get_placed_furniture_json()` generates JSON array of placed objects
2. **Blender Format**: Each placed object includes:
   - `name`: Furniture name
   - `filepath`: Path to GLB file
   - `position`: [x, y, z] coordinates
   - `rotation_degrees`: [0, 0, rotation_angle]
   - `scale`: [width_scale, depth_scale, height_scale]
3. **Blender Script**: `create_kitchen.py` reads and places furniture objects using the enhanced parenting logic

### Sample Furniture Objects

The system includes 11 sample furniture objects:

1. Base Cabinet 60cm (0.6×0.6×0.85m)
2. Base Cabinet 90cm (0.9×0.6×0.85m)
3. Wall Cabinet 60cm (0.6×0.35×0.7m)
4. Refrigerator Standard (0.7×0.7×1.8m)
5. Oven Range 60cm (0.6×0.6×0.85m)
6. Dishwasher 60cm (0.6×0.6×0.85m)
7. Kitchen Sink Single (0.8×0.5×0.2m)
8. Kitchen Island 120cm (1.2×0.8×0.9m)
9. Tall Pantry Cabinet (0.6×0.6×2.2m)
10. Dining Table 150cm (1.5×0.9×0.75m)
11. Dining Chair (0.45×0.5×0.9m)

### Admin Interface

Comprehensive admin panels for managing:

- **FurnitureObject**: Add/edit furniture with thumbnail preview, dimension constraints, placement settings
- **PlacedFurniture**: View and edit placed furniture per kitchen
- **DesignerSettings**: Configure global or user-specific settings
- **Kitchen**: View placed furniture inline with kitchen details

### Technical Stack

- **Backend**: Django 4.x, Python 3.11
- **Frontend**: 
  - Fabric.js 5.3.0 (2D canvas manipulation)
  - Bootstrap 5.3.3 (UI components)
  - Bootstrap Icons (iconography)
  - Vanilla JavaScript (state management)
- **Database**: SQLite (development), PostgreSQL-compatible
- **3D Integration**: Blender 3.x via Python subprocess

### Best Practices

1. **Unit System**: Consistent 1 unit = 1 meter throughout
2. **Validation**: All dimensions validated at model level
3. **Permissions**: Users can only access their own kitchens
4. **Error Handling**: Comprehensive validation and error messages
5. **Performance**: 
   - Efficient canvas rendering
   - Lazy loading of furniture catalog
   - Optimized API calls
6. **User Experience**:
   - Real-time visual feedback
   - Clear placement guides
   - Intuitive controls
   - Keyboard shortcuts for power users

### Future Enhancements

Potential improvements:

1. **Collision Detection**: Full overlap prevention (currently basic)
2. **Wall Snapping**: More sophisticated wall detection and snapping
3. **3D View Integration**: Inline 3D preview in designer
4. **Custom Objects**: Allow users to upload custom furniture models
5. **Templates**: Save and load furniture arrangements as templates
6. **Measurements**: Show distances between objects
7. **Layers**: Organize objects in layers
8. **Copy/Paste**: Copy furniture arrangements between kitchens
9. **Materials**: Assign materials/colors to furniture
10. **Export Options**: PDF floor plans, CSV object lists

### Usage Example

```python
# Access designer
# Navigate to: /kitchen/<kitchen_id>/designer/

# In Python/Django shell:
from kitchen.models import Kitchen, FurnitureObject, PlacedFurniture

# Get kitchen
kitchen = Kitchen.objects.get(pk=1)

# Place a base cabinet
cabinet = FurnitureObject.objects.get(name="Base Cabinet 60cm")
placed = PlacedFurniture.objects.create(
    kitchen=kitchen,
    furniture_object=cabinet,
    position_x=1.0,
    position_y=0.0,
    position_z=0.0,
    width=cabinet.default_width,
    height=cabinet.default_height,
    depth=cabinet.default_depth,
    rotation_angle=0,
    is_placed_on_wall=True,
    wall_side='front',
)

# Get all placed furniture as JSON for Blender
furniture_json = kitchen.get_placed_furniture_json()

# Generate 3D model with furniture
success, error = kitchen.generate_3d_model()
```

### Testing

To test the designer:

1. Create a kitchen
2. Add doors/windows (existing feature)
3. Click "Designer" button
4. Drag furniture from catalog
5. Resize, rotate, position
6. Save and view in 3D

### Files Modified/Created

#### New Files
- `kitchen/models.py`: Added FurnitureObject, PlacedFurniture, DesignerSettings
- `templates/kitchen/kitchen_designer.html`: Main designer interface
- `create_sample_furniture.py`: Sample data creation script
- `kitchen/fixtures/` directory

#### Modified Files
- `kitchen/views.py`: Added 9 designer views and API endpoints
- `kitchen/urls.py`: Added designer routes
- `kitchen/admin.py`: Added admin interfaces for new models
- `kitchen/blender_utils.py`: Updated to include placed furniture in JSON
- `templates/kitchen/kitchen_detail.html`: Added Designer button
- `requirements.txt`: Added Pillow for image handling

#### Migrations
- `kitchen/migrations/0003_furnitureobject_designersettings_placedfurniture.py`

## Installation

1. Install dependencies:
   ```bash
   pip install Pillow
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Create sample furniture:
   ```bash
   python manage.py shell < create_sample_furniture.py
   ```

4. Access designer at: `/kitchen/<kitchen_id>/designer/`

## Support

For issues or questions, refer to the main project documentation or create an issue in the repository.
