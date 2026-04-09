from rest_framework.permissions import BasePermission, IsAuthenticated

from .constants import ROLE_PERMISSIONS
from .exceptions import LocationRequiredError


class HasTelegramUser(IsAuthenticated):
    message = "Требуется авторизация через Telegram."


class HasRolePermission(BasePermission):
    message = "Недостаточно прав для этого действия."

    def has_permission(self, request, view):
        required_permission = getattr(view, "required_permission", None)
        if not required_permission:
            return True
        user = request.user
        if not getattr(user, "is_authenticated", False):
            return False
        return required_permission in ROLE_PERMISSIONS.get(user.role, set())


class RequireLocation(BasePermission):
    def has_permission(self, request, view):
        if getattr(view, "allow_missing_location", False):
            return True
        user = request.user
        if not getattr(user, "is_authenticated", False):
            return False
        if user.has_location:
            return True
        raise LocationRequiredError()
