"""WoRMS API client for fetching taxonomic data from the World Register of Marine Species (WoRMS)."""

from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from rest_framework import status
from urllib3.util.retry import Retry

from config import settings


@dataclass(frozen=True)
class CachedWoRMSClient:
    """Client for interacting with the Cached WoRMS API."""

    base_url: str = settings.CACHED_WORMS_API_BASE_URL

    authorization_token: str = f"Bearer {settings.CACHED_WORMS_API_TOKEN}"

    def _session(self) -> requests.Session:
        """Create a requests Session with retry logic for transient errors.

        Returns:
            A configured requests Session object with retry logic.
        """
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def _get(self, path: str) -> dict | list[dict] | None:
        """Helper method to perform a GET request to the WoRMS API.

        Args:
            path: The API endpoint path to append to the base URL.

        Returns:
            The JSON response from the API as a dictionary or list of dictionaries, or None if no content.
        """
        url = f"{self.base_url}{path}"
        with self._session() as session:
            response = session.get(url, timeout=20)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return None
            response.raise_for_status()
            return response.json()

    def _post(self, path: str, json: dict) -> requests.Response:
        """Helper method to perform a POST request to the WoRMS API.

        Args:
            path: The API endpoint path to append to the base URL.
            json: The JSON payload to send in the POST request.

        Returns:
            The response from the API as a requests.Response object.
        """
        url = f"{self.base_url}{path}"
        with self._session() as session:
            response = session.post(url, json=json, headers={"Authorization": self.authorization_token}, timeout=20)
            return response

    def ingest(self, aphia_id: int) -> requests.Response:
        """Ingest or get an AphiaID into the cache and return the result.

        Args:
            aphia_id: The AphiaID for which to trigger the ingest/get operation.

        Returns:
            A requests.Response object representing the result of the ingest operation.
        """
        return self._post("/taxa/ingest/", json={"aphia_id": aphia_id})

    def descendants_aphia_ids(self, aphia_ids: list[int]) -> list[int] | None:
        """Fetch the descendant AphiaIDs for a given list of AphiaIDs.

        Args:
            aphia_ids: A list of AphiaIDs for which to fetch the descendant AphiaIDs.

        Returns:
            A list of descendant AphiaIDs for the given list of AphiaIDs, or None if not found.
        """
        aphia_ids = [str(aphia_id) for aphia_id in aphia_ids]
        return self._get(f"/taxa/ids_with_descendants/?aphia_ids[]={"&aphia_ids[]=".join(aphia_ids)}")

    def aphia_ids_by_name_part(self, name_part: str, combine_vernaculars: bool = False) -> list[dict] | None:
        """Fetch the AphiaIDs for a given name part.

        Args:
            name_part: The partial name to search for.
            combine_vernaculars: Whether to combine vernacular names in the search.

        Returns:
            A list of dictionaries representing the AphiaIDs, or None if not found.
        """
        return self._get(
            f"/taxa/ajax_by_name_part/only_ids/{name_part}/?combine_vernaculars={str(combine_vernaculars).lower()}"
        )
