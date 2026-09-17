"""Error and schema contracts without external services."""

from http import HTTPStatus
from unittest.mock import patch

import requests
from django.test import SimpleTestCase
from django.urls import reverse
from drf_spectacular.generators import SchemaGenerator
from rest_framework.test import APIClient


class ResponseContractTests(SimpleTestCase):
    """Public responses remain distinguishable across empty results and failures."""

    def test_upstream_failure_is_not_an_empty_collection(self) -> None:
        """Taxonomy outages and timeouts return errors, while no matches is 200."""
        client = APIClient()
        with patch("api.views.worms_cache.CachedWoRMSClient") as mock:
            lookup = mock.return_value.ajax_by_name_part
            for exception, status_code in (
                (requests.ConnectionError("private-host"), HTTPStatus.BAD_GATEWAY),
                (requests.Timeout("private-host"), HTTPStatus.GATEWAY_TIMEOUT),
            ):
                lookup.side_effect = exception
                response = client.get(reverse("worms-taxa-list"), {"name_part": "cod"})
                self.assertEqual(response.status_code, status_code)
                self.assertEqual(response["Content-Type"], "application/problem+json")
                self.assertNotIn("private-host", response.content.decode())
                self.assertNotIn("results", response.data)
            lookup.side_effect = None
            lookup.return_value = None
            response = client.get(reverse("worms-taxa-list"), {"name_part": "cod"})
            self.assertEqual(response.data, {"count": 0, "next": None, "previous": None, "results": []})

    def test_validation_and_routing_errors_use_problem_details(self) -> None:
        """Both DRF and Django routing errors have the same media type."""
        client = APIClient()
        response = client.get(reverse("worms-taxa-list"), HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(response["Content-Type"], "application/problem+json")
        self.assertEqual(response.json()["code"], "invalid_parameters")
        self.assertEqual(response.data["errors"][0]["field"], "name_part")
        response = client.get("/api/does-not-exist/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(response["Content-Type"], "application/problem+json")
        self.assertEqual(response.json()["code"], "not_found")

    def test_documented_collections_are_not_double_wrapped(self) -> None:
        """Generated search and taxonomy schemas document arrays under results."""
        schema = SchemaGenerator().get_schema(request=None, public=True)
        for path in ("/api/annotations/search/", "/api/annotations/search/grouped/", "/api/taxonomy/worms/taxa/"):
            responses = schema["paths"][path]["get"]["responses"]
            ref = responses["200"]["content"]["application/json"]["schema"]["$ref"].split("/")[-1]
            self.assertEqual(schema["components"]["schemas"][ref]["properties"]["results"]["type"], "array")
            self.assertEqual(set(responses["400"]["content"]), {"application/problem+json"})
