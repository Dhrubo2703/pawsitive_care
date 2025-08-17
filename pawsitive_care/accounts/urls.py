from django.urls import path
from .views import (
    RegisterView, CustomLoginView, CustomLogoutView, profile_view,
    admin_dashboard, vet_dashboard, staff_dashboard, client_dashboard,
    AdminOnlyView, VetOnlyView, AdminOrVetView, user_management, promote_clients,
    add_veterinarian
)

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('profile/', profile_view, name='profile'),
    
    # Role-based dashboards
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('vet-dashboard/', vet_dashboard, name='vet_dashboard'),
    path('staff-dashboard/', staff_dashboard, name='staff_dashboard'),
    path('client-dashboard/', client_dashboard, name='client_dashboard'),
    
    # Role-based views (examples)
    path('admin-only/', AdminOnlyView.as_view(), name='admin_only'),
    path('vet-only/', VetOnlyView.as_view(), name='vet_only'),
    path('admin-or-vet/', AdminOrVetView.as_view(), name='admin_or_vet'),
    
    # User management (admin only)
    path('users/', user_management, name='user_management'),
    path('promote-clients/', promote_clients, name='promote_clients'),
    path('veterinarian/add/', add_veterinarian, name='add_veterinarian'),
]
