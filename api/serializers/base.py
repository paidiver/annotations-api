"""Base serializers for the API."""

from attr import dataclass
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class BaseSerializer(serializers.ModelSerializer):
    """Base serializer with common validation logic for all serializers."""

    def _validate_pairs(self, pairs, errors):
        """Helper function to validate each pair of (object_field, id_field), the client has not provided both fields.

        Args:
            pairs: A list of tuples, where each tuple contains the names of the object field and the corresponding id
        field to check.
            errors: The dictionary of accumulated validation errors to which any new errors will be added.

        Return:
            The updated errors dictionary with any new errors added.
        """
        for obj_field, id_field in pairs:
            if obj_field in self.initial_data and id_field in self.initial_data:
                msg = f"Use either '{obj_field}' (object) OR '{id_field}' (id), not both."
                errors[obj_field] = msg
        return errors

    def _validate_geom_fields(self, geom_fields, errors):
        """Helper function to validate that has not provided any of the geom fields, which are computed server-side.

        Args:
            geom_fields: A list of geom field names that should not be provided by the client.
            errors: The dictionary of accumulated validation errors to which any new errors will be added.

        Return:
            The updated errors dictionary with any new errors added.
        """
        for field in geom_fields:
            if field in self.initial_data:
                errors[field] = "This field is computed server-side and must not be provided."
        return errors

    def _materialize_deferred_related(self, validated_data, fk_pairs):
        """Convert deferred related payloads (from CreateOnlyRelatedField) into saved model instances.

        Mutates validated_data in-place.

        Args:
            validated_data (dict): The dictionary of validated data from the serializer,
        which may contain deferred related payloads.
            fk_pairs: A list of tuples, where each tuple contains the names of the object field and the corresponding id
        field to check for deferred payloads.
        """
        for obj_field, _ in fk_pairs:
            val = validated_data.get(obj_field)
            if isinstance(val, DeferredCreate):
                validated_data[obj_field] = val.save(context=self.context)

    def _materialize_deferred_list(self, items):
        """Convert a list of DeferredCreate items into saved model instances.

        Args:
            items (list): A list of items which may include DeferredCreate instances.

        Return:
            A list where all DeferredCreate instances have been replaced with their saved model instances.
        """
        if not items:
            return []
        out = []
        for item in items:
            if isinstance(item, DeferredCreate):
                out.append(item.save(context=self.context))
            else:
                out.append(item)
        return out


class NestedGetOrCreateMixin:
    """Mixin for nested serializers to get-or-create related instances based on a unique key field (e.g., name)."""

    key_field = "name"
    exclude_compare_fields = {"id", "created_at", "updated_at"}

    def get_fields(self):
        """Override to remove UniqueValidator from the key field, since we handle uniqueness in create()."""
        fields = super().get_fields()
        for f in fields.values():
            if hasattr(f, "validators"):
                f.validators = [v for v in f.validators if not isinstance(v, UniqueValidator)]
        return fields

    def create(self, validated_data):
        """Try to create a new instance. If it violates unique constraint, fetch existing and compare fields.

        Args:
            validated_data (dict): The validated data from the serializer.

        Returns:
            The created or existing instance.
        """
        Model = self.Meta.model

        try:
            with transaction.atomic():
                return Model.objects.create(**validated_data)

        except IntegrityError as err:
            key_value = validated_data.get(self.key_field)
            if key_value is None:
                raise

            existing = Model.objects.filter(**{self.key_field: key_value}).first()
            if existing is None:
                raise

            for field, incoming in validated_data.items():
                if field in self.exclude_compare_fields:
                    continue
                if getattr(existing, field) != incoming:
                    raise serializers.ValidationError(
                        {field: f"{Model.__name__} with {self.key_field}={key_value!r} already exists but differs."}
                    ) from err

            return existing


class StrictPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    """Accept PK only. If a dict/object is provided -> validation error."""

    default_error_messages = {
        "invalid": "Expected an integer id.",
    }

    def to_internal_value(self, data):
        """Reject dict/object payloads and only accept PK values."""
        if isinstance(data, dict):
            self.fail("invalid")
        return super().to_internal_value(data)


@dataclass(frozen=True)
class DeferredCreate:
    """Helper dataclass to represent a deferred creation of a related instance."""

    serializer_class: type[serializers.Serializer]
    validated_data: dict[str, any]

    def save(self, *, context):
        """Perform the actual creation of the related instance using the serializer class and validated data."""
        ser = self.serializer_class(data=self.validated_data, context=context)
        ser.is_valid(raise_exception=True)
        return ser.save()


class CreateOnlyRelatedField(serializers.Field):
    """Accept object only (dict). Creates related instance using create_serializer_class.

    Rejects any payload containing 'id'.
    """

    default_error_messages = {
        "invalid": "Expected an object.",
        "id_not_allowed": "Do not include 'id' here. Use the *_id field to reference an existing object.",
    }

    def __init__(self, *, create_serializer_class, **kwargs):
        super().__init__(**kwargs)
        self.create_serializer_class = create_serializer_class

    def to_internal_value(self, data):
        """Create the related object using the provided serializer."""
        if not isinstance(data, dict):
            self.fail("invalid")
        if "id" in data:
            self.fail("id_not_allowed")

        ser = self.create_serializer_class(data=data, context=self.context)
        ser.is_valid(raise_exception=True)

        return DeferredCreate(
            serializer_class=self.create_serializer_class,
            validated_data=ser.validated_data,
        )

    def to_representation(self, value):
        """This field is meant for write-only use (creating related objects), so we won't serialize it back."""
        return None


class CreateOnlyRelatedListField(serializers.Field):
    """Accepts a list of objects (dicts). Rejects any item containing 'id'.

    Returns a list[DeferredCreate] (no DB writes during validation).
    """

    default_error_messages = {
        "invalid": "Expected a list of objects.",
        "item_invalid": "Each item must be an object.",
        "id_not_allowed": "Do not include 'id' inside items. Use the *_ids field to reference existing objects.",
    }

    def __init__(self, *, create_serializer_class, **kwargs):
        super().__init__(**kwargs)
        self.create_serializer_class = create_serializer_class

    def to_internal_value(self, data):
        """Create the related object using the provided serializer."""
        if not isinstance(data, list):
            self.fail("invalid")

        deferred = []
        item_errors = {}

        for i, item in enumerate(data):
            if not isinstance(item, dict):
                item_errors[i] = {"non_field_errors": [self.error_messages["item_invalid"]]}
                continue
            if "id" in item:
                item_errors[i] = {"id": [self.error_messages["id_not_allowed"]]}
                continue

            ser = self.create_serializer_class(data=item, context=self.context)
            try:
                ser.is_valid(raise_exception=True)
            except serializers.ValidationError as e:
                item_errors[i] = e.detail
                continue

            deferred.append(
                DeferredCreate(
                    serializer_class=self.create_serializer_class,
                    validated_data=ser.validated_data,
                )
            )

        if item_errors:
            raise serializers.ValidationError(item_errors)

        return deferred

    def to_representation(self, value):
        """This field is meant for write-only use (creating related objects), so we won't serialize it back."""
        return None


class ReadOnlyFIeldsMixin:
    """Mixin to set all fields of a serializer to read-only."""

    def get_read_only_fields(self):
        """Override to set all fields to read-only."""
        read_only_fields = super().get_read_only_fields()
        common_fields = ["id", "created_at", "updated_at"]
        return list(set(read_only_fields) | set(common_fields))
