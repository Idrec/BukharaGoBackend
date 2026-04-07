from rest_framework import serializers


class TelegramWebAppUserSerializer(serializers.Serializer):
    """
    Подмножество полей пользователя из Telegram WebApp (initDataUnsafe.user).
    https://core.telegram.org/bots/webapps#webappuser
    """

    id = serializers.IntegerField(min_value=1)
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    username = serializers.CharField(
        required=False, allow_null=True, allow_blank=True, default=None
    )

    def validate_username(self, value):
        if value in (None, ""):
            return None
        return value
