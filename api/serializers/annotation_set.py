"""Serializers for the AnnotationSet API endpoints."""

from rest_framework import serializers

from api.models import AnnotationSet


class AnnotationSetSerializer(serializers.ModelSerializer):
    """Serializer for AnnotationSet model."""

    class Meta:
        """Meta class for AnnotationSetSerializer."""

        model = AnnotationSet
        fields = "__all__"
