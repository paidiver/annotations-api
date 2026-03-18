"""Unit tests for the worms API helper function."""

from unittest.mock import Mock, patch

from django.test import TestCase

from api.serializers.label import _ingest_get_aphia_id_cached_worms


class TestWormsAPI(TestCase):
    """Unit tests for _ingest_get_aphia_id_cached_worms."""

    CACHED_API_BASE = "http://cached/api"

    def setUp(self):
        """Set up the test case by patching settings and requests.post."""
        patcher_settings = patch("api.serializers.label.settings")
        self.mock_settings = patcher_settings.start()
        self.addCleanup(patcher_settings.stop)

        patcher_post = patch("api.serializers.label.requests.post")
        self.mock_post = patcher_post.start()
        self.addCleanup(patcher_post.stop)

        self.mock_settings.CACHED_WORMS_API_BASE_URL = self.CACHED_API_BASE
        self.mock_settings.CACHED_WORMS_API_TOKEN = "test-token"

    def test_returns_cached_if_cached_is_200(self):
        """No errors are returned if aphia_id is validated successfully."""
        cached_response = Mock(status_code=200)
        self.mock_post.return_value = cached_response

        response = _ingest_get_aphia_id_cached_worms("123")

        self.assertEqual(response, cached_response)
        self.mock_post.assert_called_once_with(
            "http://cached/api/taxa/ingest/",
            json={"aphia_id": "123"},
            headers={"Authorization": "Bearer test-token"},
            timeout=20,
        )

    def test_returns_error_if_cached_fails(self):
        """Error is returned for aphia_id if worms cache response is unsuccessful."""
        cached_response = Mock(status_code=404)

        self.mock_post.side_effect = [cached_response]

        response = _ingest_get_aphia_id_cached_worms("789")

        self.assertEqual(self.mock_post.call_count, 1)
        self.mock_post.assert_called_with(
            "http://cached/api/taxa/ingest/",
            json={"aphia_id": "789"},
            headers={"Authorization": "Bearer test-token"},
            timeout=20,
        )
        self.assertEqual(response, cached_response)
