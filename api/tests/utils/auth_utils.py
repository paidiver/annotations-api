"""Utility classes for handling authentication in tests."""

from django.contrib.auth.models import User
from rest_framework.test import APITestCase


class AuthenticatedAPITestCase(APITestCase):
    """Custom APITestCase that sets up an authenticated user by default.

    Can be overridden in a test by setting client.force_authenticate(user=None)
    if an unauthenticated user is required for a test.
    """

    def setUp(self):
        """Set up API client with an authenticated user by default."""
        super().setUp()
        self.user = User.objects.create_user(username="test", password="pass")
        self.client.force_authenticate(user=self.user)
