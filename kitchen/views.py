from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from decimal import Decimal, InvalidOperation
import json
from .models import Kitchen, KitchenObject, FurnitureObject, PlacedFurniture, DesignerSettings
from .forms import KitchenForm, KitchenObjectForm


class KitchenListView(LoginRequiredMixin, ListView):
    """List all kitchens for the logged-in user"""
    model = Kitchen
    template_name = 'kitchen/kitchen_list.html'
    context_object_name = 'kitchens'
    
    def get_queryset(self):
        return self.request.user.kitchens.all()


class KitchenCreateView(LoginRequiredMixin, CreateView):
    """Create a new kitchen"""
    model = Kitchen
    form_class = KitchenForm
    template_name = 'kitchen/kitchen_form.html'
    success_url = reverse_lazy('kitchen:kitchen_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class KitchenUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing kitchen"""
    model = Kitchen
    form_class = KitchenForm
    template_name = 'kitchen/kitchen_form.html'
    
    def get_queryset(self):
        return self.request.user.kitchens.all()
    
    def get_success_url(self):
        return reverse_lazy('kitchen:kitchen_detail', kwargs={'pk': self.object.pk})


class KitchenDetailView(LoginRequiredMixin, DetailView):
    """View kitchen details and manage objects"""
    model = Kitchen
    template_name = 'kitchen/kitchen_detail.html'
    context_object_name = 'kitchen'
    
    def get_queryset(self):
        return self.request.user.kitchens.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_form'] = KitchenObjectForm(kitchen=self.object)
        context['objects'] = self.object.objects.all()
        return context


class KitchenDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a kitchen"""
    model = Kitchen
    template_name = 'kitchen/kitchen_confirm_delete.html'
    success_url = reverse_lazy('kitchen:kitchen_list')
    
    def get_queryset(self):
        return self.request.user.kitchens.all()


@login_required
def add_kitchen_object(request, kitchen_pk):
    """Add an object to a kitchen (HTMX endpoint)"""
    kitchen = get_object_or_404(Kitchen, pk=kitchen_pk, user=request.user)
    
    if request.method == 'POST':
        form = KitchenObjectForm(request.POST, kitchen=kitchen)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.kitchen = kitchen
            obj.save()
            
            # Return the object HTML for HTMX to append
            if request.headers.get('HX-Request'):
                html = render_to_string(
                    'kitchen/partials/object_item.html',
                    {'object': obj},
                    request=request
                )
                return HttpResponse(html)
            
            return redirect('kitchen:kitchen_detail', pk=kitchen_pk)
    
    return redirect('kitchen:kitchen_detail', pk=kitchen_pk)


@login_required
def delete_kitchen_object(request, pk):
    """Delete a kitchen object (HTMX endpoint)"""
    obj = get_object_or_404(KitchenObject, pk=pk, kitchen__user=request.user)
    kitchen_pk = obj.kitchen.pk
    obj.delete()
    
    if request.headers.get('HX-Request'):
        return HttpResponse('')
    
    return redirect('kitchen:kitchen_detail', pk=kitchen_pk)


@login_required
def kitchen_visualizer(request, pk):
    """Interactive kitchen visualizer page"""
    kitchen = get_object_or_404(Kitchen, pk=pk, user=request.user)
    
    context = {
        'kitchen': kitchen,
        'objects': kitchen.objects.all(),
        'placed_furniture': kitchen.placed_furniture.all(),
    }
    
    return render(request, 'kitchen/kitchen_visualizer.html', context)


@login_required
def generate_3d_model(request, pk):
    """Generate 3D GLB model for a kitchen"""
    kitchen = get_object_or_404(Kitchen, pk=pk, user=request.user)
    
    if request.method == 'POST':
        try:
            # Run generation
            success, error = kitchen.generate_3d_model()
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': '3D model generated successfully!',
                    'model_url': kitchen.model_file.url if kitchen.model_file else None
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': error or 'Failed to generate 3D model'
                }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            }, status=500)
    
    return redirect('kitchen:kitchen_detail', pk=pk)


# ============ Kitchen Designer Views ============

@login_required
def kitchen_designer(request, pk):
    """Kitchen designer interface for placing and arranging furniture"""
    kitchen = get_object_or_404(Kitchen, pk=pk, user=request.user)
    
    wall_objects = [
        {
            'id': obj.id,
            'object_type': obj.object_type,
            'wall': obj.wall,
            'distance_from_wall_start': float(obj.distance_from_wall_start),
            'object_width': float(obj.object_width),
            'height_from_ground': float(obj.height_from_ground),
            'object_height': float(obj.object_height),
        }
        for obj in kitchen.objects.all()
    ]
    
    context = {
        'kitchen': kitchen,
        'placed_furniture': kitchen.placed_furniture.select_related('furniture_object').all(),
        'wall_objects': wall_objects,
    }
    
    return render(request, 'kitchen/kitchen_designer.html', context)


@login_required
@require_http_methods(["GET"])
def furniture_catalog_api(request):
    """API endpoint to get furniture catalog"""
    object_type = request.GET.get('type', None)
    search = request.GET.get('search', '')
    
    furniture = FurnitureObject.objects.filter(is_active=True)
    
    if object_type:
        furniture = furniture.filter(object_type=object_type)
    
    if search:
        furniture = furniture.filter(name__icontains=search)
    
    data = []
    for item in furniture:
        data.append({
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'object_type': item.object_type,
            'object_type_display': item.get_object_type_display(),
            'thumbnail': item.thumbnail.url if item.thumbnail else None,
            'glb_file': item.glb_file.url if item.glb_file else None,
            'default_width': float(item.default_width),
            'default_height': float(item.default_height),
            'default_depth': float(item.default_depth),
            'min_width': float(item.min_width),
            'max_width': float(item.max_width),
            'min_height': float(item.min_height),
            'max_height': float(item.max_height),
            'min_depth': float(item.min_depth),
            'max_depth': float(item.max_depth),
            'can_place_on_wall': item.can_place_on_wall,
            'requires_wall': item.requires_wall,
        })
    
    return JsonResponse({'furniture': data})


@login_required
@require_http_methods(["GET", "POST"])
def designer_settings_api(request):
    """API endpoint to get or update designer settings"""
    settings = DesignerSettings.get_for_user(request.user)

    def serialize(payload):
        return {
            'max_placement_depth_from_wall': float(payload.max_placement_depth_from_wall),
            'grid_snap_size': float(payload.grid_snap_size),
            'default_object_spacing': float(payload.default_object_spacing),
            'allow_object_overlap': payload.allow_object_overlap,
            'show_placement_guides': payload.show_placement_guides,
            'enable_snap_to_grid': payload.enable_snap_to_grid,
            'enable_snap_to_wall': payload.enable_snap_to_wall,
            'auto_save_interval': payload.auto_save_interval,
        }

    if request.method == 'POST':
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON payload'}, status=400)

        decimal_fields = {
            'max_placement_depth_from_wall': ('max_placement_depth_from_wall', Decimal),
            'grid_snap_size': ('grid_snap_size', Decimal),
            'default_object_spacing': ('default_object_spacing', Decimal),
        }
        bool_fields = {
            'allow_object_overlap': 'allow_object_overlap',
            'show_placement_guides': 'show_placement_guides',
            'enable_snap_to_grid': 'enable_snap_to_grid',
            'enable_snap_to_wall': 'enable_snap_to_wall',
        }
        int_fields = {
            'auto_save_interval': 'auto_save_interval',
        }

        updated = False

        for payload_key, (attr, caster) in decimal_fields.items():
            if payload_key in data:
                try:
                    value = caster(str(data[payload_key]))
                except (ValueError, TypeError, InvalidOperation):
                    continue
                if value < 0:
                    value = Decimal('0')
                setattr(settings, attr, value)
                updated = True

        for payload_key, attr in bool_fields.items():
            if payload_key in data:
                setattr(settings, attr, bool(data[payload_key]))
                updated = True

        for payload_key, attr in int_fields.items():
            if payload_key in data:
                try:
                    value = int(data[payload_key])
                except (ValueError, TypeError):
                    continue
                if value < 0:
                    value = 0
                setattr(settings, attr, value)
                updated = True

        if updated:
            settings.save()

        return JsonResponse({'success': True, 'settings': serialize(settings)})

    return JsonResponse(serialize(settings))


@login_required
@require_http_methods(["GET"])
def placed_furniture_list_api(request, kitchen_pk):
    """API endpoint to get all placed furniture in a kitchen"""
    kitchen = get_object_or_404(Kitchen, pk=kitchen_pk, user=request.user)
    
    furniture_list = []
    for placed in kitchen.placed_furniture.select_related('furniture_object').all():
        furniture_list.append({
            'id': placed.id,
            'furniture_object_id': placed.furniture_object.id,
            'furniture_name': placed.furniture_object.name,
            'object_type': placed.furniture_object.object_type,
            'requires_wall': placed.furniture_object.requires_wall,
            'can_place_on_wall': placed.furniture_object.can_place_on_wall,
            'position_x': float(placed.position_x),
            'position_y': float(placed.position_y),
            'position_z': float(placed.position_z),
            'width': float(placed.width),
            'height': float(placed.height),
            'depth': float(placed.depth),
            'rotation_angle': placed.rotation_angle,
            'is_placed_on_wall': placed.is_placed_on_wall,
            'wall_side': placed.wall_side,
            'thumbnail': placed.furniture_object.thumbnail.url if placed.furniture_object.thumbnail else None,
        })
    
    return JsonResponse({'placed_furniture': furniture_list})


@login_required
@require_http_methods(["POST"])
def place_furniture_api(request, kitchen_pk):
    """API endpoint to place furniture in a kitchen"""
    kitchen = get_object_or_404(Kitchen, pk=kitchen_pk, user=request.user)
    
    try:
        data = json.loads(request.body)
        print(f"Place furniture data: {data}")  # Debug logging
        
        furniture_obj = get_object_or_404(FurnitureObject, id=data['furniture_object_id'])
        
        placed = PlacedFurniture.objects.create(
            kitchen=kitchen,
            furniture_object=furniture_obj,
            position_x=Decimal(str(data['position_x'])),
            position_y=Decimal(str(data['position_y'])),
            position_z=Decimal(str(data.get('position_z', 0))),
            width=Decimal(str(data.get('width', furniture_obj.default_width))),
            height=Decimal(str(data.get('height', furniture_obj.default_height))),
            depth=Decimal(str(data.get('depth', furniture_obj.default_depth))),
            rotation_angle=data.get('rotation_angle', 0),
            is_placed_on_wall=data.get('is_placed_on_wall', False),
            wall_side=data.get('wall_side', 'none'),
        )
        
        return JsonResponse({
            'success': True,
            'id': placed.id,
            'message': 'Furniture placed successfully'
        })
    
    except KeyError as e:
        print(f"Missing key in request: {e}")  # Debug logging
        return JsonResponse({
            'success': False,
            'error': f'Missing required field: {str(e)}'
        }, status=400)
    except Exception as e:
        print(f"Error placing furniture: {e}")  # Debug logging
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["PUT", "POST"])
def update_furniture_position_api(request, pk):
    """API endpoint to update furniture position"""
    placed = get_object_or_404(PlacedFurniture, id=pk, kitchen__user=request.user)
    
    try:
        data = json.loads(request.body)
        
        if 'position_x' in data:
            placed.position_x = Decimal(str(data['position_x']))
        if 'position_y' in data:
            placed.position_y = Decimal(str(data['position_y']))
        if 'position_z' in data:
            placed.position_z = Decimal(str(data['position_z']))
        if 'is_placed_on_wall' in data:
            placed.is_placed_on_wall = data['is_placed_on_wall']
        if 'wall_side' in data:
            placed.wall_side = data['wall_side']
        
        placed.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Position updated successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["PUT", "POST"])
def update_furniture_size_api(request, pk):
    """API endpoint to update furniture size"""
    placed = get_object_or_404(PlacedFurniture, id=pk, kitchen__user=request.user)
    
    try:
        data = json.loads(request.body)
        
        if 'width' in data:
            placed.width = Decimal(str(data['width']))
        if 'height' in data:
            placed.height = Decimal(str(data['height']))
        if 'depth' in data:
            placed.depth = Decimal(str(data['depth']))
        
        placed.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Size updated successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["PUT", "POST"])
def rotate_furniture_api(request, pk):
    """API endpoint to rotate furniture"""
    placed = get_object_or_404(PlacedFurniture, id=pk, kitchen__user=request.user)
    
    try:
        data = json.loads(request.body)
        rotation = data.get('rotation_angle', 0)
        
        # Ensure rotation is in valid range (0, 90, 180, 270)
        rotation = rotation % 360
        if rotation not in [0, 90, 180, 270]:
            # Round to nearest 90 degrees
            rotation = round(rotation / 90) * 90
        
        placed.rotation_angle = rotation
        placed.save()
        
        return JsonResponse({
            'success': True,
            'rotation_angle': placed.rotation_angle,
            'message': 'Rotation updated successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["DELETE", "POST"])
def delete_placed_furniture_api(request, pk):
    """API endpoint to delete placed furniture"""
    placed = get_object_or_404(PlacedFurniture, id=pk, kitchen__user=request.user)
    
    try:
        placed.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Furniture deleted successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def duplicate_furniture_api(request, pk):
    """API endpoint to duplicate placed furniture"""
    original = get_object_or_404(PlacedFurniture, id=pk, kitchen__user=request.user)
    
    try:
        data = json.loads(request.body)
        
        # Create duplicate with offset position
        duplicate = PlacedFurniture.objects.create(
            kitchen=original.kitchen,
            furniture_object=original.furniture_object,
            position_x=Decimal(str(data.get('position_x', float(original.position_x) + 0.5))),
            position_y=Decimal(str(data.get('position_y', float(original.position_y) + 0.5))),
            position_z=original.position_z,
            width=original.width,
            height=original.height,
            depth=original.depth,
            rotation_angle=original.rotation_angle,
            is_placed_on_wall=original.is_placed_on_wall,
            wall_side=original.wall_side,
        )
        
        return JsonResponse({
            'success': True,
            'id': duplicate.id,
            'message': 'Furniture duplicated successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
