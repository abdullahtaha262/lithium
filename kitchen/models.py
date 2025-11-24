from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import os

class Kitchen(models.Model):
    """
    Represents a kitchen with its dimensions.
    The coordinate system is based on looking from below the kitchen upward:
    - Width and Length represent positive values of x, y
    - Height (depth) is z
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='kitchens'
    )
    name = models.CharField(max_length=255, default=_("My Kitchen"))
    
    # Dimensions
    length = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text=_("Length dimension (Y-axis)")
    )
    width = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text=_("Width dimension (X-axis)")
    )
    height = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text=_("Height dimension (Z-axis)")
    )
    wall_thickness = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=1.0,
        help_text=_("Wall thickness")
    )
    
    # 3D model file (optional for future use)
    model_file = models.FileField(
        upload_to='kitchen_models/', 
        blank=True, 
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Kitchen'
        verbose_name_plural = 'Kitchens'
    
    def clean(self):
        """Validate that length >= width"""
        if self.length and self.width and self.length < self.width:
            raise ValidationError({
                'length': 'Length must be greater than or equal to width.'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} - {self.user.email if hasattr(self.user, 'email') else self.user.id}"
    
    @property
    def kitchen_space_points(self):
        """
        Returns the 4 corner points of the kitchen floor space.
        Point 1 (0,0) -> Point 2 (width,0) -> Point 3 (width,length) -> Point 4 (0,length)
        """
        return [
            (0, 0),
            (float(self.width), 0),
            (float(self.width), float(self.length)),
            (0, float(self.length))
        ]
    
    @property
    def wall_definitions(self):
        """
        Returns the wall definitions with begin and end points.
        """
        w = float(self.width)
        l = float(self.length)
        return {
            'width_wall_1': {'begin': (0, 0), 'end': (w, 0)},
            'width_wall_2': {'begin': (0, l), 'end': (w, l)},
            'length_wall_1': {'begin': (0, 0), 'end': (0, l)},
            'length_wall_2': {'begin': (w, 0), 'end': (w, l)},
        }
    
    def generate_3d_model(self, blender_path='blender'):
        """
        Generate 3D GLB model using Blender.
        
        Args:
            blender_path: Path to Blender executable
            
        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        from .blender_utils import run_blender_generation
        
        success, glb_path, error = run_blender_generation(self, blender_path)
        
        if success:
            self.model_file = glb_path
            self.save(update_fields=['model_file'])
            return True, None
        else:
            return False, error
    
    @property
    def has_3d_model(self):
        """Check if kitchen has a generated 3D model."""
        return bool(self.model_file and self.model_file.name)
    
    def get_placed_furniture_json(self):
        """
        Get JSON representation of all placed furniture for Blender export.
        Returns list of objects in the format expected by create_kitchen.py
        """
        furniture_list = []
        for placed in self.placed_furniture.all():
            furniture_list.append(placed.to_blender_json())
        return furniture_list


class KitchenObject(models.Model):
    """
    Represents objects in the kitchen walls (doors, windows, etc.)
    Objects are positioned on one of the four walls with 3D coordinates.
    """
    
    OBJECT_TYPES = [
        ('door', 'Door'),
        ('window', 'Window'),
        ('other', 'Other'),
    ]
    
    WALL_CHOICES = [
        ('width_wall_1', 'Width Wall 1 (Front)'),
        ('width_wall_2', 'Width Wall 2 (Back)'),
        ('length_wall_1', 'Length Wall 1 (Left)'),
        ('length_wall_2', 'Length Wall 2 (Right)'),
    ]
    
    kitchen = models.ForeignKey(
        Kitchen, 
        on_delete=models.CASCADE,
        related_name='objects'
    )
    object_type = models.CharField(
        max_length=20, 
        choices=OBJECT_TYPES
    )
    description = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Description for 'other' type objects"
    )
    
    # Wall placement
    wall = models.CharField(
        max_length=20, 
        choices=WALL_CHOICES,
        help_text="Which wall the object is placed on"
    )
    
    # Position along the wall (2D coordinates)
    # Distance from wall begin point to object begin
    distance_from_wall_start = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Distance from wall's begin point to object's begin point"
    )
    # Object width along the wall
    object_width = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Width of the object along the wall"
    )
    
    # Height positioning (Z-axis)
    height_from_ground = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Distance from ground (0) to object's bottom edge"
    )
    object_height = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Height of the object"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['kitchen', 'wall', 'distance_from_wall_start']
        verbose_name = 'Kitchen Object'
        verbose_name_plural = 'Kitchen Objects'
    
    def clean(self):
        """Validate object dimensions against kitchen dimensions"""
        if not self.kitchen_id:
            return
        
        # Get wall length based on which wall
        if 'width_wall' in self.wall:
            wall_length = self.kitchen.width
        else:
            wall_length = self.kitchen.length
        
        # Check if object fits on the wall
        object_end = self.distance_from_wall_start + self.object_width
        if object_end > wall_length:
            raise ValidationError({
                'object_width': f'Object extends beyond wall length ({wall_length})'
            })
        
        # Check if object fits within height
        object_top = self.height_from_ground + self.object_height
        if object_top > self.kitchen.height:
            raise ValidationError({
                'object_height': f'Object extends beyond kitchen height ({self.kitchen.height})'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        type_display = self.get_object_type_display()
        if self.object_type == 'other' and self.description:
            type_display = f"{type_display} ({self.description})"
        return f"{type_display} on {self.get_wall_display()} - {self.kitchen.name}"
    
    @property
    def coordinates_3d(self):
        """
        Returns the 3D coordinates of the object.
        Format depends on which wall the object is on.
        """
        wall_def = self.kitchen.wall_definitions[self.wall]
        begin_point = wall_def['begin']
        
        # Calculate based on wall orientation
        if 'width_wall' in self.wall:
            # Object on width walls (varies in X, fixed Y)
            y = begin_point[1]
            x_begin = begin_point[0] + float(self.distance_from_wall_start)
            x_end = x_begin + float(self.object_width)
            
            return {
                'begin': (x_begin, y, float(self.height_from_ground)),
                'end': (x_end, y, float(self.height_from_ground) + float(self.object_height))
            }
        else:
            # Object on length walls (fixed X, varies in Y)
            x = begin_point[0]
            y_begin = begin_point[1] + float(self.distance_from_wall_start)
            y_end = y_begin + float(self.object_width)
            
            return {
                'begin': (x, y_begin, float(self.height_from_ground)),
                'end': (x, y_end, float(self.height_from_ground) + float(self.object_height))
            }


class FurnitureObject(models.Model):
    """
    Catalog of 3D furniture objects that can be placed in kitchens.
    Examples: cabinets, appliances, islands, tables, chairs, etc.
    """
    
    OBJECT_TYPES = [
        ('base_cabinet', 'Base Cabinet'),
        ('wall_cabinet', 'Wall Cabinet'),
        ('tall_cabinet', 'Tall Cabinet'),
        ('island', 'Kitchen Island'),
        ('refrigerator', 'Refrigerator'),
        ('oven', 'Oven/Range'),
        ('dishwasher', 'Dishwasher'),
        ('sink', 'Sink'),
        ('countertop', 'Countertop'),
        ('table', 'Table'),
        ('chair', 'Chair'),
        ('shelf', 'Shelf'),
        ('other', 'Other'),
    ]
    
    # Basic information
    name = models.CharField(
        max_length=255,
        help_text="Name of the furniture object"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the object"
    )
    object_type = models.CharField(
        max_length=30,
        choices=OBJECT_TYPES,
        help_text="Type/category of the furniture"
    )
    
    # 3D model and thumbnail
    glb_file = models.FileField(
        upload_to='furniture_objects/',
        help_text="GLB 3D model file"
    )
    thumbnail = models.ImageField(
        upload_to='furniture_thumbnails/',
        blank=True,
        null=True,
        help_text="Thumbnail preview image"
    )
    
    # Default dimensions (in meters, 1 unit = 1 meter)
    default_width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Default width in meters"
    )
    default_height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Default height in meters"
    )
    default_depth = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Default depth in meters"
    )
    
    # Size constraints
    min_width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum allowed width"
    )
    max_width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum allowed width"
    )
    min_height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum allowed height"
    )
    max_height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum allowed height"
    )
    min_depth = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum allowed depth"
    )
    max_depth = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum allowed depth"
    )
    
    # Wall placement settings
    can_place_on_wall = models.BooleanField(
        default=False,
        help_text="Whether this object can be placed against walls (e.g., cabinets)"
    )
    requires_wall = models.BooleanField(
        default=False,
        help_text="Whether this object must be placed against a wall"
    )
    
    # Availability
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this object is available in the catalog"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['object_type', 'name']
        verbose_name = 'Furniture Object'
        verbose_name_plural = 'Furniture Objects'
    
    def clean(self):
        """Validate dimension constraints"""
        if self.min_width and self.max_width and self.min_width > self.max_width:
            raise ValidationError({'max_width': 'Maximum width must be greater than minimum width'})
        if self.min_height and self.max_height and self.min_height > self.max_height:
            raise ValidationError({'max_height': 'Maximum height must be greater than minimum height'})
        if self.min_depth and self.max_depth and self.min_depth > self.max_depth:
            raise ValidationError({'max_depth': 'Maximum depth must be greater than minimum depth'})
        
        # Validate defaults are within constraints
        if self.default_width and (self.default_width < self.min_width or self.default_width > self.max_width):
            raise ValidationError({'default_width': 'Default width must be between min and max'})
        if self.default_height and (self.default_height < self.min_height or self.default_height > self.max_height):
            raise ValidationError({'default_height': 'Default height must be between min and max'})
        if self.default_depth and (self.default_depth < self.min_depth or self.default_depth > self.max_depth):
            raise ValidationError({'default_depth': 'Default depth must be between min and max'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.get_object_type_display()})"
    
    @property
    def glb_filename(self):
        """Get the filename of the GLB file for JSON export"""
        if self.glb_file:
            return os.path.basename(self.glb_file.name)
        return None


class PlacedFurniture(models.Model):
    """
    Represents furniture objects placed in a specific kitchen.
    Tracks position, size, rotation, and wall association.
    """
    
    WALL_SIDES = [
        ('none', 'None (Free-standing)'),
        ('front', 'Front Wall (Y=0)'),
        ('back', 'Back Wall (Y=length)'),
        ('left', 'Left Wall (X=0)'),
        ('right', 'Right Wall (X=width)'),
    ]
    
    ROTATION_ANGLES = [
        (0, '0° (Original)'),
        (90, '90° (Rotated Right)'),
        (180, '180° (Rotated 180)'),
        (270, '270° (Rotated Left)'),
    ]
    
    # Relationships
    kitchen = models.ForeignKey(
        Kitchen,
        on_delete=models.CASCADE,
        related_name='placed_furniture'
    )
    furniture_object = models.ForeignKey(
        FurnitureObject,
        on_delete=models.CASCADE,
        related_name='placements'
    )
    
    # Position in 3D space (in meters)
    position_x = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="X coordinate (0 = left edge of kitchen)"
    )
    position_y = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Y coordinate (0 = front edge of kitchen)"
    )
    position_z = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        help_text="Z coordinate (0 = floor level)"
    )
    
    # Custom dimensions (can differ from default)
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Custom width in meters"
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Custom height in meters"
    )
    depth = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Custom depth in meters"
    )
    
    # Rotation (in degrees: 0, 90, 180, 270)
    rotation_angle = models.IntegerField(
        choices=ROTATION_ANGLES,
        default=0,
        help_text="Rotation in 90-degree increments"
    )
    
    # Wall association
    is_placed_on_wall = models.BooleanField(
        default=False,
        help_text="Whether this object is placed against a wall"
    )
    wall_side = models.CharField(
        max_length=10,
        choices=WALL_SIDES,
        default='none',
        help_text="Which wall side the object is placed against"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['kitchen', 'created_at']
        verbose_name = 'Placed Furniture'
        verbose_name_plural = 'Placed Furniture'
    
    def clean(self):
        """Validate placement within kitchen bounds and size constraints"""
        if not self.kitchen_id or not self.furniture_object_id:
            return
        
        # Validate dimensions against furniture constraints
        furniture = self.furniture_object
        if self.width < furniture.min_width or self.width > furniture.max_width:
            raise ValidationError({
                'width': f'Width must be between {furniture.min_width}m and {furniture.max_width}m'
            })
        if self.height < furniture.min_height or self.height > furniture.max_height:
            raise ValidationError({
                'height': f'Height must be between {furniture.min_height}m and {furniture.max_height}m'
            })
        if self.depth < furniture.min_depth or self.depth > furniture.max_depth:
            raise ValidationError({
                'depth': f'Depth must be between {furniture.min_depth}m and {furniture.max_depth}m'
            })
        
        # Validate position within kitchen bounds
        kitchen = self.kitchen
        
        # Consider rotation when checking bounds
        if self.rotation_angle in [90, 270]:
            # Rotation swaps width and depth
            effective_width = float(self.depth)
            effective_depth = float(self.width)
        else:
            effective_width = float(self.width)
            effective_depth = float(self.depth)
        
        # Check X bounds
        if self.position_x < 0 or (float(self.position_x) + effective_width) > float(kitchen.width):
            raise ValidationError({
                'position_x': f'Object extends beyond kitchen width ({kitchen.width}m)'
            })
        
        # Check Y bounds
        if self.position_y < 0 or (float(self.position_y) + effective_depth) > float(kitchen.length):
            raise ValidationError({
                'position_y': f'Object extends beyond kitchen length ({kitchen.length}m)'
            })
        
        # Check Z bounds
        if self.position_z < 0 or (float(self.position_z) + float(self.height)) > float(kitchen.height):
            raise ValidationError({
                'position_z': f'Object extends beyond kitchen height ({kitchen.height}m)'
            })
        
        # Validate wall placement requirements
        if furniture.requires_wall and not self.is_placed_on_wall:
            raise ValidationError({
                'is_placed_on_wall': f'{furniture.name} must be placed against a wall'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.furniture_object.name} in {self.kitchen.name}"
    
    @property
    def bounding_box(self):
        """Returns the 2D bounding box of the object on the floor plan"""
        # Consider rotation
        if self.rotation_angle in [90, 270]:
            width = float(self.depth)
            depth = float(self.width)
        else:
            width = float(self.width)
            depth = float(self.depth)
        
        return {
            'x_min': float(self.position_x),
            'y_min': float(self.position_y),
            'x_max': float(self.position_x) + width,
            'y_max': float(self.position_y) + depth,
        }
    
    def to_blender_json(self):
        """Convert to JSON format for Blender script"""
        glb_path = None
        if self.furniture_object.glb_file:
            glb_path = self.furniture_object.glb_file.path
        return {
            'name': self.furniture_object.name,
            'filepath': glb_path,
            'position': [
                float(self.position_x),
                float(self.position_y),
                float(self.position_z)
            ],
            'rotation_degrees': [0, 0, float(self.rotation_angle)],
            'scale': [
                float(self.width) / float(self.furniture_object.default_width),
                float(self.depth) / float(self.furniture_object.default_depth),
                float(self.height) / float(self.furniture_object.default_height)
            ]
        }


class DesignerSettings(models.Model):
    """
    Settings for the kitchen designer interface.
    Uses singleton pattern - only one instance should exist per user or globally.
    """
    
    # User-specific settings (null = global settings)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='designer_settings',
        help_text="User-specific settings (null for global defaults)"
    )
    
    # Placement constraints
    max_placement_depth_from_wall = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.8,
        help_text="Maximum depth allowed from wall for wall-mounted objects (in meters)"
    )
    
    # Grid settings
    grid_snap_size = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.1,
        help_text="Grid snap size in meters (0 = no snap)"
    )
    
    # Spacing
    default_object_spacing = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0.005,
        help_text="Minimum spacing between objects in meters"
    )
    
    # Behavior settings
    allow_object_overlap = models.BooleanField(
        default=False,
        help_text="Whether objects can overlap each other"
    )
    show_placement_guides = models.BooleanField(
        default=True,
        help_text="Show visual guides for valid placement areas"
    )
    enable_snap_to_grid = models.BooleanField(
        default=True,
        help_text="Enable snap-to-grid when placing objects"
    )
    enable_snap_to_wall = models.BooleanField(
        default=True,
        help_text="Enable automatic snap to walls for wall objects"
    )
    
    # Auto-save
    auto_save_interval = models.IntegerField(
        default=30,
        help_text="Auto-save interval in seconds (0 = disabled)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Designer Settings'
        verbose_name_plural = 'Designer Settings'
    
    def __str__(self):
        if self.user:
            return f"Designer Settings for {self.user.email if hasattr(self.user, 'email') else self.user.username}"
        return "Global Designer Settings"
    
    @classmethod
    def get_for_user(cls, user):
        """Get or create settings for a specific user"""
        settings, created = cls.objects.get_or_create(user=user)
        return settings
    
    @classmethod
    def get_global(cls):
        """Get or create global settings"""
        settings, created = cls.objects.get_or_create(user=None)
        return settings
