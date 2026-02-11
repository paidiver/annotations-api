"""Serializers for the Annotations API endpoints."""

from django.db import transaction
from rest_framework import serializers

from api.models import Annotation, Annotator
from api.models.annotation import AnnotationLabel
from api.models.annotation_set import AnnotationSet
from api.models.image import Image
from api.models.label import Label
from api.serializers.base import (
    BaseSerializer,
    CreateOnlyRelatedField,
    NestedGetOrCreateMixin,
    ReadOnlyFieldsMixin,
    StrictPrimaryKeyRelatedField,
)

FK_PAIRS = [
    ("annotator", "annotator_id"),
]


class AnnotatorSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for Annotator model."""

    key_field = "name"

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


class AnnotationLabelSerializer(ReadOnlyFieldsMixin, BaseSerializer):
    """Serializer for AnnotationLabel model."""

    annotation_id = serializers.PrimaryKeyRelatedField(
        source="annotation",
        queryset=Annotation.objects.all(),
    )
    label_id = serializers.PrimaryKeyRelatedField(
        source="label",
        queryset=Label.objects.all(),
    )

    annotator_id = StrictPrimaryKeyRelatedField(
        source="annotator",
        queryset=AnnotationLabel._meta.get_field("annotator").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )
    annotator = CreateOnlyRelatedField(
        create_serializer_class=AnnotatorSerializer,
        write_only=True,
        required=False,
    )

    class Meta:
        """Meta class for AnnotationLabelSerializer."""

        model = AnnotationLabel
        fields = ["id", "annotation_id", "label_id", "annotator_id", "annotator", "creation_datetime"]
        validators = []

    def validate(self, attrs: dict) -> dict:
        """Custom validation to ensure no duplicate AnnotationLabel for the same annotation, label, and annotator.

        Args:
            attrs (dict): The attributes to validate.

        Returns:
            dict: The validated attributes.
        """
        errors = {}

        errors = self._validate_pairs(FK_PAIRS, errors)
        if errors:
            raise serializers.ValidationError(errors)
        self._materialize_deferred_related(attrs, FK_PAIRS)

        errors = self._validate_constraints(attrs, errors)

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def _validate_constraints(self, attrs: dict, errors: dict) -> dict:
        """Validate that there are no duplicate AnnotationLabel for the same annotation, label, and annotator.

        Args:
            attrs (dict): The attributes to validate.
            errors (dict): The dictionary to store validation errors.

        Returns:
            dict: The updated errors dictionary.
        """
        annotation = attrs.get("annotation")
        label = attrs.get("label")
        annotator = attrs.get("annotator")

        exists = AnnotationLabel.objects.filter(
            annotation=annotation,
            label=label,
            annotator=annotator,
        ).exists()
        if exists:
            errors["non_field_errors"] = ["AnnotationLabel with this annotation, label and annotator already exists."]
        return errors

    @transaction.atomic
    def create(self, validated_data) -> AnnotationLabel:
        """Override create to handle nested creation of related objects and setting M2M relationships.

        Args:
            validated_data: The validated data from the serializer.

        Returns:
            The created AnnotationLabel instance.
        """
        self._materialize_deferred_related(validated_data, FK_PAIRS)

        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data) -> AnnotationLabel:
        """Override update to handle nested updates of related objects and setting M2M relationships.

        Args:
            instance: The existing AnnotationLabel instance.
            validated_data: The validated data from the serializer.

        Returns:
            The updated AnnotationLabel instance.
        """
        self._materialize_deferred_related(validated_data, FK_PAIRS)

        return super().update(instance, validated_data)
