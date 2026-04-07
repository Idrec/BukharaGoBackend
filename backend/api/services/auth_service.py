import logging
from typing import Any

from users.models import TelegramUser

logger = logging.getLogger(__name__)


def upsert_telegram_user(validated_data: dict[str, Any]) -> TelegramUser:
    """Create or update Telegram user by telegram_id."""
    telegram_id = validated_data["id"]

    user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            "username": validated_data.get("username"),
            "first_name": validated_data.get("first_name") or "",
            "last_name": validated_data.get("last_name") or "",
        },
    )

    if not created:
        user.username = validated_data.get("username")
        user.first_name = validated_data.get("first_name") or ""
        user.last_name = validated_data.get("last_name") or ""
        user.save(update_fields=["username", "first_name", "last_name"])

    return user
