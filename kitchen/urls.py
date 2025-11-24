from django.urls import path
from . import views

app_name = 'kitchen'

urlpatterns = [
    path('', views.KitchenListView.as_view(), name='kitchen_list'),
    path('create/', views.KitchenCreateView.as_view(), name='kitchen_create'),
    path('<int:pk>/', views.KitchenDetailView.as_view(), name='kitchen_detail'),
    path('<int:pk>/edit/', views.KitchenUpdateView.as_view(), name='kitchen_update'),
    path('<int:pk>/delete/', views.KitchenDeleteView.as_view(), name='kitchen_delete'),
    path('<int:pk>/visualizer/', views.kitchen_visualizer, name='kitchen_visualizer'),
    path('<int:pk>/generate-3d/', views.generate_3d_model, name='generate_3d_model'),
    path('<int:kitchen_pk>/add-object/', views.add_kitchen_object, name='add_kitchen_object'),
    path('object/<int:pk>/delete/', views.delete_kitchen_object, name='delete_kitchen_object'),
    
    # Kitchen Designer URLs
    path('<int:pk>/designer/', views.kitchen_designer, name='kitchen_designer'),
    
    # Designer API endpoints
    path('api/furniture-catalog/', views.furniture_catalog_api, name='furniture_catalog_api'),
    path('api/designer-settings/', views.designer_settings_api, name='designer_settings_api'),
    path('api/<int:kitchen_pk>/placed-furniture/', views.placed_furniture_list_api, name='placed_furniture_list_api'),
    path('api/<int:kitchen_pk>/place-furniture/', views.place_furniture_api, name='place_furniture_api'),
    path('api/placed-furniture/<int:pk>/position/', views.update_furniture_position_api, name='update_furniture_position_api'),
    path('api/placed-furniture/<int:pk>/size/', views.update_furniture_size_api, name='update_furniture_size_api'),
    path('api/placed-furniture/<int:pk>/rotate/', views.rotate_furniture_api, name='rotate_furniture_api'),
    path('api/placed-furniture/<int:pk>/delete/', views.delete_placed_furniture_api, name='delete_placed_furniture_api'),
    path('api/placed-furniture/<int:pk>/duplicate/', views.duplicate_furniture_api, name='duplicate_furniture_api'),
]
