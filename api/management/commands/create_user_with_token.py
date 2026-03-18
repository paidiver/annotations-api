"""Management command to create a new user with an API token."""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    """Django management command to create a new user with an API token."""

    help = "Create a new user. Returns the new user's API token."

    def add_arguments(self, parser) -> None:
        """Add command-line arguments for user options.

        Args:
            parser: The argument parser to which we can add custom arguments.
        """
        parser.add_argument(
            "username", help="Username for the new user."
        )
        parser.add_argument(
            "password", help="Password for the new user."
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        """Create new user based on provided options and return API token.

        Args:
            *args: Positional arguments (not used here).
            **options: Command-line options for seeding counts.
        """
        user = User.objects.create_user(options["username"], email=None, password=options["password"])
        user.save()
        token, created = Token.objects.get_or_create(user=user)

        self.stdout.write(f"User created: {options["username"]}. API token (please store this securely): {token.key}")
