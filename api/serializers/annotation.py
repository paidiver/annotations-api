"""Serializers for the Annotations API endpoints."""

from rest_framework import serializers

from api.models import Annotation, Annotator
from api.models.annotation import AnnotationLabel
from api.models.annotation_set import AnnotationSet
from api.models.image import Image


class AnnotatorSerializer(serializers.ModelSerializer):
    """Serializer for Annotator model."""

    class Meta:
        """Meta class for AnnotatorSerializer."""

        model = Annotator
        fields = ["id", "name"]

        read_only_fields = ["id", "created_at", "updated_at"]


class AnnotationSerializer(serializers.ModelSerializer):
    """Serializer for Annotation model."""

    image_id = serializers.PrimaryKeyRelatedField(
        source="image",
        queryset=Image.objects.all(),
    )
    annotation_set_id = serializers.PrimaryKeyRelatedField(
        source="annotation_set",
        queryset=AnnotationSet.objects.all(),
    )

    class Meta:
        """Meta class for AnnotationSerializer."""

        model = Annotation
        fields = [
            "id",
            "image_id",
            "annotation_platform",
            "shape",
            "coordinates",
            "dimension_pixels",
            "annotation_set_id",
        ]

        read_only_fields = ["id", "created_at", "updated_at"]


class AnnotationLabelSerializer(serializers.ModelSerializer):
    """Serializer for AnnotationLabel model."""

    class Meta:
        """Meta class for AnnotationLabelSerializer."""

        model = AnnotationLabel
        fields = ["id", "annotation_id", "label_id", "annotator_id", "creation_datetime"]

        read_only_fields = ["id", "created_at", "updated_at"]
