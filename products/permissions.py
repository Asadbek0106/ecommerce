from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners to edit or delete their objects.
    The owner field is taken from ``view.owner_field`` (default: ``user``).
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner (or staff).
        owner = getattr(obj, getattr(view, 'owner_field', 'user'), None)
        return owner == request.user or request.user.is_staff


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow staff members to edit or delete products
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
