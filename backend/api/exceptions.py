from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidTelegramToken(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Неверный токен Telegram."
    default_code = "invalid_telegram_token"


class InactiveTelegramUser(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Пользователь деактивирован."
    default_code = "inactive_user"


class LocationRequiredError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Выберите страну, регион и город."
    default_code = "location_required"


class PlacesPendingError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Места еще наполняются."
    default_code = "places_pending"
