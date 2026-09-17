"""WoRMS Cache compatibility across the annotations boundary."""

from unittest.mock import Mock, patch

import requests
from django.urls import reverse
from rest_framework.test import APITestCase

from api.services.cached_worms_client import CachedWoRMSClient


class WormsContractTests(APITestCase):
    """Keep the public collection and error contract stable."""

    @patch.object(CachedWoRMSClient, "_get")
    def test_empty_id_queries_do_not_request_all_taxa(self, get: Mock) -> None:
        """Empty caller selections must not turn into cache browsing."""
        client = CachedWoRMSClient()
        self.assertEqual(client.get_taxa([]), [])
        self.assertEqual(client.descendants_aphia_ids([]), [])
        get.assert_not_called()

    @patch.object(CachedWoRMSClient, "_get")
    def test_name_paths_are_encoded(self, get: Mock) -> None:
        """Reserved characters cannot become query parameters or URL fragments."""
        CachedWoRMSClient().ajax_by_name_part("Cod #1?foo=bar")
        self.assertIn("Cod%20%231%3Ffoo%3Dbar", get.call_args.args[0])

    @patch("api.views.worms_cache.CachedWoRMSClient")
    def test_upstream_http_timeout_remains_a_timeout(self, client: Mock) -> None:
        """An explicit cache 504 must not become empty success or an unrelated error."""
        response = requests.Response()
        response.status_code = 504
        client.return_value.ajax_by_name_part.side_effect = requests.HTTPError(response=response)
        result = self.client.get(reverse("worms-taxa-list"), {"name_part": "Cod"})
        self.assertEqual(result.status_code, 504)
        self.assertEqual(result.data["code"], "upstream_timeout")

    @patch("api.views.worms_cache.CachedWoRMSClient")
    def test_cache_empty_response_keeps_annotations_collection(self, client: Mock) -> None:
        """WoRMS 204 is normalized only at the application boundary."""
        client.return_value.ajax_by_name_part.return_value = None
        result = self.client.get(reverse("worms-taxa-list"), {"name_part": "Cod"})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data, {"count": 0, "next": None, "previous": None, "results": []})
