from django.urls import path

from .views import LoginView, MeView, RefreshView

auth_urlpatterns = [
    path("token/", LoginView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", RefreshView.as_view(), name="token_refresh"),
]

users_urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
]
