from rest_framework import exceptions, serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from common.exceptions import ApplicationError

from .models import User


class InvalidCredentials(ApplicationError):
    status_code = 401
    code = "INVALID_CREDENTIALS"
    message = "Invalid username or password."


class LoginSerializer(TokenObtainPairSerializer):
    """username + password → access/refresh. Never reveals which part was wrong."""

    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except exceptions.AuthenticationFailed as exc:
            # Unknown user, wrong password and inactive user look identical.
            raise InvalidCredentials() from exc


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class AccessTokenSerializer(serializers.Serializer):
    access = serializers.CharField()


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "role", "is_staff"]
        read_only_fields = fields
