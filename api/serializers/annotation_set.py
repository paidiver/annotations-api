"""Serializer for the AnnotationSet model."""

from django.db import transaction
from rest_framework import serializers

from api.models import AnnotationSet, AnnotationSetModel, Creator, LabelSet, RelatedMaterial
from api.models.image_set import ImageSet
from api.serializers.fields import (
    ContextSerializer,
    CreatorSerializer,
    LicenseSerializer,
    PISerializer,
    ProjectSerializer,
    RelatedMaterialSerializer,
)

from .base import (
    BaseSerializer,
    CreateAndReadRelatedField,
    CreateAndReadRelatedListField,
    StrictPrimaryKeyRelatedField,
)

FK_PAIRS = [
    ("context", "context_id"),
    ("project", "project_id"),
    ("pi", "pi_id"),
    ("license", "license_id"),
    ("creators", "creators_ids"),
    ("related_materials", "related_material_ids"),
]


class AnnotationSetSerializer(BaseSerializer):
    """Serializer for the AnnotationSet model."""

    context_id = StrictPrimaryKeyRelatedField(
        source="context",
        queryset=AnnotationSet._meta.get_field("context").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    context = CreateAndReadRelatedField(
        create_serializer_class=ContextSerializer,
        required=False,
    )

    project_id = StrictPrimaryKeyRelatedField(
        source="project",
        queryset=AnnotationSet._meta.get_field("project").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )
    project = CreateAndReadRelatedField(
        create_serializer_class=ProjectSerializer,
        required=False,
    )

    pi_id = StrictPrimaryKeyRelatedField(
        source="pi",
        queryset=AnnotationSet._meta.get_field("pi").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    pi = CreateAndReadRelatedField(
        create_serializer_class=PISerializer,
        required=False,
    )

    license_id = StrictPrimaryKeyRelatedField(
        source="license",
        queryset=AnnotationSet._meta.get_field("license").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    license = CreateAndReadRelatedField(
        create_serializer_class=LicenseSerializer,
        required=False,
    )

    creators_ids = StrictPrimaryKeyRelatedField(
        source="creators",
        many=True,
        queryset=Creator.objects.all(),
        required=False,
        write_only=True,
    )

    creators = CreateAndReadRelatedListField(
        create_serializer_class=CreatorSerializer,
        required=False,
    )

    image_set_ids = StrictPrimaryKeyRelatedField(
        source="image_sets",
        many=True,
        queryset=ImageSet.objects.all(),
        required=False,
    )
    label_set_ids = serializers.PrimaryKeyRelatedField(
        source="label_sets", many=True, queryset=LabelSet.objects.all(), required=False
    )
    connected_set_ids = serializers.PrimaryKeyRelatedField(
        source="connected_sets", many=True, queryset=AnnotationSet.objects.all(), required=False
    )
    related_material_ids = serializers.PrimaryKeyRelatedField(
        source="related_materials",
        many=True,
        queryset=RelatedMaterial.objects.all(),
        required=False,
        write_only=True,
    )
    related_materials = CreateAndReadRelatedListField(
        create_serializer_class=RelatedMaterialSerializer,
        required=False,
    )

    class Meta:
        """Serializer for the AnnotationSet model."""

        model = AnnotationSet
        fields = [
            "id",
            "name",
            "handle",
            "copyright",
            "abstract",
            "objective",
            "context_id",
            "context",
            "project_id",
            "project",
            "pi_id",
            "pi",
            "license_id",
            "license",
            "creators_ids",
            "creators",
            "image_set_ids",
            "label_set_ids",
            "connected_set_ids",
            "machine_scope",
            "related_material_ids",
            "quantitative_or_qualitative",
            "quantification_type",
            "biological_metrics",
            "biological_stats",
            "obis_handles",
            "funding",
            "target_environment",
            "target_timescale",
            "related_materials",
        ]

    def validate(self, attrs: dict) -> dict:
        """Perform cross-field validation to enforce constraints that can't be captured by field-level validation alone.

        Args:
            attrs (dict): The dictionary of field values after field-level validation.

        Raise:
            serializers.ValidationError: If any of the cross-field validation rules are violated.

        Return:
            The validated attributes, if all checks pass.
        """
        errors = {}

        # forbid client from adding object + id together
        errors = self._validate_pairs(FK_PAIRS, errors)

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    @transaction.atomic
    def create(self, validated_data: dict) -> AnnotationSet:
        """Override create to handle nested creation of related objects and setting M2M relationships.

        Args:
            validated_data (dict): The validated data from the serializer.

        Returns:
            The created AnnotationSet instance.
        """
        creators_deferred = validated_data.pop("creators", None)
        related_materials_deferred = validated_data.pop("related_materials", None)

        self._materialize_deferred_related(validated_data, FK_PAIRS)

        instance = super().create(validated_data)

        if creators_deferred is not None:
            instance.creators.set(self._materialize_deferred_list(creators_deferred))
        if related_materials_deferred is not None:
            instance.related_materials.set(self._materialize_deferred_list(related_materials_deferred))

        return instance

    @transaction.atomic
    def update(self, instance: AnnotationSet, validated_data: dict) -> AnnotationSet:
        """Override update to handle nested updates of related objects and setting M2M relationships.

        Args:
            instance (AnnotationSet): The existing AnnotationSet instance.
            validated_data (dict): The validated data from the serializer.

        Returns:
            The updated AnnotationSet instance.
        """
        creators_deferred = validated_data.pop("creators", None)
        related_materials_deferred = validated_data.pop("related_materials", None)

        self._materialize_deferred_related(validated_data, FK_PAIRS)

        instance = super().update(instance, validated_data)

        if creators_deferred is not None:
            instance.creators.set(self._materialize_deferred_list(creators_deferred))
        if related_materials_deferred is not None:
            instance.related_materials.set(self._materialize_deferred_list(related_materials_deferred))

        return instance


class AnnotationSetModelSerializer(serializers.ModelSerializer):
    """Serializer for AnnotationSetModel model."""

    annotation_set_id = serializers.PrimaryKeyRelatedField(
        source="annotation_set", queryset=AnnotationSet.objects.all()
    )
    label_set_id = serializers.PrimaryKeyRelatedField(
        source="label_set", queryset=LabelSet.objects.all(), required=False, allow_null=True
    )

    class Meta:
        """Meta class for AnnotationSetModelSerializer."""

        model = AnnotationSetModel
        fields = [
            "id",
            "annotation_set_id",
            "model_id",
            "name",
            "version",
            "task",
            "handle",
            "weights_sha256",
            "description",
            "score_type",
            "confidence_threshold",
            "label_set_id",
            "training_image_set",
            "training_annotation_set",
            "validation_image_set",
            "validation_annotation_set",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        """Ensure the optional label set is linked to the annotation set."""
        attrs = super().validate(attrs)
        annotation_set = attrs.get("annotation_set", getattr(self.instance, "annotation_set", None))
        label_set = attrs.get("label_set", getattr(self.instance, "label_set", None))
        if label_set and annotation_set and not annotation_set.label_sets.filter(pk=label_set.pk).exists():
            raise serializers.ValidationError({"label_set_id": "The label set must be linked to the annotation set."})
        return attrs
