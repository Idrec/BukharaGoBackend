import logging

from django.db import DatabaseError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services.auth_service import upsert_telegram_user
from .serializers import TelegramWebAppUserSerializer
from .telegram_auth import validate_telegram_data

logger = logging.getLogger(__name__)


@api_view(["POST"])
def auth_telegram_user(request):
    """
    Аутентификация пользователя Telegram WebApp.
    Ожидает JSON:
    {
      "init_data": "<tg.initData>",
      "user": { ... initDataUnsafe.user ... }
    }
    """
    init_data = request.data.get("init_data")
    user_payload = request.data.get("user")

    if not init_data or not isinstance(user_payload, dict):
        logger.warning("Missing init_data or user in payload")
        return Response(
            {"status": "error", "message": "invalid_payload"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not validate_telegram_data(init_data):
        logger.warning("Invalid Telegram WebApp init_data signature")
        return Response(
            {"status": "error", "message": "invalid_telegram_data"},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = TelegramWebAppUserSerializer(data=user_payload)
    if not serializer.is_valid():
        logger.warning("Invalid user payload: %s", serializer.errors)
        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = upsert_telegram_user(serializer.validated_data)
    except DatabaseError:
        logger.exception("Database error while processing Telegram auth")
        return Response(
            {"status": "error", "message": "database_error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception:
        logger.exception("Unexpected error while processing Telegram auth")
        return Response(
            {"status": "error", "message": "internal_error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {"status": "ok", "user_id": user.id, "is_active": user.is_active},
        status=status.HTTP_200_OK,
    )
