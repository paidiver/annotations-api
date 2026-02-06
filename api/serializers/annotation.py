"""Serializers for the Annotation API endpoints."""

from rest_framework import serializers

from api.models import Annotation, Annotator


class AnnotatorSerializer(serializers.ModelSerializer):
    """Serializer for Annotator model."""

    class Meta:
        """Meta class for AnnotatorSerializer."""

        model = Annotator
        fields = "__all__"


class AnnotationSerializer(serializers.ModelSerializer):
    """Serializer for Annotation model."""

    class Meta:
        """Meta class for AnnotationSerializer."""

        model = Annotation
        fields = "__all__"
