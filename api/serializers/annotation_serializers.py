"""Serializers for annotations related endpoints."""

from rest_framework import serializers

from ..models.annotation import Annotator


class AnnotatorSerializer(serializers.ModelSerializer):
    """Serializer for Annotator model."""
    class Meta:
        """Meta class for AnnotatorSerializer."""
        model = Annotator
        fields = ["id", "name", "created_at", "updated_at"]

        # Set read-only fields
        read_only_fields = ["id", "created_at", "updated_at"]
