import logging

from django.db import DatabaseError, IntegrityError
from django.db.models import Avg, Count, Prefetch
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler as drf_exception_handler

from api.constants import DEFAULT_LOCATION
from api.exceptions import LocationRequiredError
from api.logging_utils import log_user_action
from api.models import Favorite, Place, Review
from api.permissions import HasRolePermission, HasTelegramUser, RequireLocation
from api.serializers import (
    FavoriteSerializer,
    LocationSerializer,
    PlaceSerializer,
    ReviewSerializer,
    TelegramUserProfileSerializer,
    TelegramWebAppUserSerializer,
)
from api.telegram_auth import validate_telegram_data
from users.models import TelegramUser

from .services.auth_service import upsert_telegram_user

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    request = context.get("request")
    user = getattr(request, "user", None) if request else None

    if response is None:
        if isinstance(exc, IntegrityError):
            response = Response(
                {
                    "status": "error",
                    "code": "integrity_error",
                    "message": "Проверьте уникальность данных перед сохранением.",
                },
                status=status.HTTP_409_CONFLICT,
            )
        elif isinstance(exc, DatabaseError):
            response = Response(
                {
                    "status": "error",
                    "code": "database_error",
                    "message": "Ошибка базы данных.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        else:
            logger.exception("Unhandled API error", exc_info=exc)
            response = Response(
                {
                    "status": "error",
                    "code": "internal_error",
                    "message": "Внутренняя ошибка сервера.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    if isinstance(exc, LocationRequiredError):
        response.data = {
            "status": "error",
            "code": "location_required",
            "message": "Выберите страну, регион и город.",
            "prompt": "Выберите локацию для продолжения.",
            "default_location": DEFAULT_LOCATION,
        }
    elif isinstance(exc, NotAuthenticated):
        response.data = {
            "status": "error",
            "code": "authentication_required",
            "message": "Требуется авторизация через Telegram.",
        }
    elif isinstance(exc, PermissionDenied):
        response.data = {
            "status": "error",
            "code": "permission_denied",
            "message": str(getattr(exc, "detail", "Недостаточно прав.")),
        }
    elif isinstance(exc, ValidationError):
        response.data = {
            "status": "error",
            "code": "validation_error",
            "message": "Проверьте корректность данных запроса.",
            "errors": response.data,
        }
    else:
        response.data = {
            "status": "error",
            "code": response.data.get("code", getattr(exc, "default_code", "api_error")),
            "message": response.data.get("detail", response.data.get("message", "Ошибка API.")),
            **{
                key: value
                for key, value in response.data.items()
                if key not in {"detail", "message"}
            },
        }

    log_user_action(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=f"{request.method} {request.path}" if request else "api_error",
        result=f"error:{response.status_code}",
        details={"code": response.data.get("code")},
    )
    return response


@api_view(["POST"])
def auth_telegram_user(request):
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
            {
                "status": "error",
                "code": "invalid_telegram_token",
                "message": "Неверный токен Telegram.",
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = TelegramWebAppUserSerializer(data=user_payload)
    serializer.is_valid(raise_exception=True)

    try:
        user = upsert_telegram_user(serializer.validated_data)
    except DatabaseError:
        logger.exception("Database error while processing Telegram auth")
        return Response(
            {"status": "error", "message": "database_error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    log_user_action(user=user, action="auth", result="success")
    return Response(
        {
            "status": "ok",
            "user": TelegramUserProfileSerializer(user).data,
            "location_required": not user.has_location,
        },
        status=status.HTTP_200_OK,
    )


class PermissionedViewMixin:
    permission_action_map: dict[str, str] = {}
    allow_missing_location = False

    def get_permissions(self):
        self.required_permission = self.permission_action_map.get(getattr(self, "action", None))
        permission_classes = [HasTelegramUser, HasRolePermission]
        if not self.allow_missing_location:
            permission_classes.append(RequireLocation)
        return [permission() for permission in permission_classes]


class ProfileView(PermissionedViewMixin, APIView):
    allow_missing_location = True
    required_permission = "profile:view"

    def get_permissions(self):
        permission_classes = [HasTelegramUser, HasRolePermission]
        return [permission() for permission in permission_classes]

    def get(self, request):
        self.required_permission = "profile:view"
        serializer = TelegramUserProfileSerializer(request.user)
        log_user_action(user=request.user, action="profile:view", result="success")
        return Response(
            {
                "status": "ok",
                "user": serializer.data,
                "location_required": not request.user.has_location,
            }
        )


class ProfileLocationView(PermissionedViewMixin, APIView):
    allow_missing_location = True
    required_permission = "profile:update_location"

    def get_permissions(self):
        permission_classes = [HasTelegramUser, HasRolePermission]
        return [permission() for permission in permission_classes]

    def patch(self, request):
        self.required_permission = "profile:update_location"
        serializer = LocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            setattr(request.user, field, value)
        request.user.save(update_fields=["country", "region", "city", "updated_at"])

        log_user_action(user=request.user, action="profile:update_location", result="success")
        return Response(
            {
                "status": "ok",
                "message": "Локация сохранена.",
                "user": TelegramUserProfileSerializer(request.user).data,
            }
        )


class PlaceViewSet(PermissionedViewMixin, viewsets.ModelViewSet):
    serializer_class = PlaceSerializer
    permission_action_map = {
        "list": "place:view",
        "retrieve": "place:view",
        "create": "place:create",
        "update": "place:update",
        "partial_update": "place:update",
        "destroy": "place:delete",
    }

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Place.objects.select_related("created_by")
            .prefetch_related(
                Prefetch(
                    "reviews",
                    queryset=Review.objects.select_related("user"),
                )
            )
            .annotate(average_rating=Avg("reviews__rating"), reviews_count=Count("reviews"))
        )

        if self.action in {"list", "retrieve"} or user.role != TelegramUser.Roles.SUPERADMIN:
            queryset = queryset.filter(is_active=True)

        country = self.request.query_params.get("country") or user.country
        region = self.request.query_params.get("region") or user.region
        city = self.request.query_params.get("city") or user.city

        if country:
            queryset = queryset.filter(country__iexact=country)
        if region:
            queryset = queryset.filter(region__iexact=region)
        if city:
            queryset = queryset.filter(city__iexact=city)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        favorite_place_ids = set(
            Favorite.objects.filter(user=request.user, place__in=queryset).values_list("place_id", flat=True)
        )
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={"request": request, "favorite_place_ids": favorite_place_ids},
        )
        message = None
        if not serializer.data:
            message = "Места еще наполняются"
        log_user_action(user=request.user, action="place:list", result="success", details={"count": len(serializer.data)})
        return Response(
            {
                "status": "ok",
                "message": message,
                "results": serializer.data,
            }
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        log_user_action(user=self.request.user, action="place:create", result="success")

    def perform_update(self, serializer):
        serializer.save()
        log_user_action(user=self.request.user, action="place:update", result="success")

    def perform_destroy(self, instance):
        log_user_action(user=self.request.user, action="place:delete", result="success", details={"place_id": instance.id})
        instance.delete()


class ReviewViewSet(
    PermissionedViewMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ReviewSerializer
    permission_action_map = {
        "list": "review:view",
        "create": "review:create",
        "update": "review:update",
        "partial_update": "review:update",
        "destroy": "review:delete",
    }

    def get_queryset(self):
        queryset = Review.objects.select_related("user", "place")
        place_id = self.request.query_params.get("place")
        if place_id:
            queryset = queryset.filter(place_id=place_id)
        return queryset.filter(
            place__is_active=True,
            place__country__iexact=self.request.user.country,
            place__region__iexact=self.request.user.region,
            place__city__iexact=self.request.user.city,
        )

    def perform_create(self, serializer):
        place = serializer.validated_data["place"]
        if not place.is_active:
            raise ValidationError({"place": "Нельзя оставить отзыв для неактивного места."})
        serializer.save(user=self.request.user)
        log_user_action(user=self.request.user, action="review:create", result="success")

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.user_id != self.request.user.id and self.request.user.role == TelegramUser.Roles.USER:
            raise PermissionDenied("Можно изменять только свои отзывы.")
        serializer.save()
        log_user_action(user=self.request.user, action="review:update", result="success")

    def perform_destroy(self, instance):
        if instance.user_id != self.request.user.id and self.request.user.role == TelegramUser.Roles.USER:
            raise PermissionDenied("Можно удалять только свои отзывы.")
        log_user_action(user=self.request.user, action="review:delete", result="success", details={"review_id": instance.id})
        instance.delete()


class FavoriteViewSet(
    PermissionedViewMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = FavoriteSerializer
    permission_action_map = {
        "list": "favorite:view",
        "create": "favorite:create",
        "destroy": "favorite:delete",
    }

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related("user", "place", "place__created_by")

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True, context={"request": request})
        log_user_action(user=request.user, action="favorite:list", result="success", details={"count": len(serializer.data)})
        return Response({"status": "ok", "results": serializer.data})

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        log_user_action(user=self.request.user, action="favorite:create", result="success")

    def perform_destroy(self, instance):
        if instance.user_id != self.request.user.id:
            raise PermissionDenied("Можно удалять только свои избранные места.")
        log_user_action(user=self.request.user, action="favorite:delete", result="success", details={"favorite_id": instance.id})
        instance.delete()
