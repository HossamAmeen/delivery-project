"""Response shapes for the OpenAPI schema (``data`` part of the envelope)."""

from rest_framework import serializers

# Named in SPECTACULAR_SETTINGS["ENUM_NAME_OVERRIDES"] (one schema enum each).
CHECK_RESULT_CHOICES = ["ok", "error"]
OPTIONAL_CHECK_RESULT_CHOICES = ["ok", "error", "skipped"]


class StatusSerializer(serializers.Serializer):
    status = serializers.CharField(help_text='Always "ok".')


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField(help_text='Always "healthy".')


class ReadinessChecksSerializer(serializers.Serializer):
    database = serializers.ChoiceField(choices=CHECK_RESULT_CHOICES)
    cache = serializers.ChoiceField(choices=CHECK_RESULT_CHOICES)
    celery = serializers.ChoiceField(choices=OPTIONAL_CHECK_RESULT_CHOICES)


class ReadinessSerializer(serializers.Serializer):
    status = serializers.CharField(help_text='Always "ready".')
    checks = ReadinessChecksSerializer()
