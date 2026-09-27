"""Success envelope renderer and pagination (DRF_SKILL §19, §40)."""

import pytest

from common.renderers import EnvelopeJSONRenderer
from common.responses import is_envelope
from tests.testapp.models import Widget

pytestmark = [pytest.mark.django_db, pytest.mark.urls("tests.testapp.urls")]


def test_plain_response_is_wrapped_with_default_message(api_client):
    response = api_client.get("/t/public/")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Operation completed successfully.",
        "data": {"hello": "world"},
    }


def test_success_response_helper_sets_message_and_status(api_client):
    response = api_client.get("/t/message/")

    assert response.status_code == 201
    assert response.json() == {"success": True, "message": "Widget created.", "data": {"id": 1}}


def test_already_enveloped_data_passes_through(api_client):
    response = api_client.get("/t/enveloped/")

    assert response.json() == {"success": True, "message": "Custom.", "data": {"x": 1}}


def test_list_data_is_wrapped(api_client):
    response = api_client.get("/t/list/")

    assert response.json()["data"] == [1, 2, 3]


def test_no_content_has_empty_body(api_client):
    response = api_client.delete("/t/no-content/")

    assert response.status_code == 204
    assert response.content == b""


def test_raw_error_payload_is_wrapped_as_error(api_client):
    response = api_client.get("/t/raw-error/")

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "message": "Request failed.",
        "errors": {"detail": ["bad"]},
    }


def test_renderer_without_response_context_renders_plain_json():
    assert EnvelopeJSONRenderer().render({"a": 1}) == b'{"a":1}'


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"success": True, "message": "m", "data": None}, True),
        ({"success": False, "message": "m", "errors": {}}, True),
        ({"success": True, "data": 1}, False),
        ({"success": "yes", "message": "m", "data": 1}, False),
        ([1], False),
        (None, False),
    ],
)
def test_is_envelope(data, expected):
    assert is_envelope(data) is expected


def test_pagination_shape(api_client, settings):
    Widget.objects.bulk_create(Widget(name=f"w{i}") for i in range(5))
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "PAGE_SIZE": 2}

    response = api_client.get("/t/widgets/")

    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    data = body["data"]
    assert set(data) == {"count", "next", "previous", "results"}
    assert data["count"] == 5
    assert data["previous"] is None
    assert data["next"].endswith("/t/widgets/?page=2")
    assert [item["name"] for item in data["results"]] == ["w0", "w1"]


def test_pagination_page_size_param_is_capped_by_max(api_client, settings):
    Widget.objects.bulk_create(Widget(name=f"w{i}") for i in range(5))
    settings.API_MAX_PAGE_SIZE = 3

    response = api_client.get("/t/widgets/?page_size=50")

    assert len(response.json()["data"]["results"]) == 3


def test_pagination_invalid_page_returns_404(api_client):
    response = api_client.get("/t/widgets/?page=99")

    assert response.status_code == 404
    assert response.json()["errors"]["code"] == "NOT_FOUND"


def test_soft_deleted_rows_are_not_listed(api_client):
    Widget.objects.create(name="keep")
    Widget.objects.create(name="gone").soft_delete()

    response = api_client.get("/t/widgets/")

    assert [item["name"] for item in response.json()["data"]["results"]] == ["keep"]
