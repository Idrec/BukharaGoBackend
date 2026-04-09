from django.contrib import admin

from .models import Favorite, Place, Review


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "country",
        "region",
        "city",
        "created_by",
        "is_active",
        "created_at",
    )
    search_fields = ("name", "city", "region", "country", "address")
    list_filter = ("is_active", "country", "region", "city")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("place", "user", "rating", "created_at")
    search_fields = ("place__name", "user__username", "user__telegram_id", "text")
    list_filter = ("rating", "created_at")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("place", "user", "created_at")
    search_fields = ("place__name", "user__username", "user__telegram_id")
    readonly_fields = ("created_at",)
