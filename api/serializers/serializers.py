"""Serializers for endpoints."""

from rest_framework import serializers

from ..models.fields import Context, Creator


class CreatorSerializer(serializers.ModelSerializer):
    """Serializer for Creator model."""
    class Meta:
        """Meta class for CreatorSerializer."""
        model = Creator
        fields = ["id", "name", "uri", "created_at", "updated_at"]


class ContextSerializer(serializers.ModelSerializer):
    """Serializer for Context model."""
    class Meta:
        """Meta class for ContextSerializer."""
        model = Context
        fields = "__all__"
