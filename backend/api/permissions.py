from rest_framework import permissions


class ActionRestriction(permissions.BasePermission):
    """Проверка разрешений на действия и личной инфы."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (
            request.user.is_staff or request.user == view.get_object().author
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user == obj.author:
            return True
        return request.method in permissions.SAFE_METHODS


class IsAuthorOrStaff(permissions.DjangoModelPermissions):
    """Разрешено автору или с правами админа."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user == obj.author:
            return True
        return request.method in permissions.SAFE_METHODS
