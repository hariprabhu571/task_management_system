# taskmanager/permissions.py

from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsManagerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow managers and admin users.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.role == 'admin' or request.user.role == 'manager'
        )


class IsOwnerOrAssignee(permissions.BasePermission):
    """
    Custom permission to only allow task owners or assignees.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if user is the task creator
        if obj.created_by == request.user:
            return True
        
        # Check if user is assigned to the task
        if hasattr(obj, 'assigned_to') and request.user in obj.assigned_to.all():
            return True
        
        return False