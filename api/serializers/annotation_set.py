"""Serializer for the AnnotationSet model."""

from django.db import transaction
from rest_framework import serializers

from api.models import AnnotationSet, Creator
from api.models.image_set import ImageSet
from api.serializers.fields import (
    ContextSerializer,
    CreatorSerializer,
    LicenseSerializer,
    PISerializer,
    ProjectSerializer,
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
]


class AnnotationSetSerializer(BaseSerializer):
    """Serializer for the AnnotationSet model."""

    context_id = StrictPrimaryKeyRelatedField(
        source="context",
        queryset=AnnotationSet._meta.get_field("context").remote_field.model.objects.all(),
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
        queryset=AnnotationSet._meta.get_field("project").remote_field.model.objects.all(),
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
        queryset=AnnotationSet._meta.get_field("pi").remote_field.model.objects.all(),
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
        queryset=AnnotationSet._meta.get_field("license").remote_field.model.objects.all(),
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

    image_set_ids = StrictPrimaryKeyRelatedField(
        source="image_sets",
        many=True,
        queryset=ImageSet.objects.all(),
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
            "target_environment",
            "target_timescale",
            "curation_protocol",
            "version",
            "image_set_ids",
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
        ]

    def validate(self, attrs) -> dict:
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
    def create(self, validated_data) -> AnnotationSet:
        """Override create to handle nested creation of related objects and setting M2M relationships.

        Args:
            validated_data (dict): The validated data from the serializer.

        Returns:
            The created AnnotationSet instance.
        """
        creators_deferred = validated_data.pop("_creators_deferred", None)

        self._materialize_deferred_related(validated_data, FK_PAIRS)

        instance = super().create(validated_data)

        if creators_deferred is not None:
            instance.creators.set(self._materialize_deferred_list(creators_deferred))

        return instance

    @transaction.atomic
    def update(self, instance, validated_data) -> AnnotationSet:
        """Override update to handle nested updates of related objects and setting M2M relationships.

        Args:
            instance (AnnotationSet): The existing AnnotationSet instance.
            validated_data (dict): The validated data from the serializer.

        Returns:
            The updated AnnotationSet instance.
        """
        creators_deferred = validated_data.pop("_creators_deferred", None)

        self._materialize_deferred_related(validated_data, FK_PAIRS)

        instance = super().update(instance, validated_data)

        if creators_deferred is not None:
            instance.creators.set(self._materialize_deferred_list(creators_deferred))

        return instance
