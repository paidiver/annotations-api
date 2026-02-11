"""Unit tests for the worms API helper function."""

from unittest.mock import Mock, patch

from django.test import TestCase

from api.serializers.label import _test_cached_and_live_worms_api


class TestWormsAPI(TestCase):
    """Unit tests for _test_cached_and_live_worms_api."""

    @patch("api.serializers.label.requests.get")
    @patch("django.conf.settings")
    def test_returns_cached_if_cached_is_200(self, mock_settings, mock_get):
        """If cached API returns 200, live API should not be called.

        Args:
            mock_settings (Mock): The mocked Django settings.
            mock_get (Mock): The mocked requests.get function.
        """
        mock_settings.CACHED_WORMS_API_BASE_URL = "http://cached"
        mock_settings.WORMS_API_BASE_URL = "http://live"

        cached_response = Mock(status_code=200)
        mock_get.return_value = cached_response

        response = _test_cached_and_live_worms_api("123")

        self.assertEqual(response, cached_response)
        mock_get.assert_called_once_with("http://cached/AphiaRecordByAphiaID/123")

    @patch("api.serializers.label.requests.get")
    @patch("django.conf.settings")
    def test_falls_back_to_live_if_cached_not_200(self, mock_settings, mock_get):
        """If cached fails, live API should be called.

        Args:
            mock_settings (Mock): The mocked Django settings.
            mock_get (Mock): The mocked requests.get function.
        """
        mock_settings.CACHED_WORMS_API_BASE_URL = "http://cached"
        mock_settings.WORMS_API_BASE_URL = "http://live"

        cached_response = Mock(status_code=404)
        live_response = Mock(status_code=200)

        mock_get.side_effect = [cached_response, live_response]

        response = _test_cached_and_live_worms_api("456")

        self.assertEqual(response, live_response)
        self.assertEqual(mock_get.call_count, 2)

        mock_get.assert_any_call("http://cached/AphiaRecordByAphiaID/456")
        mock_get.assert_any_call("http://live/AphiaRecordByAphiaID/456")

    @patch("api.serializers.label.requests.get")
    @patch("django.conf.settings")
    def test_returns_live_error_if_both_fail(self, mock_settings, mock_get):
        """If both cached and live fail, return the live response.

        Args:
            mock_settings (Mock): The mocked Django settings.
            mock_get (Mock): The mocked requests.get function.
        """
        mock_settings.CACHED_WORMS_API_BASE_URL = "http://cached"
        mock_settings.WORMS_API_BASE_URL = "http://live"

        cached_response = Mock(status_code=404)
        live_response = Mock(status_code=500)

        mock_get.side_effect = [cached_response, live_response]

        response = _test_cached_and_live_worms_api("789")

        self.assertEqual(response, live_response)
        self.assertEqual(mock_get.call_count, 2)
