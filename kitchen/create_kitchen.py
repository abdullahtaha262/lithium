import bpy
import json
import os
import sys
import math

# --- Utility Functions (No Changes) ---

def clean_scene():
    """Deletes all objects in the current scene."""
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    print("🧹 Scene cleaned.")

def apply_boolean_modifier(target_obj, cutter_obj):
    """Applies a boolean difference modifier and deletes the cutter."""
    print(f"Applying boolean cut to '{target_obj.name}' using '{cutter_obj.name}'")
    boolean_mod = target_obj.modifiers.new(name="BooleanCutter", type='BOOLEAN')
    boolean_mod.operation = 'DIFFERENCE'
    boolean_mod.object = cutter_obj
    bpy.context.view_layer.objects.active = target_obj
    bpy.ops.object.modifier_apply(modifier=boolean_mod.name)
    bpy.data.objects.remove(cutter_obj, do_unlink=True)

def join_objects(obj_list, final_name="KitchenLayout"):
    """Joins a list of mesh objects into a single object."""
    if not obj_list: return None
    bpy.ops.object.select_all(action='DESELECT')
    for obj in obj_list:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = obj_list[0]
    bpy.ops.object.join()
    final_obj = bpy.context.active_object
    final_obj.name = final_name
    print(f"✅ Room geometry joined into '{final_obj.name}'.")
    return final_obj

def setup_lighting():
    """Sets up enhanced lighting for better wall distinction."""
    print("💡 Setting up lighting...")
    
    # Main key light (bright, from top-front-right)
    bpy.ops.object.light_add(type='SUN', location=(8, -8, 10))
    key_light = bpy.context.active_object
    key_light.name = "KeyLight"
    key_light.data.energy = 4.5
    key_light.data.color = (1.0, 0.98, 0.95)  # Slightly warm white
    key_light.rotation_euler = (math.radians(40), 0, math.radians(-45))
    
    # Fill light (cooler, from left)
    bpy.ops.object.light_add(type='SUN', location=(-8, -3, 7))
    fill_light = bpy.context.active_object
    fill_light.name = "FillLight"
    fill_light.data.energy = 2.5
    fill_light.data.color = (0.95, 0.97, 1.0)  # Slightly cool white
    fill_light.rotation_euler = (math.radians(50), 0, math.radians(60))
    
    # Top light (ambient, from directly above)
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 12))
    top_light = bpy.context.active_object
    top_light.name = "TopLight"
    top_light.data.energy = 2.0
    top_light.rotation_euler = (0, 0, 0)
    
    # Rim light (from behind, helps separate walls)
    bpy.ops.object.light_add(type='SUN', location=(0, 10, 6))
    rim_light = bpy.context.active_object
    rim_light.name = "RimLight"
    rim_light.data.energy = 1.5
    rim_light.rotation_euler = (math.radians(120), 0, 0)
    
    print("✅ Enhanced four-point lighting configured.")

# --- Geometry and Object Placement Functions ---

def create_material(name, base_color, roughness=0.5, metallic=0.0, use_fresnel=False):
    """Creates a PBR material with specified properties and optional Fresnel edge highlighting."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Create shader nodes
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.location = (0, 0)
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    if use_fresnel:
        # Add Fresnel effect for edge highlighting
        fresnel = nodes.new(type='ShaderNodeFresnel')
        fresnel.inputs['IOR'].default_value = 1.15  # Subtle edge glow
        fresnel.location = (-400, -200)
        
        # Color ramp to control fresnel intensity
        color_ramp = nodes.new(type='ShaderNodeValToRGB')
        color_ramp.color_ramp.elements[0].position = 0.6
        color_ramp.color_ramp.elements[1].position = 1.0
        color_ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        color_ramp.color_ramp.elements[1].color = (0.2, 0.2, 0.2, 1)
        color_ramp.location = (-200, -200)
        
        # Mix the fresnel with base color
        mix = nodes.new(type='ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.inputs[6].default_value = base_color  # A (base color)
        # B will be brighter version
        brighter_color = (
            min(base_color[0] + 0.1, 1.0),
            min(base_color[1] + 0.1, 1.0),
            min(base_color[2] + 0.1, 1.0),
            1.0
        )
        mix.inputs[7].default_value = brighter_color  # B (lighter edge)
        mix.location = (-200, 0)
        
        # Connect fresnel to mix factor
        links.new(fresnel.outputs['Fac'], color_ramp.inputs[0])
        links.new(color_ramp.outputs[0], mix.inputs[0])
        
        # Connect mix to bsdf
        links.new(mix.outputs[2], bsdf.inputs['Base Color'])
    
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_walls(dims, wall_props):
    """Generates four walls based on kitchen dimensions."""
    print("🧱 Generating walls...")
    width, depth = dims['width'], dims['depth']
    height, thickness = wall_props['height'], wall_props['thickness']
    
    # Walls extend OUTWARD from the kitchen interior space
    # Interior corners are at (0,0), (width,0), (width,depth), (0,depth)
    # Each wall only covers its own side - corners remain empty (90° gaps)
    
    # Define walls with distinct, more contrasting colors for each
    wall_data = [
        {
            'name': 'Wall_Back',
            # Back wall: along Y=depth, extends outward (positive Y)
            # Only spans the width (doesn't extend into corners)
            'dims': (width, thickness, height), 
            'loc': (width / 2, depth + thickness / 2, height / 2),
            'color': (0.85, 0.82, 0.78, 1.0)  # Warm beige
        },
        {
            'name': 'Wall_Right',
            # Right wall: along X=width, extends outward (positive X)
            # Only spans the depth (doesn't extend into corners)
            'dims': (thickness, depth, height), 
            'loc': (width + thickness / 2, depth / 2, height / 2),
            'color': (0.78, 0.85, 0.82, 1.0)  # Cool mint
        },
        {
            'name': 'Wall_Front',
            # Front wall: along Y=0, extends outward (negative Y)
            # Only spans the width (doesn't extend into corners)
            'dims': (width, thickness, height), 
            'loc': (width / 2, -thickness / 2, height / 2),
            'color': (0.88, 0.84, 0.80, 1.0)  # Light cream
        },
        {
            'name': 'Wall_Left',
            # Left wall: along X=0, extends outward (negative X)
            # Only spans the depth (doesn't extend into corners)
            'dims': (thickness, depth, height), 
            'loc': (-thickness / 2, depth / 2, height / 2),
            'color': (0.82, 0.78, 0.85, 1.0)  # Soft lavender
        }
    ]
    
    walls = []
    for data in wall_data:
        bpy.ops.mesh.primitive_cube_add(location=data['loc'])
        wall = bpy.context.active_object
        wall.name = data['name']
        wall.dimensions = data['dims']
        
        # Create unique material with Fresnel edge highlighting
        wall_material = create_material(
            name=f"{data['name']}_Material",
            base_color=data['color'],
            roughness=0.9,
            metallic=0.0,
            use_fresnel=True
        )
        
        # Apply material
        if wall.data.materials:
            wall.data.materials[0] = wall_material
        else:
            wall.data.materials.append(wall_material)
        
        walls.append(wall)
    return walls

def create_floor(dims, floor_props):
    """Generates the floor plane."""
    print("🏠 Generating floor...")
    width, depth = dims['width'], dims['depth']
    thickness = floor_props['thickness']
    bpy.ops.mesh.primitive_cube_add(location=(width / 2, depth / 2, -thickness / 2))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor.dimensions = (width, depth, thickness)
    
    # Create floor material (light wood/tile color)
    floor_material = create_material(
        name="FloorMaterial",
        base_color=(0.65, 0.55, 0.45, 1.0),  # Darker wood color for contrast
        roughness=0.3,
        metallic=0.0
    )
    
    # Apply material
    if floor.data.materials:
        floor.data.materials[0] = floor_material
    else:
        floor.data.materials.append(floor_material)
    
    return floor

def create_apertures(apertures, walls, dims, wall_props):
    """Creates and applies cutouts for doors and windows."""
    print("🪟 Creating apertures (doors/windows)...")
    width, depth = dims['width'], dims['depth']
    wall_thickness = wall_props['thickness']
    
    for ap in apertures:
        target_wall = walls[ap['wall_index']]
        ap_width, ap_height = ap['dimensions']['width'], ap['dimensions']['height']
        dist_from_start = ap['position']['distance_from_start']
        height_from_floor = ap['position'].get('height_from_floor', 0)
        cutter_thickness = wall_thickness * 1.2
        
        # Wall positions now extend OUTWARD from interior space
        # Interior corners: (0,0), (width,0), (width,depth), (0,depth)
        # Walls only span their own sides (90° corner gaps)
        
        if ap['wall_index'] == 0:  # Back wall (at Y=depth, extending outward)
            dims = (ap_width, cutter_thickness, ap_height)
            loc = (dist_from_start + ap_width/2, depth + wall_thickness/2, height_from_floor + ap_height/2)
        elif ap['wall_index'] == 1:  # Right wall (at X=width, extending outward)
            dims = (cutter_thickness, ap_width, ap_height)
            loc = (width + wall_thickness/2, dist_from_start + ap_width/2, height_from_floor + ap_height/2)
        elif ap['wall_index'] == 2:  # Front wall (at Y=0, extending outward)
            dims = (ap_width, cutter_thickness, ap_height)
            loc = (width - dist_from_start - ap_width/2, -wall_thickness/2, height_from_floor + ap_height/2)
        else:  # Left wall (at X=0, extending outward)
            dims = (cutter_thickness, ap_width, ap_height)
            loc = (-wall_thickness/2, depth - dist_from_start - ap_width/2, height_from_floor + ap_height/2)
        
        bpy.ops.mesh.primitive_cube_add(location=loc)
        cutter = bpy.context.active_object
        cutter.name = f"Cutter_{ap['type']}"
        cutter.dimensions = dims
        apply_boolean_modifier(target_wall, cutter)

# --- place_objects function (MODIFIED) ---

def place_objects(objects_config, base_path):
    """Imports objects, parents them correctly, and places them in the scene."""
    print("🛋️ Placing objects in the scene...")
    if not objects_config:
        print("No objects to place."); return

    for obj_data in objects_config:
        filepath = os.path.join(base_path, obj_data['filepath'])
        if not os.path.exists(filepath):
            print(f"⚠️ Warning: Object file not found, skipping: {filepath}"); continue

        print(f"Importing and parenting '{obj_data['filepath']}'...")
        
        # --- NEW PARENTING LOGIC ---
        # 1. Deselect everything before import to isolate new objects
        bpy.ops.object.select_all(action='DESELECT')
        
        # 2. Import the object. All imported objects will be selected.
        bpy.ops.import_scene.gltf(filepath=filepath)
        imported_objects = bpy.context.selected_objects
        
        if not imported_objects:
            print(f"    -> No objects were imported from {obj_data['filepath']}. Skipping."); continue

        # 3. Find the root(s) of the imported hierarchy.
        #    Roots are objects that have no parent within the imported group.
        roots = [obj for obj in imported_objects if obj.parent not in imported_objects]
        
        control_object = None
        if len(roots) == 1:
            # If there's one clear root, use it as the controller.
            control_object = roots[0]
            print(f"    -> Identified single root '{control_object.name}' for control.")
        else:
            # If multiple roots, create a new Empty to act as a parent controller.
            print(f"    -> Multiple roots found. Creating a new parent Empty.")
            bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
            control_object = bpy.context.active_object
            
            # Parent all original roots to the new Empty
            for root_obj in roots:
                root_obj.parent = control_object
        
        # 4. Apply transformations from JSON to the single control_object.
        #    All children will now follow these transformations.
        control_object.name = obj_data.get('name', 'PlacedObject')
        control_object.location = obj_data['position']
        rotation_deg = obj_data['rotation_degrees']
        control_object.rotation_euler = [math.radians(deg) for deg in rotation_deg]
        control_object.scale = obj_data.get('scale', [1, 1, 1])

# --- Main Execution (No Changes) ---

def main():
    """Main function to run the entire kitchen generation process."""
    argv = sys.argv
    try:
        json_path = argv[argv.index("--") + 1]
    except (ValueError, IndexError):
        print("Error: No JSON file provided. Usage: blender -b -P create_kitchen.py -- /path/to/layout.json"); sys.exit(1)
    if not os.path.exists(json_path):
        print(f"Error: File not found at '{json_path}'"); sys.exit(1)

    with open(json_path, 'r') as f:
        config = json.load(f)
    print(f"✅ Configuration loaded from '{os.path.basename(json_path)}'.")

    clean_scene()
    
    # Set up lighting first
    setup_lighting()
    
    # 1. Generate the room structure
    walls = create_walls(config['kitchen_dimensions'], config['wall_defaults'])
    create_apertures(config['apertures'], walls, config['kitchen_dimensions'], config['wall_defaults'])
    floor = create_floor(config['kitchen_dimensions'], config['floor'])
    
    # 2. Join the room structure into a single object
    room_geometry = walls + [floor]
    join_objects(room_geometry)
    
    # 3. Place objects specified in the JSON
    json_dir = os.path.dirname(os.path.abspath(json_path))
    place_objects(config.get('objects', []), json_dir)
    
    # 4. Export the final scene (room + objects)
    output_filename = os.path.splitext(os.path.basename(json_path))[0] + '.glb'
    output_path = os.path.join(json_dir, output_filename)
    
    print(f"🚀 Exporting final scene to '{output_path}'...")
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format='GLB'
    )
    print("🎉 Script finished successfully!")
    
    # Explicitly exit with success code
    sys.exit(0)

if __name__ == "__main__":
    main()