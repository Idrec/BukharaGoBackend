from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from users.models import TelegramUser

from .exceptions import InvalidTelegramToken
from .telegram_auth import extract_telegram_user_id, validate_telegram_data


class TelegramUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.telegram_user = None
        request.telegram_auth_failed = False

        if not request.path.startswith("/api/") or request.path == "/api/auth/":
            return None

        init_data = request.headers.get("X-Telegram-Init-Data")
        auth_header = request.headers.get("Authorization", "")
        if not init_data and auth_header.startswith("Telegram "):
            init_data = auth_header.split(" ", 1)[1].strip()

        if not init_data:
            return None

        if not validate_telegram_data(init_data):
            request.telegram_auth_failed = True
            return JsonResponse(
                {
                    "status": "error",
                    "code": InvalidTelegramToken.default_code,
                    "message": str(InvalidTelegramToken.default_detail),
                },
                status=InvalidTelegramToken.status_code,
            )

        telegram_id = extract_telegram_user_id(init_data)
        if telegram_id is None:
            request.telegram_auth_failed = True
            return JsonResponse(
                {
                    "status": "error",
                    "code": InvalidTelegramToken.default_code,
                    "message": str(InvalidTelegramToken.default_detail),
                },
                status=InvalidTelegramToken.status_code,
            )

        request.telegram_user = TelegramUser.objects.filter(telegram_id=telegram_id).first()
        return None
