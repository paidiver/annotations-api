"""Serializers for the Annotations API endpoints."""

from rest_framework import serializers

from api.models import Annotation, Annotator


class AnnotatorSerializer(serializers.ModelSerializer):
    """Serializer for Annotator model."""

    class Meta:
        """Meta class for AnnotatorSerializer."""

        model = Annotator
        fields = "__all__"

        read_only_fields = ["id", "created_at", "updated_at"]


class AnnotationSerializer(serializers.ModelSerializer):
    """Serializer for Annotation model."""

    class Meta:
        """Meta class for AnnotationSerializer."""

        model = Annotation
        fields = "__all__"

        read_only_fields = ["id", "created_at", "updated_at"]


class AnnotationLabelSerializer(serializers.ModelSerializer):
    """Serializer for AnnotationLabel model."""

    class Meta:
        """Meta class for AnnotationLabelSerializer."""

        model = Annotation.Labels.through
        fields = "__all__"

        read_only_fields = ["id", "created_at", "updated_at"]
