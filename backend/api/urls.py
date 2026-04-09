from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FavoriteViewSet,
    PlaceViewSet,
    ProfileLocationView,
    ProfileView,
    ReviewViewSet,
    auth_telegram_user,
)

router = DefaultRouter()
router.register("places", PlaceViewSet, basename="place")
router.register("reviews", ReviewViewSet, basename="review")
router.register("favorites", FavoriteViewSet, basename="favorite")

urlpatterns = [
    path("auth/", auth_telegram_user, name="api-auth"),
    path("profile/", ProfileView.as_view(), name="api-profile"),
    path("profile/location/", ProfileLocationView.as_view(), name="api-profile-location"),
    path("", include(router.urls)),
]
