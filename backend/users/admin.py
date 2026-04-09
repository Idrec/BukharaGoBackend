from django.contrib import admin

from .models import TelegramUser


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = (
        "telegram_id",
        "username",
        "first_name",
        "last_name",
        "role",
        "country",
        "region",
        "city",
        "is_active",
        "created_at",
    )
    search_fields = ("telegram_id", "username", "first_name", "last_name")
    list_filter = ("role", "is_active", "country", "region", "city", "created_at")
    readonly_fields = ("created_at", "updated_at")
