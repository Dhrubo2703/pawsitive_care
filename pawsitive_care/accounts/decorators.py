from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def get_user_dashboard_redirect(user):
    """Get the appropriate dashboard redirect URL based on user role"""
    if user.role == 'admin':
        return 'accounts:admin_dashboard'
    elif user.role == 'vet':
        return 'accounts:vet_dashboard'
    elif user.role == 'staff':
        return 'accounts:staff_dashboard'
    else:  # client or default
        return 'accounts:client_dashboard'


def role_required(required_roles):
    """
    Decorator factory that creates decorators to check if user has required role(s)
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'role'):
                messages.error(request, 'Access denied. User role not found.')
                return redirect('accounts:login')
            
            if isinstance(required_roles, str):
                roles = [required_roles]
            else:
                roles = required_roles
            
            if request.user.role not in roles:
                messages.error(request, 'Access denied. Insufficient permissions.')
                # Redirect to user's appropriate dashboard instead of always client_dashboard
                return redirect(get_user_dashboard_redirect(request.user))
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """Decorator to require admin role"""
    return role_required('admin')(view_func)


def vet_required(view_func):
    """Decorator to require vet role"""
    return role_required('vet')(view_func)


def staff_required(view_func):
    """Decorator to require staff role"""
    return role_required('staff')(view_func)


def client_required(view_func):
    """Decorator to require client role"""
    return role_required('client')(view_func)


def vet_required(view_func):
    """Decorator to require veterinarian role"""
    return role_required('vet')(view_func)


def staff_required(view_func):
    """Decorator to require staff role"""
    return role_required('staff')(view_func)


def admin_or_vet_required(view_func):
    """Decorator to require admin or veterinarian role"""
    return role_required(['admin', 'vet'])(view_func)


def admin_or_staff_required(view_func):
    """Decorator to require admin or staff role"""
    return role_required(['admin', 'staff'])(view_func)


# Class-based view mixins
class RoleRequiredMixin(AccessMixin):
    """Mixin for class-based views to check user roles"""
    required_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not hasattr(request.user, 'role'):
            messages.error(request, 'Access denied. User role not found.')
            return redirect('accounts:login')
        
        if isinstance(self.required_roles, str):
            roles = [self.required_roles]
        else:
            roles = self.required_roles
        
        if request.user.role not in roles:
            messages.error(request, 'Access denied. Insufficient permissions.')
            # Redirect to user's appropriate dashboard instead of always client_dashboard
            return redirect(get_user_dashboard_redirect(request.user))
        
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin to require admin role"""
    required_roles = ['admin']


class VetRequiredMixin(RoleRequiredMixin):
    """Mixin to require veterinarian role"""
    required_roles = ['vet']


class StaffRequiredMixin(RoleRequiredMixin):
    """Mixin to require staff role"""
    required_roles = ['staff']


class AdminOrVetRequiredMixin(RoleRequiredMixin):
    """Mixin to require admin or veterinarian role"""
    required_roles = ['admin', 'vet']


class AdminOrStaffRequiredMixin(RoleRequiredMixin):
    """Mixin to require admin or staff role"""
    required_roles = ['admin', 'staff']
