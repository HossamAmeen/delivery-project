"""Standard page-number pagination (DRF_SKILL §40, api-contracts §1.3)."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.settings import api_settings


class StandardPagination(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "page_size"

    def get_page_size(self, request) -> int:
        # Read at request time so settings overrides (tests, env) apply.
        self.page_size = api_settings.PAGE_SIZE or 20
        self.max_page_size = getattr(settings, "API_MAX_PAGE_SIZE", 100)
        return super().get_page_size(request)

    def get_paginated_response(self, data: list[Any]) -> Response:
        # The renderer wraps this dict into the success envelope's ``data``.
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "object",
            "required": ["count", "results"],
            "properties": {
                "count": {"type": "integer", "example": 120},
                "next": {"type": "string", "nullable": True, "format": "uri"},
                "previous": {"type": "string", "nullable": True, "format": "uri"},
                "results": schema,
            },
        }
