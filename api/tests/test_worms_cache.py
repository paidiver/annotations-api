"""Tests for WormsCacheAjaxViewSet."""

from unittest.mock import Mock, patch

import requests
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.views.worms_cache import _get_ajax_by_name_part_results


class WormsCacheAjaxViewSetTests(APITestCase):
    """Integration tests for WormsCacheAjaxViewSet endpoint."""

    def ajax_url(self, name_part: str) -> str:
        """Build URL for the worms_cache ajax_by_name_part action."""
        return reverse("worms_cache-ajax-by-name-part", kwargs={"name_part": name_part})

    @patch("api.views.worms_cache.CachedWoRMSClient")
    def test_ajax_by_name_part_returns_results(self, mocked_client_cls: Mock) -> None:
        """Return WoRMS rows as-is when the cached service responds successfully."""
        mocked_client = mocked_client_cls.return_value
        mocked_client.ajax_by_name_part.return_value = [
            {
                "AphiaID": 1,
                "scientificname": "Lophius piscatorius",
                "rank": "Species",
                "valid_AphiaID": None,
                "modified": None,
                "cached_at": None,
                "parent_AphiaID": 10
            }
        ]

        resp = self.client.get(self.ajax_url("lophi"))
        data = list(resp.data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(data, mocked_client.ajax_by_name_part.return_value)
        mocked_client.ajax_by_name_part.assert_called_once_with("lophi", combine_vernaculars=True)

    @patch("api.views.worms_cache.CachedWoRMSClient")
    def test_ajax_by_name_part_honours_combine_vernaculars_query_param(self, mocked_client_cls: Mock) -> None:
        """Pass combine_vernaculars=false through to the client as a boolean false."""
        mocked_client = mocked_client_cls.return_value
        mocked_client.ajax_by_name_part.return_value = []

        resp = self.client.get(self.ajax_url("lophi"), {"combine_vernaculars": "false"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])
        mocked_client.ajax_by_name_part.assert_called_once_with("lophi", combine_vernaculars=False)


class GetAjaxByNamePartResultsTests(APITestCase):
    """Unit tests for _get_ajax_by_name_part_results helper."""

    @patch("api.views.worms_cache.CachedWoRMSClient")
    def test_get_ajax_by_name_part_results_returns_empty_on_request_exception(self, mocked_client_cls: Mock) -> None:
        """Return an empty list when the cached service raises a request error."""
        mocked_client = mocked_client_cls.return_value
        mocked_client.ajax_by_name_part.side_effect = requests.RequestException()

        results = _get_ajax_by_name_part_results(name_part="lophi")

        self.assertEqual(results, [])

    @patch("api.views.worms_cache.CachedWoRMSClient")
    def test_get_ajax_by_name_part_results_converts_mapping_to_list(self, mocked_client_cls: Mock) -> None:
        """Convert mapping payloads to a list to keep response shape consistent."""
        mocked_client = mocked_client_cls.return_value
        mocked_client.ajax_by_name_part.return_value = {
            "row-1": {"AphiaID": 1, "scientificname": "Name 1"},
            "row-2": {"AphiaID": 2, "scientificname": "Name 2"},
        }

        results = _get_ajax_by_name_part_results(name_part="name")

        self.assertEqual(
            results, [{"AphiaID": 1, "scientificname": "Name 1"}, {"AphiaID": 2, "scientificname": "Name 2"}]
        )
