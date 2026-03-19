"""Unit tests for the worms API helper function."""

from unittest.mock import Mock, patch

from django.test import TestCase

from api.serializers.label import _ingest_get_aphia_id_cached_worms


class TestWormsAPI(TestCase):
    """Unit tests for _ingest_get_aphia_id_cached_worms."""

    @patch("api.serializers.label.CachedWoRMSClient")
    def test_returns_cached_if_cached_is_200(self, mock_client_class):
        """Return the response from CachedWoRMSClient.ingest when the cache returns 200."""
        cached_response = Mock(status_code=200)
        mock_client = mock_client_class.return_value
        mock_client.ingest.return_value = cached_response

        response = _ingest_get_aphia_id_cached_worms("123")

        self.assertEqual(response, cached_response)
        mock_client_class.assert_called_once_with()
        mock_client.ingest.assert_called_once_with("123")

    @patch("api.serializers.label.CachedWoRMSClient")
    def test_returns_error_if_cached_fails(self, mock_client_class):
        """Return the response from CachedWoRMSClient.ingest when the cache returns an error."""
        cached_response = Mock(status_code=404)
        mock_client = mock_client_class.return_value
        mock_client.ingest.return_value = cached_response

        response = _ingest_get_aphia_id_cached_worms("789")

        self.assertEqual(response, cached_response)
        mock_client_class.assert_called_once_with()
        mock_client.ingest.assert_called_once_with("789")
