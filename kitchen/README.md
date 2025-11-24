# Kitchen Designer App

This Django app provides an interactive kitchen design system that allows users to create and visualize kitchen layouts with precise 3D coordinates.

## Features

### Kitchen Model
- **Dimensions**: Define length, width, height, and wall thickness
- **Coordinate System**: Based on looking from below the kitchen upward
  - Width and Length = positive X, Y values
  - Height (depth) = Z-axis
- **Validation**: Ensures length ≥ width for consistency
- **Wall Definitions**: Automatically calculates 4 wall segments with begin/end points

### Kitchen Objects
- **Types**: Doors, Windows, and Other custom objects
- **3D Positioning**: Place objects on any of the 4 walls with precise coordinates
  - Wall selection (Width Wall 1/2, Length Wall 1/2)
  - Distance from wall start point
  - Object width along the wall
  - Height from ground
  - Object height
- **Validation**: Ensures objects fit within kitchen dimensions
- **Automatic 3D Coordinates**: Calculates exact 3D position based on wall placement

## Technology Stack

- **Backend**: Django 5.1 with custom models and validation
- **Frontend**: Bootstrap 5 for UI
- **Interactivity**: 
  - **HTMX**: For seamless AJAX interactions when adding/deleting objects
  - **Alpine.js**: For reactive visualizer controls (zoom, highlighting)
- **Forms**: django-crispy-forms with Bootstrap 5 theme

## URL Structure

```
/kitchen/                          - List all user's kitchens
/kitchen/create/                   - Create new kitchen
/kitchen/<id>/                     - Kitchen detail and object management
/kitchen/<id>/edit/                - Edit kitchen dimensions
/kitchen/<id>/delete/              - Delete kitchen
/kitchen/<id>/visualizer/          - Interactive 2D floor plan visualizer
/kitchen/<id>/add-object/          - HTMX endpoint to add objects
/kitchen/object/<id>/delete/       - HTMX endpoint to delete objects
```

## Key Views

1. **KitchenListView**: Browse all user kitchens
2. **KitchenCreateView**: Create new kitchen with dimensions
3. **KitchenDetailView**: Manage kitchen and add objects
4. **KitchenVisualizerView**: Interactive SVG-based floor plan
5. **HTMX Endpoints**: Dynamic object add/delete without page reload

## Interactive Visualizer

The visualizer page (`kitchen_visualizer.html`) features:
- **SVG-based 2D floor plan** showing kitchen layout from top view
- **Interactive zoom control** (5-50x scale)
- **Object highlighting** on hover
- **Color-coded objects**:
  - 🚪 Green = Doors
  - 🪟 Blue = Windows  
  - 📦 Gray = Other objects
- **Wall labels** showing all 4 walls
- **Dimension indicators** showing length and width
- **Real-time object positioning** based on precise coordinates

## HTMX Integration

Objects can be added and removed without page refresh:
- Form submission via HTMX POST
- Dynamic HTML insertion for new objects
- Delete operations with confirmation
- Smooth transitions and updates

## Alpine.js Features

The visualizer uses Alpine.js for:
- Reactive zoom control
- Object highlighting state
- View angle switching (ready for 3D expansion)
- Clean, declarative interactivity

## Coordinate System Explained

The kitchen uses a consistent coordinate system:

```
        Width Wall 2 (Back)
    (0,L) ●──────────────● (W,L)
          │              │
Length    │              │  Length
Wall 1    │   Kitchen    │  Wall 2
(Left)    │    Space     │  (Right)
          │              │
          │              │
     (0,0)●──────────────● (W,0)
        Width Wall 1 (Front)

Where:
- W = width dimension
- L = length dimension
- Objects placed with precise (X, Y, Z) coordinates
```

## Usage Example

1. **Create Kitchen**:
   - Name: "My Dream Kitchen"
   - Length: 20 units
   - Width: 15 units
   - Height: 10 units

2. **Add Door** (on Width Wall 1):
   - Distance from start: 5 units
   - Object width: 3 units
   - Height from ground: 0 units
   - Object height: 8 units
   - Result: Door at (5, 0) to (8, 0) from ground to 8 units high

3. **Add Window** (on Length Wall 2):
   - Distance from start: 10 units
   - Object width: 4 units
   - Height from ground: 5 units
   - Object height: 3 units
   - Result: Window at (15, 10) to (15, 14) from 5 to 8 units high

4. **Visualize**: View in interactive floor plan with zoom and highlighting

## Admin Interface

Full admin support with:
- Inline object editing within kitchen admin
- List filters by type, wall, date
- Search functionality
- Organized fieldsets for easy data entry

## Future Enhancements

- 3D view mode (foundation already in place with Alpine.js)
- Export to PDF/CAD formats
- Collision detection between objects
- Furniture placement on kitchen floor
- Material/texture selection
- Cost estimation
- Cabinet placement system
