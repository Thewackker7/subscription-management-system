from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    message = "Admin role required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "ADMIN")


class IsAdminOrStaff(BasePermission):
    message = "Admin or Staff role required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in {"ADMIN", "STAFF"})
