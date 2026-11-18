"""Serializer for the LabelSet model."""

from django.db import transaction
from rest_framework import serializers

from api.models import Creator, LabelSet, RelatedMaterial
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
    CreateOnlyRelatedField,
    CreateOnlyRelatedListField,
    StrictPrimaryKeyRelatedField,
)

FK_PAIRS = [
    ("context", "context_id"),
    ("project", "project_id"),
    ("pi", "pi_id"),
    ("license", "license_id"),
    ("creators", "creators_ids"),
    ("related_materials", "related_materials_ids"),
]


class LabelSetSerializer(BaseSerializer):
    """Serializer for the LabelSet model."""

    context_id = StrictPrimaryKeyRelatedField(
        source="context",
        queryset=LabelSet._meta.get_field("context").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    context = CreateOnlyRelatedField(
        create_serializer_class=ContextSerializer,
        write_only=True,
        required=False,
    )

    project_id = StrictPrimaryKeyRelatedField(
        source="project",
        queryset=LabelSet._meta.get_field("project").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    project = CreateOnlyRelatedField(
        create_serializer_class=ProjectSerializer,
        write_only=True,
        required=False,
    )

    pi_id = StrictPrimaryKeyRelatedField(
        source="pi",
        queryset=LabelSet._meta.get_field("pi").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    pi = CreateOnlyRelatedField(
        create_serializer_class=PISerializer,
        write_only=True,
        required=False,
    )

    license_id = StrictPrimaryKeyRelatedField(
        source="license",
        queryset=LabelSet._meta.get_field("license").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    license = CreateOnlyRelatedField(
        create_serializer_class=LicenseSerializer,
        write_only=True,
        required=False,
    )

    creators_ids = StrictPrimaryKeyRelatedField(
        source="creators",
        many=True,
        queryset=Creator.objects.all(),
        required=False,
    )

    creators = CreateOnlyRelatedListField(
        create_serializer_class=CreatorSerializer,
        write_only=True,
        required=False,
        source="_creators_deferred",
    )

    related_materials_ids = StrictPrimaryKeyRelatedField(
        source="related_materials",
        many=True,
        queryset=RelatedMaterial.objects.all(),
        required=False,
    )

    related_materials = CreateOnlyRelatedListField(
        create_serializer_class=RelatedMaterialSerializer,
        write_only=True,
        required=False,
        source="_related_materials_deferred",
    )

    class Meta:
        """Serializer for the LabelSet model."""

        model = LabelSet
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
            "related_materials_ids",
            "related_materials",
            "catalogue",
            "funding",
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

        errors = self._validate_pairs(FK_PAIRS, errors)

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    @transaction.atomic
    def create(self, validated_data: dict) -> LabelSet:
        """Override create to handle nested creation of related objects and setting M2M relationships.

        Args:
            validated_data (dict): The validated data from the serializer.

        Returns:
            The created LabelSet instance.
        """
        creators_deferred = validated_data.pop("_creators_deferred", None)
        related_materials_deferred = validated_data.pop("_related_materials_deferred", None)

        self._materialize_deferred_related(validated_data, FK_PAIRS)

        instance = super().create(validated_data)

        if creators_deferred is not None:
            instance.creators.set(self._materialize_deferred_list(creators_deferred))
        if related_materials_deferred is not None:
            instance.related_materials.set(self._materialize_deferred_list(related_materials_deferred))

        return instance

    @transaction.atomic
    def update(self, instance: LabelSet, validated_data: dict) -> LabelSet:
        """Override update to handle nested updates of related objects and setting M2M relationships.

        Args:
            instance (LabelSet): The existing LabelSet instance.
            validated_data (dict): The validated data from the serializer.

        Returns:
            The updated LabelSet instance.
        """
        creators_deferred = validated_data.pop("_creators_deferred", None)
        related_materials_deferred = validated_data.pop("_related_materials_deferred", None)

        self._materialize_deferred_related(validated_data, FK_PAIRS)

        instance = super().update(instance, validated_data)

        if creators_deferred is not None:
            instance.creators.set(self._materialize_deferred_list(creators_deferred))
        if related_materials_deferred is not None:
            instance.related_materials.set(self._materialize_deferred_list(related_materials_deferred))

        return instance
