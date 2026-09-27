"""Views that raise each error type, for the common/ tests."""

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, generics, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import ApplicationError, BusinessConflictError, BusinessValidationError
from common.responses import success_response
from common.throttling import SensitiveRateThrottle

from .models import Widget


class PublicView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"hello": "world"})


class PrivateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user": request.user.username})


class SensitiveView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [SensitiveRateThrottle]

    def get(self, request):
        return Response({"sensitive": True})


class MessageView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return success_response({"id": 1}, message="Widget created.", status=201)


class EnvelopedView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"success": True, "message": "Custom.", "data": {"x": 1}})


class NoContentView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request):
        return Response(status=204)


class ListDataView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response([1, 2, 3])


class RawErrorView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(["bad"], status=400)


class EchoSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=5)

    def validate(self, attrs):
        if attrs["name"] == "clash":
            raise serializers.ValidationError("Name clashes with another widget.")
        return attrs


class ValidateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EchoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=201)


class TeapotError(exceptions.APIException):
    status_code = 418
    default_detail = "I am a teapot."
    default_code = "teapot"


RAISERS = {
    "teapot": TeapotError(),
    "not-found": Http404("secret-lookup-detail"),
    "django-permission": DjangoPermissionDenied("internal reason"),
    "django-validation": DjangoValidationError("Bad value."),
    "permission": exceptions.PermissionDenied(),
    "auth-failed": exceptions.AuthenticationFailed("internal token detail"),
    "throttled": exceptions.Throttled(wait=42),
    "conflict": BusinessConflictError(code="INVALID_TRANSITION", message="Cannot move."),
    "business-validation": BusinessValidationError(),
    "application": ApplicationError(extra={"field_hint": "x"}),
    "custom-api": exceptions.APIException(),
    "unexpected": RuntimeError("secret internals at /srv/flash/shared/.env"),
}


class RaiseView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, kind):
        raise RAISERS[kind]


class WidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Widget
        fields = ["id", "name"]


class WidgetListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = WidgetSerializer
    queryset = Widget.objects.all()
