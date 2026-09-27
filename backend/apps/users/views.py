from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from common.openapi import ErrorEnvelopeSerializer
from common.throttling import AuthRateThrottle

from .serializers import AccessTokenSerializer, LoginSerializer, MeSerializer, TokenPairSerializer


def _error(description: str) -> OpenApiResponse:
    return OpenApiResponse(ErrorEnvelopeSerializer, description=description)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    authentication_classes: list = []
    throttle_classes = [AuthRateThrottle]

    @extend_schema(
        tags=["auth"],
        summary="Obtain a JWT pair with username + password",
        request=LoginSerializer,
        responses={
            200: TokenPairSerializer,
            400: _error("Missing field: `errors.<field>`."),
            401: _error("`INVALID_CREDENTIALS` (unknown user, wrong password or inactive user)."),
        },
        auth=[],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshView(TokenRefreshView):
    authentication_classes: list = []
    throttle_classes = [AuthRateThrottle]

    @extend_schema(
        tags=["auth"],
        summary="Get a new access token (no refresh rotation)",
        request=TokenRefreshSerializer,
        responses={
            200: AccessTokenSerializer,
            400: _error("Missing field: `errors.refresh`."),
            401: _error("`TOKEN_INVALID`: the refresh token is invalid or expired."),
        },
        auth=[],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MeView(RetrieveAPIView):
    """Minimal identity of the authenticated user."""

    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    @extend_schema(
        tags=["users"],
        summary="Current user",
        responses={
            200: MeSerializer,
            401: _error("`NOT_AUTHENTICATED` or `TOKEN_INVALID`."),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
