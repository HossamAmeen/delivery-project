"""URLconf used with @pytest.mark.urls("tests.testapp.urls")."""

from django.urls import include, path

from . import views

urlpatterns = [
    path("t/public/", views.PublicView.as_view()),
    path("t/private/", views.PrivateView.as_view()),
    path("t/sensitive/", views.SensitiveView.as_view()),
    path("t/message/", views.MessageView.as_view()),
    path("t/enveloped/", views.EnvelopedView.as_view()),
    path("t/no-content/", views.NoContentView.as_view()),
    path("t/list/", views.ListDataView.as_view()),
    path("t/raw-error/", views.RawErrorView.as_view()),
    path("t/validate/", views.ValidateView.as_view()),
    path("t/raise/<str:kind>/", views.RaiseView.as_view()),
    path("t/widgets/", views.WidgetListView.as_view()),
    path("", include("config.urls")),
]

handler404 = "common.views.page_not_found"
handler500 = "common.views.server_error"
