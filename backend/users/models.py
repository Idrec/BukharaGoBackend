from django.db import models


class TelegramUser(models.Model):
    """Пользователь, пришедший из Telegram WebApp."""

    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, blank=True, default="")
    last_name = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        parts = [self.first_name, self.last_name]
        name = " ".join(p for p in parts if p).strip() or "—"
        uname = f"@{self.username}" if self.username else ""
        return f"{name} {uname} ({self.telegram_id})".strip()
