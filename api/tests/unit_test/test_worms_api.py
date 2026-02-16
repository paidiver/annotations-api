"""Unit tests for the worms API helper function."""

from unittest.mock import Mock, call, patch

from django.test import TestCase

from api.serializers.label import _test_cached_and_live_worms_api


class TestWormsAPI(TestCase):
    """Unit tests for _test_cached_and_live_worms_api."""

    CACHED_API_BASE = "http://cached"
    LIVE_API_BASE = "http://live"

    def setUp(self):
        """Set up the test case by patching settings and requests.get."""
        patcher_settings = patch("api.serializers.label.settings")
        self.mock_settings = patcher_settings.start()
        self.addCleanup(patcher_settings.stop)

        patcher_get = patch("api.serializers.label.requests.get")
        self.mock_get = patcher_get.start()
        self.addCleanup(patcher_get.stop)

        self.mock_settings.CACHED_WORMS_API_BASE_URL = self.CACHED_API_BASE
        self.mock_settings.WORMS_API_BASE_URL = self.LIVE_API_BASE

    def test_returns_cached_if_cached_is_200(self):
        """If cached API returns 200, live API should not be called."""
        cached_response = Mock(status_code=200)
        self.mock_get.return_value = cached_response

        response = _test_cached_and_live_worms_api("123")

        self.assertEqual(response, cached_response)
        self.mock_get.assert_called_once_with("http://cached/AphiaRecordByAphiaID/123")

    def test_falls_back_to_live_if_cached_not_200(self):
        """If cached fails, live API should be called."""
        cached_response = Mock(status_code=404)
        live_response = Mock(status_code=200)

        self.mock_get.side_effect = [cached_response, live_response]

        response = _test_cached_and_live_worms_api("456")

        self.assertEqual(response, live_response)
        self.assertEqual(self.mock_get.call_count, 2)

        expected_calls = ["http://cached/AphiaRecordByAphiaID/456", "http://live/AphiaRecordByAphiaID/456"]
        self.mock_get.assert_has_calls([call(url) for url in expected_calls])

    def test_returns_live_error_if_both_fail(self):
        """If both cached and live fail, return the live response."""
        cached_response = Mock(status_code=404)
        live_response = Mock(status_code=500)

        self.mock_get.side_effect = [cached_response, live_response]

        response = _test_cached_and_live_worms_api("789")

        self.assertEqual(response, live_response)
        self.assertEqual(self.mock_get.call_count, 2)
