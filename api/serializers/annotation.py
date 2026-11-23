"""Serializers for the Annotations API endpoints."""

from rest_framework import serializers

from api.models import Annotation, Creator
from api.models.annotation_set import AnnotationSet, AnnotationSetModel
from api.models.base import AliasedShapesEnumField, ShapeEnum, enum_choices
from api.models.image import Image
from api.models.label import Label


def _model_score_error(model: AnnotationSetModel | None, confidence: float | None, kind: str) -> str | None:
    """Return a relationship error for a model score, if any."""
    if confidence is None:
        return None
    if model is None:
        return f"A {kind} model is required when confidence is provided."
    if not model.score_type:
        return f"The {kind} model must define its score type."
    return None


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
    label_id = serializers.PrimaryKeyRelatedField(source="label", queryset=Label.objects.all())
    creator_id = serializers.PrimaryKeyRelatedField(
        source="creator", queryset=Creator.objects.all(), required=False, allow_null=True
    )
    human_reviewer_id = serializers.PrimaryKeyRelatedField(
        source="human_reviewer", queryset=Creator.objects.all(), required=False, allow_null=True
    )
    detection_model_id = serializers.PrimaryKeyRelatedField(
        source="detection_model", queryset=AnnotationSetModel.objects.all(), required=False, allow_null=True
    )
    classification_model_id = serializers.PrimaryKeyRelatedField(
        source="classification_model", queryset=AnnotationSetModel.objects.all(), required=False, allow_null=True
    )
    shape = serializers.CharField()  # Accept any string, validate manually below

    class Meta:
        """Meta class for AnnotationSerializer."""

        model = Annotation
        fields = [
            "id",
            "image_id",
            "annotation_set_id",
            "label_id",
            "creator_id",
            "annotation_platform",
            "human_or_machine",
            "creation_datetime",
            "shape",
            "coordinates",
            "dimension_pixels",
            "human_reviewer_id",
            "machine_training_validation",
            "additional_info",
            "detection_model_id",
            "classification_model_id",
            "detection_confidence",
            "classification_confidence",
            "mask",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_shape(self, value: str) -> str:
        """Manual validation of shape to allow for value mappings."""
        normalised = AliasedShapesEnumField().normaliseAnnotationShapeValue(value)
        valid_values = [v for v, _ in enum_choices(ShapeEnum)]
        if normalised not in valid_values:
            raise serializers.ValidationError(f'"{value}" is not a valid shape.')
        return normalised

    def validate(self, attrs: dict) -> dict:
        """Validate label, model, and confidence relationships."""
        attrs = super().validate(attrs)
        instance = self.instance
        annotation_set = attrs.get("annotation_set", getattr(instance, "annotation_set", None))
        label = attrs.get("label", getattr(instance, "label", None))
        detection_model = attrs.get("detection_model", getattr(instance, "detection_model", None))
        classification_model = attrs.get("classification_model", getattr(instance, "classification_model", None))
        detection_confidence = attrs.get("detection_confidence", getattr(instance, "detection_confidence", None))
        classification_confidence = attrs.get(
            "classification_confidence", getattr(instance, "classification_confidence", None)
        )
        errors = {}
        if annotation_set and label and not annotation_set.label_sets.filter(pk=label.label_set_id).exists():
            errors["label_id"] = "The label must belong to a label set linked to the annotation set."
        for field_name, model in (
            ("detection_model_id", detection_model),
            ("classification_model_id", classification_model),
        ):
            if model and annotation_set and model.annotation_set_id != annotation_set.pk:
                errors[field_name] = "The model must be registered on the same annotation set."
        detection_error = _model_score_error(detection_model, detection_confidence, "detection")
        classification_error = _model_score_error(classification_model, classification_confidence, "classification")
        if detection_error:
            errors["detection_model_id"] = detection_error
        if classification_error:
            errors["classification_model_id"] = classification_error
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file upload, for uploading annotations data using XLSX file."""

    file = serializers.FileField(help_text="Select the .xlsx template file")
