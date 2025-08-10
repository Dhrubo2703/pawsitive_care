from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

User = get_user_model()

from .models import CustomUser, Veterinarian

@admin.register(Veterinarian)
class VeterinarianAdmin(admin.ModelAdmin):
    list_display = ('user', 'clinic_branch', 'specialization', 'license_number', 'years_of_experience', 'can_handle_emergencies')
    list_filter = ('clinic_branch', 'can_handle_emergencies')
    search_fields = ('user__username', 'user__email', 'specialization', 'license_number')
    raw_id_fields = ('user',)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(role='vet')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Customize the admin site headers
admin.site.site_header = "Pawsitive Care Administration"
admin.site.site_title = "Pawsitive Care Admin"
admin.site.index_title = "Welcome to Pawsitive Care Administration"

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    # Add custom fields to the fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Information', {
            'fields': ('phone', 'address', 'role'),
            'classes': ('wide',),
        }),
    )
    
    # Add fields to the creation form
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('email', 'first_name', 'last_name', 'phone', 'address', 'role'),
            'classes': ('wide',),
        }),
    )
    
    def role_badge(self, obj):
        """Display role as a colored badge"""
        colors = {
            'admin': 'red',
            'vet': 'green',
            'staff': 'blue',
            'client': 'gray'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.role, 'gray'),
            obj.get_role_display()
        )
    role_badge.short_description = 'Role'
    
    # Customize the list display
    list_display = (
        'username', 
        'email', 
        'first_name', 
        'last_name', 
        'role_badge',
        'is_active', 
        'is_staff', 
        'date_joined'
    )
    
    # Add filters to the right sidebar
    list_filter = BaseUserAdmin.list_filter + ('role', 'date_joined')
    
    # Add search functionality
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    
    # Set default ordering
    ordering = ('-date_joined',)
    
