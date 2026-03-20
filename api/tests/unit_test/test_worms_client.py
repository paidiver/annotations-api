"""Unit tests for CachedWoRMSClient (worms_client)."""

from unittest.mock import MagicMock, patch

import requests
from django.test import SimpleTestCase
from requests.exceptions import HTTPError
from requests.sessions import HTTPAdapter
from rest_framework import status

from api.services.cached_worms_client import CachedWoRMSClient


class CachedWoRMSClientTests(SimpleTestCase):
    """Tests for CachedWoRMSClient using mocked requests.Session."""

    def _mock_session_cm(self, response: MagicMock) -> tuple[MagicMock, MagicMock]:
        """Helper function to create a mocked for requests.

        Args:
            response: The MagicMock response object that the session's get() method should return.

        Returns:
            A tuple containing the mocked context manager and the mocked session.
        """
        session = MagicMock(name="session")
        session.get.return_value = response
        session.post.return_value = response

        cm = MagicMock(name="session_cm")
        cm.__enter__.return_value = session
        cm.__exit__.return_value = None
        return cm, session

    def test_session_creates_session_with_retries(self):
        """Test that _session() creates a requests Session with the expected retry configuration."""
        client = CachedWoRMSClient(base_url="https://worms.example")
        session = client._session()

        self.assertIsInstance(session, requests.Session)
        adapter = session.get_adapter("https://")
        self.assertIsInstance(adapter, HTTPAdapter)
        self.assertIsNotNone(adapter.max_retries)
        self.assertEqual(adapter.max_retries.total, 5)
        self.assertEqual(adapter.max_retries.backoff_factor, 0.5)
        self.assertEqual(adapter.max_retries.status_forcelist, (429, 500, 502, 503, 504))
        self.assertEqual(adapter.max_retries.allowed_methods, ("GET",))

    def test_get_returns_json_for_200(self):
        """Test that _get() returns the JSON-decoded response for a successful 200 response from the WoRMS API."""
        client = CachedWoRMSClient(base_url="https://worms.example")

        response = MagicMock(name="response")
        response.status_code = 200
        response.json.return_value = {"ok": True}
        response.raise_for_status.return_value = None

        cm, session = self._mock_session_cm(response)

        with patch.object(CachedWoRMSClient, "_session", return_value=cm):
            out = client._get("/example")

        self.assertEqual(out, {"ok": True})
        session.get.assert_called_once_with("https://worms.example/example", timeout=20)
        response.raise_for_status.assert_called_once()

    def test_get_returns_none_for_204(self):
        """Test that _get() returns None for a 204 No Content response from the WoRMS API."""
        client = CachedWoRMSClient(base_url="https://worms.example")

        response = MagicMock(name="response")
        response.status_code = status.HTTP_204_NO_CONTENT
        cm, session = self._mock_session_cm(response)

        with patch.object(CachedWoRMSClient, "_session", return_value=cm):
            out = client._get("/example")

        self.assertIsNone(out)
        session.get.assert_called_once()
        response.raise_for_status.assert_not_called()
        response.json.assert_not_called()

    def test_get_raises_for_non_204_http_error(self):
        """Test that _get() raises an HTTPError for a non-204 with an HTTP error status code from the WoRMS API."""
        client = CachedWoRMSClient(base_url="https://worms.example")

        response = MagicMock(name="response")
        response.status_code = 500
        response.raise_for_status.side_effect = HTTPError("boom")

        cm, session = self._mock_session_cm(response)

        with patch.object(CachedWoRMSClient, "_session", return_value=cm), self.assertRaises(HTTPError):
            client._get("/example")

        session.get.assert_called_once()
        response.raise_for_status.assert_called_once()

    def test_descendants_aphia_ids_builds_correct_path(self):
        """Test that descendants_aphia_ids() builds the correct API path and returns the expected result."""
        client = CachedWoRMSClient(base_url="https://worms.example")
        with patch.object(CachedWoRMSClient, "_get", return_value=[10, 20, 30, 40]) as mock_get:
            out = client.descendants_aphia_ids([1, 2])

        self.assertEqual(out, [10, 20, 30, 40])
        mock_get.assert_called_once_with("/taxa/ids_with_descendants/?aphia_ids[]=1&aphia_ids[]=2")

    def test_aphia_ids_by_name_part_builds_correct_path(self):
        """Test that aphia_ids_by_name_part() builds the correct API path and returns the expected result."""
        client = CachedWoRMSClient(base_url="https://worms.example")
        with patch.object(CachedWoRMSClient, "_get", return_value=[10, 20, 30, 40]) as mock_get:
            out = client.aphia_ids_by_name_part("example")

        self.assertEqual(out, [10, 20, 30, 40])
        mock_get.assert_called_once_with("/taxa/ajax_by_name_part/only_ids/example/?combine_vernaculars=false")

    def test_post_returns_response(self):
        """Test that _post() returns None for a 204 No Content response from the WoRMS API."""
        client = CachedWoRMSClient(base_url="https://worms.example")

        response = MagicMock(name="response")
        response.status_code = status.HTTP_204_NO_CONTENT
        cm, session = self._mock_session_cm(response)

        with patch.object(CachedWoRMSClient, "_session", return_value=cm):
            out = client._post("/example", json={"key": "value"})

        self.assertEqual(out, response)
        session.post.assert_called_once_with(
            "https://worms.example/example",
            json={"key": "value"},
            headers={"Authorization": client.authorization_token},
            timeout=20,
        )

    def test_ingest_aphia_id_builds_correct_path(self):
        """Test that ingest_aphia_id() builds the correct API path and returns the expected result."""
        client = CachedWoRMSClient(base_url="https://worms.example")
        return_value = [
            {"AphiaID": 10},
            {"AphiaID": 20},
            {"AphiaID": 30},
            {"AphiaID": 40},
        ]
        with patch.object(CachedWoRMSClient, "_post", return_value=return_value) as mock_post:
            out = client.ingest(1)

        self.assertEqual(out, return_value)
        mock_post.assert_called_once_with("/taxa/ingest/", json={"aphia_id": 1})
