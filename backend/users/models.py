from django.db import models


class TelegramUser(models.Model):
    """User authenticated from Telegram WebApp."""

    class Roles(models.TextChoices):
        SUPERADMIN = "superadmin", "Superadmin"
        MANAGER = "manager", "Manager"
        USER = "user", "User"

    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, blank=True, default="")
    last_name = models.CharField(max_length=255, blank=True, default="")
    role = models.CharField(
        max_length=32,
        choices=Roles.choices,
        default=Roles.USER,
        db_index=True,
    )
    country = models.CharField(max_length=128, blank=True, default="")
    region = models.CharField(max_length=128, blank=True, default="")
    city = models.CharField(max_length=128, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        parts = [self.first_name, self.last_name]
        name = " ".join(p for p in parts if p).strip() or "-"
        uname = f"@{self.username}" if self.username else ""
        return f"{name} {uname} ({self.telegram_id})".strip()

    @property
    def has_location(self) -> bool:
        return all([self.country.strip(), self.region.strip(), self.city.strip()])

    @property
    def is_authenticated(self) -> bool:
        return True
