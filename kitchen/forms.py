from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Div
from .models import Kitchen, KitchenObject


class KitchenForm(forms.ModelForm):
    class Meta:
        model = Kitchen
        fields = ['name', 'length', 'width', 'height', 'wall_thickness']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'My Kitchen'}),
            'length': forms.NumberInput(attrs={'step': '0.1', 'min': '0.1', 'placeholder': 'e.g., 5.5'}),
            'width': forms.NumberInput(attrs={'step': '0.1', 'min': '0.1', 'placeholder': 'e.g., 4.0'}),
            'height': forms.NumberInput(attrs={'step': '0.1', 'min': '0.1', 'placeholder': 'e.g., 3.0'}),
            'wall_thickness': forms.NumberInput(attrs={'step': '0.1', 'min': '0.1', 'placeholder': 'e.g., 0.2'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('name', css_class='form-control'),
            HTML('<h5 class="mt-4 mb-3">Kitchen Dimensions</h5>'),
            HTML('<p class="text-muted">Note: Length must be greater than or equal to width.</p>'),
            Row(
                Column('length', css_class='form-group col-md-6 mb-3'),
                Column('width', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('height', css_class='form-group col-md-6 mb-3'),
                Column('wall_thickness', css_class='form-group col-md-6 mb-3'),
            ),
            Div(
                Submit('submit', 'Save Kitchen', css_class='btn btn-primary'),
                css_class='mt-3'
            )
        )


class KitchenObjectForm(forms.ModelForm):
    class Meta:
        model = KitchenObject
        fields = ['object_type', 'description', 'wall', 'distance_from_wall_start', 
                  'object_width', 'height_from_ground', 'object_height']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Enter description for other objects'}),
            'distance_from_wall_start': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'placeholder': 'e.g., 1.5'}),
            'object_width': forms.NumberInput(attrs={'step': '0.1', 'min': '0.1', 'placeholder': 'e.g., 0.9'}),
            'height_from_ground': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'placeholder': 'e.g., 0.0'}),
            'object_height': forms.NumberInput(attrs={'step': '0.1', 'min': '0.1', 'placeholder': 'e.g., 2.1'}),
        }
    
    def __init__(self, *args, kitchen=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.kitchen = kitchen
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.attrs = {
            'hx-post': '',
            'hx-target': '#objects-list',
            'hx-swap': 'beforeend',
        }

        binding_attrs = {
            'object_type': {'x-model': 'objectType'},
            'wall': {'x-model': 'wall'},
            'distance_from_wall_start': {'x-model.number': 'distanceFromStart'},
            'object_width': {'x-model.number': 'objectWidth'},
            'height_from_ground': {'x-model.number': 'heightFromGround'},
            'object_height': {'x-model.number': 'objectHeight'},
        }

        for field_name, attrs in binding_attrs.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update(attrs)
        self.helper.layout = Layout(
            Row(
                Column('object_type', css_class='form-group col-md-6 mb-3'),
                Column('description', css_class='form-group col-md-6 mb-3'),
            ),
            HTML('<h6 class="mt-3 mb-2">Wall Placement</h6>'),
            Field('wall', css_class='form-control mb-3'),
            Row(
                Column(Field('distance_from_wall_start', 
                           placeholder='Distance from wall start'),
                       css_class='form-group col-md-6 mb-3'),
                Column(Field('object_width', 
                           placeholder='Object width'),
                       css_class='form-group col-md-6 mb-3'),
            ),
            HTML('<h6 class="mt-3 mb-2">Height Positioning</h6>'),
            Row(
                Column(Field('height_from_ground', 
                           placeholder='Height from ground'),
                       css_class='form-group col-md-6 mb-3'),
                Column(Field('object_height', 
                           placeholder='Object height'),
                       css_class='form-group col-md-6 mb-3'),
            ),
            Div(
                Submit('submit', 'Add Object', css_class='btn btn-success'),
                css_class='mt-3'
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Add kitchen-specific validation if kitchen is provided
        if self.kitchen:
            wall = cleaned_data.get('wall')
            distance = cleaned_data.get('distance_from_wall_start')
            width = cleaned_data.get('object_width')
            
            if wall and distance is not None and width:
                if 'width_wall' in wall:
                    wall_length = self.kitchen.width
                else:
                    wall_length = self.kitchen.length
                
                if distance + width > wall_length:
                    raise forms.ValidationError(
                        f'Object extends beyond wall length ({wall_length})'
                    )
        
        return cleaned_data
