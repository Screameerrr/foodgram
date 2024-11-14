from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Разрешает доступ только автору для изменения или удаления."""

    def has_object_permission(self, request, view, obj):
        # Разрешаем просмотр всем пользователям
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешаем изменение и удаление только автору
        return obj.author == request.user