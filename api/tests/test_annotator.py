"""Unit tests for annotations endpoints."""

from uuid import UUID

from django.urls import reverse
from rest_framework import status

from api.models.annotation import Annotator
from api.tests.utils.auth_utils import AuthenticatedAPITestCase


class AnnotatorTests(AuthenticatedAPITestCase):
    """Tests for the Annotator model."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        cls.annotator = Annotator.objects.create(name="Test Annotator")
        cls.annotator.save()
        cls.annotator_id = cls.annotator.id
        cls.annotator_detail = reverse("annotator-detail", kwargs={"pk": cls.annotator_id})
        cls.annotator_list = reverse("annotator-list")

    def test_get_annotators(self) -> None:
        """Test retrieving annotators list."""
        url = self.annotator_list
        self.client.force_authenticate(user=None)  # ensure endpoint works for anonymous users
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), {"count", "next", "previous", "results"})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Test Annotator")

    def test_get_annotator_detail_by_id(self) -> None:
        """Test retrieving a specific annotator."""
        url = self.annotator_detail
        self.client.force_authenticate(user=None)  # ensure endpoint works for anonymous users
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(UUID(response.data["id"]), self.annotator_id)
        self.assertEqual(response.data["name"], "Test Annotator")

    def test_post_annotator(self) -> None:
        """Test the POST /annotator/ endpoint."""
        response = self.client.post(self.annotator_list, {"name": "New Test Annotator"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Annotator.objects.count(), 2)
        self.assertEqual(response.data["name"], "New Test Annotator")

    def test_put_annotator(self) -> None:
        """Test the PUT /annotator/{id}/ endpoint."""
        response = self.client.put(self.annotator_detail, {"name": "Updated Test Annotator"}, format="json")
        self.annotator.refresh_from_db()  # Refresh the annotator instance to get the updated values from the database
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.annotator.name)

    def test_readonly_annotator_fields(self) -> None:
        """Test that read-only fields cannot be updated."""
        data = {
            "id": "12345678-1234-5678-1234-567812345678",  # Attempt to change the ID
            "name": "Attempted Update",
        }
        response = self.client.put(self.annotator_detail, data, format="json")
        self.annotator.refresh_from_db()  # Refresh the annotator instance to get the updated values from the database
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(UUID(data["id"]), self.annotator_id)
        self.assertEqual(response.data["id"], str(self.annotator_id))  # The ID should remain unchanged
        self.assertEqual(response.data["name"], self.annotator.name)

    def test_delete_annotator(self) -> None:
        """Test the DELETE /annotator/{id}/ endpoint."""
        response = self.client.delete(self.annotator_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Annotator.objects.count(), 0)

    def test_anonymous_user_cannot_post_annotator(self) -> None:
        """Test that an Annotator can't be created by an anonymous user."""
        self.client.force_authenticate(user=None)
        response = self.client.post(self.annotator_list, {"name": "New Test Annotator"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Annotator.objects.count(), 1)
