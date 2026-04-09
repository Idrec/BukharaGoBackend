from rest_framework.authentication import BaseAuthentication

from .exceptions import InactiveTelegramUser, InvalidTelegramToken


class TelegramUserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if not request.path.startswith("/api/") or request.path == "/api/auth/":
            return None

        if getattr(request, "telegram_auth_failed", False):
            raise InvalidTelegramToken()

        user = getattr(request, "telegram_user", None)
        if user is None:
            return None
        if not user.is_active:
            raise InactiveTelegramUser()
        return (user, None)
