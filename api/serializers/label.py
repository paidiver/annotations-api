"""Serializers for the Labels API endpoints."""

from rest_framework import serializers

from api.models import Label


class LabelSerializer(serializers.ModelSerializer):
    """Serializer for Label model."""

    class Meta:
        """Meta class for LabelSerializer."""

        model = Label
        fields = "__all__"

        read_only_fields = ["id", "created_at", "updated_at"]
