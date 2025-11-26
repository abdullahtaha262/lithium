"""
Utility functions for generating Blender-compatible JSON from Kitchen models.
"""
import json
import os
from pathlib import Path
from django.conf import settings


def kitchen_to_blender_json(kitchen):
    """
    Converts a Kitchen model instance to the JSON format expected by create_kitchen.py.
    
    Args:
        kitchen: Kitchen model instance
        
    Returns:
        dict: Configuration dictionary for Blender script
    """
    # Map our wall choices to indices (0=Back, 1=Right, 2=Front, 3=Left)
    # SWAPPED: Right and Left are swapped to match user perspective
    wall_mapping = {
        'width_wall_2': 0,  # Back wall (at Y=length)
        'length_wall_2': 3,  # Right wall -> mapped to Left index (swapped)
        'width_wall_1': 2,   # Front wall (at Y=0)
        'length_wall_1': 1,  # Left wall -> mapped to Right index (swapped)
    }
    
    # Kitchen dimensions
    config = {
        'kitchen_dimensions': {
            'width': float(kitchen.width),
            'depth': float(kitchen.length),  # In Blender script, depth = our length
        },
        'wall_defaults': {
            'height': float(kitchen.height),
            'thickness': float(kitchen.wall_thickness),
        },
        'floor': {
            'thickness': 0.1,  # Default floor thickness
        },
        'apertures': [],
        'objects': []  # For future furniture/cabinet placement
    }
    
    # Convert kitchen objects to apertures
    for obj in kitchen.objects.all():
        # Map wall to Blender index
        wall_index = wall_mapping.get(obj.wall)
        if wall_index is None:
            continue
        
        # Determine aperture type
        aperture_type = 'door' if obj.object_type == 'door' else 'window'
        
        aperture = {
            'type': aperture_type,
            'wall_index': wall_index,
            'dimensions': {
                'width': float(obj.object_width),
                'height': float(obj.object_height),
            },
            'position': {
                'distance_from_start': float(obj.distance_from_wall_start),
                'height_from_floor': float(obj.height_from_ground),
            }
        }
        
        config['apertures'].append(aperture)
    
    # Add placed furniture objects
    config['objects'] = kitchen.get_placed_furniture_json()
    
    return config


def save_kitchen_json(kitchen, output_dir=None):
    """
    Saves kitchen configuration as JSON file for Blender processing.
    
    Args:
        kitchen: Kitchen model instance
        output_dir: Directory to save JSON file (defaults to media/kitchen_json/)
        
    Returns:
        str: Path to saved JSON file
    """
    if output_dir is None:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'kitchen_json')
    
    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    filename = f'kitchen_{kitchen.pk}_{kitchen.user.pk}.json'
    filepath = os.path.join(output_dir, filename)
    
    # Generate and save JSON
    config = kitchen_to_blender_json(kitchen)
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)
    
    return filepath


def get_blender_script_path():
    """Returns the path to the create_kitchen.py Blender script."""
    return os.path.join(settings.BASE_DIR, 'kitchen', 'create_kitchen.py')


def get_expected_glb_path(kitchen, json_path):
    """
    Returns the expected path where Blender will save the GLB file.
    
    Args:
        kitchen: Kitchen model instance
        json_path: Path to the JSON config file
        
    Returns:
        str: Expected GLB file path
    """
    # Blender script saves GLB in same directory as JSON with same base name
    json_dir = os.path.dirname(json_path)
    json_basename = os.path.basename(json_path)
    glb_filename = os.path.splitext(json_basename)[0] + '.glb'
    return os.path.join(json_dir, glb_filename)


def run_blender_generation(kitchen, blender_executable='blender'):
    """
    Runs the Blender script to generate a 3D model from kitchen data.
    
    Args:
        kitchen: Kitchen model instance
        blender_executable: Path to Blender executable (default: 'blender' in PATH)
        
    Returns:
        tuple: (success: bool, glb_path: str or None, error_message: str or None)
    """
    import subprocess
    
    # Save kitchen configuration as JSON
    json_path = save_kitchen_json(kitchen)
    script_path = get_blender_script_path()
    expected_glb_path = get_expected_glb_path(kitchen, json_path)
    
    # Build Blender command
    # -b: background mode (no GUI)
    # -P: run Python script
    # --: arguments for the script
    cmd = [
        blender_executable,
        '-b',
        '-P', script_path,
        '--', json_path
    ]
    
    try:
        # Run Blender process
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        # Check return code first
        if result.returncode != 0:
            error_msg = f"Blender process failed with code {result.returncode}.\nStderr: {result.stderr}\nStdout: {result.stdout}"
            return False, None, error_msg
        
        # Check if GLB was created
        if os.path.exists(expected_glb_path):
            # Return relative path from MEDIA_ROOT for Django FileField
            relative_path = os.path.relpath(expected_glb_path, settings.MEDIA_ROOT)
            return True, relative_path, None
        else:
            error_msg = f"Blender ran successfully but GLB file not found at {expected_glb_path}.\nStdout: {result.stdout}"
            return False, None, error_msg
            
    except subprocess.TimeoutExpired:
        return False, None, "Blender process timed out after 2 minutes"
    except FileNotFoundError:
        return False, None, f"Blender executable not found: {blender_executable}. Please install Blender or provide correct path."
    except Exception as e:
        return False, None, f"Error running Blender: {str(e)}"


def check_blender_available(blender_executable='blender'):
    """
    Checks if Blender is available in the system.
    
    Args:
        blender_executable: Path to Blender executable
        
    Returns:
        tuple: (available: bool, version: str or None)
    """
    import subprocess
    
    try:
        result = subprocess.run(
            [blender_executable, '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Extract version from output
            version_line = result.stdout.split('\n')[0]
            return True, version_line
        else:
            return False, None
            
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False, None
