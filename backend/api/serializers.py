from django.db.models import Avg
from rest_framework import serializers

from api.constants import DEFAULT_LOCATION
from api.models import Favorite, Place, Review
from users.models import TelegramUser


class TelegramWebAppUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=1)
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    username = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        default=None,
    )

    def validate_username(self, value):
        if value in (None, ""):
            return None
        return value


class LocationSerializer(serializers.Serializer):
    country = serializers.CharField(max_length=128)
    region = serializers.CharField(max_length=128)
    city = serializers.CharField(max_length=128)

    def validate(self, attrs):
        for field in ("country", "region", "city"):
            attrs[field] = attrs[field].strip()
            if not attrs[field]:
                raise serializers.ValidationError({field: "Это поле обязательно."})
        return attrs


class TelegramUserProfileSerializer(serializers.ModelSerializer):
    has_location = serializers.BooleanField(read_only=True)
    default_location = serializers.SerializerMethodField()

    class Meta:
        model = TelegramUser
        fields = (
            "id",
            "telegram_id",
            "username",
            "first_name",
            "last_name",
            "role",
            "country",
            "region",
            "city",
            "has_location",
            "default_location",
            "is_active",
        )

    def get_default_location(self, obj):
        return DEFAULT_LOCATION


class PlaceSerializer(serializers.ModelSerializer):
    created_by = TelegramUserProfileSerializer(read_only=True)
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.IntegerField(read_only=True)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = (
            "id",
            "name",
            "description",
            "country",
            "region",
            "city",
            "address",
            "latitude",
            "longitude",
            "is_active",
            "created_by",
            "average_rating",
            "reviews_count",
            "is_favorite",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_by", "created_at", "updated_at")

    def validate(self, attrs):
        for field in ("name", "country", "region", "city"):
            value = attrs.get(field)
            if value is not None:
                attrs[field] = value.strip()
                if not attrs[field]:
                    raise serializers.ValidationError({field: "Это поле обязательно."})

        latitude = attrs.get("latitude")
        longitude = attrs.get("longitude")
        if latitude is not None and not (-90 <= latitude <= 90):
            raise serializers.ValidationError(
                {"latitude": "Широта должна быть между -90 и 90."}
            )
        if longitude is not None and not (-180 <= longitude <= 180):
            raise serializers.ValidationError(
                {"longitude": "Долгота должна быть между -180 и 180."}
            )
        return attrs

    def get_average_rating(self, obj):
        value = getattr(obj, "average_rating", None)
        if value is None:
            value = obj.reviews.aggregate(value=Avg("rating"))["value"]
        return round(value, 2) if value is not None else None

    def get_is_favorite(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not getattr(user, "is_authenticated", False):
            return False
        favorite_place_ids = self.context.get("favorite_place_ids")
        if favorite_place_ids is not None:
            return obj.id in favorite_place_ids
        return Favorite.objects.filter(user=user, place=obj).exists()


class ReviewSerializer(serializers.ModelSerializer):
    user = TelegramUserProfileSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ("id", "user", "place", "text", "rating", "created_at", "updated_at")
        read_only_fields = ("user", "created_at", "updated_at")

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Оценка должна быть от 1 до 5.")
        return value

    def validate_text(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Текст отзыва обязателен.")
        return value


class FavoriteSerializer(serializers.ModelSerializer):
    user = TelegramUserProfileSerializer(read_only=True)
    place = PlaceSerializer(read_only=True)
    place_id = serializers.PrimaryKeyRelatedField(
        queryset=Place.objects.filter(is_active=True),
        source="place",
        write_only=True,
    )

    class Meta:
        model = Favorite
        fields = ("id", "user", "place", "place_id", "created_at")
        read_only_fields = ("user", "place", "created_at")
