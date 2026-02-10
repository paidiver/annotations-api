"""Serializers for the Annotations API endpoints."""

from rest_framework import serializers

from api.models import Annotation, Annotator
from api.models.annotation import AnnotationLabel
from api.models.annotation_set import AnnotationSet
from api.models.image import Image
from api.models.label import Label
from api.serializers.base import ReadOnlyFIeldsMixin


class AnnotatorSerializer(ReadOnlyFIeldsMixin, serializers.ModelSerializer):
    """Serializer for Annotator model."""

    class Meta:
        """Meta class for AnnotatorSerializer."""

        model = Annotator
        fields = ["id", "name"]


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

    annotation_id = serializers.PrimaryKeyRelatedField(
        source="annotation",
        queryset=Annotation.objects.all(),
    )
    label_id = serializers.PrimaryKeyRelatedField(
        source="label",
        queryset=Label.objects.all(),
    )
    annotator_id = serializers.PrimaryKeyRelatedField(
        source="annotator",
        queryset=Annotator.objects.all(),
        allow_null=True,
        required=False,
    )

    def validate(self, attrs):
        """Custom validation to ensure no duplicate AnnotationLabel for the same annotation, label, and annotator.

        Args:
            attrs (dict): The attributes to validate.

        Returns:
            dict: The validated attributes.
        """
        annotation = attrs.get("annotation")
        label = attrs.get("label")
        annotator = attrs.get("annotator")

        if annotation and label and annotator:
            exists = AnnotationLabel.objects.filter(
                annotation=annotation,
                label=label,
                annotator=annotator,
            ).exists()
            if exists:
                raise serializers.ValidationError(
                    {"non_field_errors": ["AnnotationLabel with this annotation, label and annotator already exists."]}
                )

        return attrs

    class Meta:
        """Meta class for AnnotationLabelSerializer."""

        model = AnnotationLabel
        fields = ["id", "annotation_id", "label_id", "annotator_id", "creation_datetime"]

        read_only_fields = ["id", "created_at", "updated_at"]
