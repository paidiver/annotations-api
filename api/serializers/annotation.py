"""Serializers for the Annotations API endpoints."""

from rest_framework import serializers

from api.models import Annotation, Annotator
from api.models.annotation import AnnotationLabel
from api.serializers.base import ReadOnlyFIeldsMixin


class AnnotatorSerializer(ReadOnlyFIeldsMixin, serializers.ModelSerializer):
    """Serializer for Annotator model."""

    class Meta:
        """Meta class for AnnotatorSerializer."""

        model = Annotator
        fields = ["name", "id"]


class AnnotationSerializer(serializers.ModelSerializer):
    """Serializer for Annotation model."""

    class Meta:
        """Meta class for AnnotationSerializer."""

        model = Annotation
        fields = ["image_id", "annotation_platform", "shape", "coordinates", "dimension_pixels", "annotation_set_id"]

        read_only_fields = ["id", "created_at", "updated_at"]


class AnnotationLabelSerializer(serializers.ModelSerializer):
    """Serializer for AnnotationLabel model."""

    class Meta:
        """Meta class for AnnotationLabelSerializer."""

        model = AnnotationLabel
        fields = ["annotation_id", "label_id", "annotator_id", "creation_datetime"]

        read_only_fields = ["id", "created_at", "updated_at"]
