from django.contrib import admin
from django.utils.html import format_html
from .models import Kitchen, KitchenObject, FurnitureObject, PlacedFurniture, DesignerSettings


class KitchenObjectInline(admin.TabularInline):
    model = KitchenObject
    extra = 1
    fields = ['object_type', 'description', 'wall', 'distance_from_wall_start', 
              'object_width', 'height_from_ground', 'object_height']


class PlacedFurnitureInline(admin.TabularInline):
    model = PlacedFurniture
    extra = 0
    fields = ['furniture_object', 'position_x', 'position_y', 'position_z', 
              'width', 'depth', 'height', 'rotation_angle', 'wall_side']
    readonly_fields = ['created_at']


@admin.register(Kitchen)
class KitchenAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'length', 'width', 'height', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['name', 'user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [KitchenObjectInline, PlacedFurnitureInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name')
        }),
        ('Dimensions', {
            'fields': ('length', 'width', 'height', 'wall_thickness')
        }),
        ('3D Model', {
            'fields': ('model_file',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(KitchenObject)
class KitchenObjectAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'object_type', 'wall', 'kitchen', 'created_at']
    list_filter = ['object_type', 'wall', 'created_at']
    search_fields = ['description', 'kitchen__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('kitchen', 'object_type', 'description')
        }),
        ('Wall Placement', {
            'fields': ('wall', 'distance_from_wall_start', 'object_width')
        }),
        ('Height Positioning', {
            'fields': ('height_from_ground', 'object_height')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FurnitureObject)
class FurnitureObjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'object_type', 'thumbnail_preview', 'default_dimensions', 
                    'is_active', 'created_at']
    list_filter = ['object_type', 'is_active', 'can_place_on_wall', 'requires_wall', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'thumbnail_preview']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'object_type', 'is_active')
        }),
        ('3D Model & Preview', {
            'fields': ('glb_file', 'thumbnail', 'thumbnail_preview')
        }),
        ('Default Dimensions (meters)', {
            'fields': ('default_width', 'default_height', 'default_depth')
        }),
        ('Size Constraints', {
            'fields': (
                ('min_width', 'max_width'),
                ('min_height', 'max_height'),
                ('min_depth', 'max_depth')
            )
        }),
        ('Placement Settings', {
            'fields': ('can_place_on_wall', 'requires_wall')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def thumbnail_preview(self, obj):
        """Display thumbnail preview in admin"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px;" />',
                obj.thumbnail.url
            )
        return "No thumbnail"
    thumbnail_preview.short_description = "Thumbnail Preview"
    
    def default_dimensions(self, obj):
        """Display default dimensions in a compact format"""
        return f"{obj.default_width}×{obj.default_depth}×{obj.default_height}m"
    default_dimensions.short_description = "Dimensions (W×D×H)"


@admin.register(PlacedFurniture)
class PlacedFurnitureAdmin(admin.ModelAdmin):
    list_display = ['furniture_object', 'kitchen', 'position_display', 'dimensions_display', 
                    'rotation_angle', 'wall_side', 'created_at']
    list_filter = ['furniture_object__object_type', 'wall_side', 'rotation_angle', 'created_at']
    search_fields = ['furniture_object__name', 'kitchen__name', 'kitchen__user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Object & Kitchen', {
            'fields': ('kitchen', 'furniture_object')
        }),
        ('Position (meters)', {
            'fields': (
                ('position_x', 'position_y', 'position_z'),
            )
        }),
        ('Dimensions (meters)', {
            'fields': (
                ('width', 'depth', 'height'),
            )
        }),
        ('Orientation & Wall', {
            'fields': ('rotation_angle', 'is_placed_on_wall', 'wall_side')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def position_display(self, obj):
        """Display position in compact format"""
        return f"({obj.position_x}, {obj.position_y}, {obj.position_z})"
    position_display.short_description = "Position (X,Y,Z)"
    
    def dimensions_display(self, obj):
        """Display dimensions in compact format"""
        return f"{obj.width}×{obj.depth}×{obj.height}m"
    dimensions_display.short_description = "Size (W×D×H)"


@admin.register(DesignerSettings)
class DesignerSettingsAdmin(admin.ModelAdmin):
    list_display = ['user_display', 'grid_snap_size', 'allow_object_overlap', 
                    'enable_snap_to_grid', 'auto_save_interval']
    list_filter = ['allow_object_overlap', 'show_placement_guides', 'enable_snap_to_grid']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',),
            'description': 'Leave user blank for global default settings'
        }),
        ('Placement Constraints', {
            'fields': ('max_placement_depth_from_wall', 'default_object_spacing')
        }),
        ('Grid Settings', {
            'fields': ('grid_snap_size', 'enable_snap_to_grid')
        }),
        ('Behavior', {
            'fields': ('allow_object_overlap', 'show_placement_guides', 'enable_snap_to_wall')
        }),
        ('Auto-Save', {
            'fields': ('auto_save_interval',),
            'description': 'Set to 0 to disable auto-save'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_display(self, obj):
        """Display user or 'Global Settings'"""
        if obj.user:
            return obj.user.email if hasattr(obj.user, 'email') else obj.user.username
        return "Global Settings"
    user_display.short_description = "User"
