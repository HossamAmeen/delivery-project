from django.urls import path

from .views import HealthView, ReadinessView, StatusView

app_name = "health"

urlpatterns = [
    path("status/", StatusView.as_view(), name="status"),
    path("health/", HealthView.as_view(), name="health"),
    path("health/ready/", ReadinessView.as_view(), name="ready"),
]
