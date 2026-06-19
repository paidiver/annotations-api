"""Tests for base API functionality."""

from contextlib import nullcontext
from unittest import TestCase
from unittest.mock import Mock, patch

from django.db import IntegrityError
from django.urls import reverse
from rest_framework import serializers, status
from rest_framework.test import APITestCase

from api.models.base import AliasedShapesEnumField, ShapeEnum
from api.serializers.base import (
    BaseSerializer,
    CreateOnlyRelatedField,
    CreateOnlyRelatedListField,
    DeferredCreate,
    NestedGetOrCreateMixin,
    ReadOnlyFieldsMixin,
    StrictPrimaryKeyRelatedField,
)


class HealthTests(APITestCase):
    """Integration tests for LabelViewSet endpoints."""

    def test_health_endpoint(self) -> None:
        """Test the health endpoint."""
        resp = self.client.get(reverse("Health"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {"status": "ok"})


class BaseModelTests(TestCase):
    """Unit tests for model helpers in api.models.base."""

    def test_aliased_shapes_normalise_non_string_passthrough(self) -> None:
        """Non-string values should pass through unchanged."""
        field = AliasedShapesEnumField(max_length=32)
        self.assertEqual(field.normaliseAnnotationShapeValue(123), 123)

    def test_case_insensitive_enum_matching_and_missing(self) -> None:
        """Enums should match case-insensitively and return None for unsupported values."""
        self.assertEqual(ShapeEnum("PoLyGoN"), ShapeEnum.polygon)
        self.assertIsNone(ShapeEnum._missing_(123))
        self.assertIsNone(ShapeEnum._missing_("unknown-shape"))


class _CreateRelatedSerializer(serializers.Serializer):
    """Small serializer used by field tests."""

    name = serializers.CharField()

    def create(self, validated_data: dict) -> dict:
        """Return plain dict for easy assertions."""
        return {"name": validated_data["name"]}


class _SingleRelatedWrapperSerializer(serializers.Serializer):
    """Serializer wrapper for CreateOnlyRelatedField."""

    related = CreateOnlyRelatedField(create_serializer_class=_CreateRelatedSerializer)


class _ListRelatedWrapperSerializer(serializers.Serializer):
    """Serializer wrapper for CreateOnlyRelatedListField."""

    related = CreateOnlyRelatedListField(create_serializer_class=_CreateRelatedSerializer)


class BaseSerializerHelpersTests(TestCase):
    """Tests for serializer helper classes in api.serializers.base."""

    def test_materialize_deferred_related_and_list(self) -> None:
        """Deferred items should be saved while plain items are preserved."""
        helper = type("Helper", (), {"context": {"request_id": "x"}})()

        with patch.object(DeferredCreate, "save", return_value={"name": "saved"}):
            validated_data = {
                "related": DeferredCreate(_CreateRelatedSerializer, {"name": "cod"}),
            }
            BaseSerializer._materialize_deferred_related(helper, validated_data, [("related", "related_id")])
            self.assertEqual(validated_data["related"], {"name": "saved"})

            items = [DeferredCreate(_CreateRelatedSerializer, {"name": "crab"}), {"name": "existing"}]
            out = BaseSerializer._materialize_deferred_list(helper, items)
            self.assertEqual(out, [{"name": "saved"}, {"name": "existing"}])

    def test_deferred_create_save(self) -> None:
        """DeferredCreate should validate then create using the provided serializer class."""
        deferred = DeferredCreate(serializer_class=_CreateRelatedSerializer, validated_data={"name": "lobster"})
        self.assertEqual(deferred.save(context={}), {"name": "lobster"})

    def test_nested_get_or_create_validation_when_key_fields_empty(self) -> None:
        """When key fields are disabled, integrity collisions should become ValidationError."""

        class DummyModel:
            objects = Mock()

        class DummySerializer(NestedGetOrCreateMixin):
            class Meta:
                model = DummyModel

        DummyModel.objects.create.side_effect = IntegrityError("duplicate")
        instance = DummySerializer()
        instance.key_fields = []

        with (
            patch("api.serializers.base.transaction.atomic", return_value=nullcontext()),
            self.assertRaises(serializers.ValidationError),
        ):
            instance.create({"name": "A"})

    def test_nested_get_or_create_reraises_when_existing_not_found(self) -> None:
        """Integrity collisions should be re-raised if existing row cannot be located."""

        class DummyModel:
            objects = Mock()

        class DummySerializer(NestedGetOrCreateMixin):
            class Meta:
                model = DummyModel

        DummyModel.objects.create.side_effect = IntegrityError("duplicate")
        DummyModel.objects.filter.return_value.first.return_value = None

        with (
            patch("api.serializers.base.transaction.atomic", return_value=nullcontext()),
            self.assertRaises(IntegrityError),
        ):
            DummySerializer().create({"name": "A", "uri": "u"})

    def test_nested_get_or_create_ignores_excluded_fields_and_returns_existing(self) -> None:
        """Excluded compare fields should not block returning the existing object."""

        class Existing:
            name = "A"
            uri = "u"

        class DummyModel:
            objects = Mock()

        class DummySerializer(NestedGetOrCreateMixin):
            class Meta:
                model = DummyModel

        existing = Existing()
        DummyModel.objects.create.side_effect = IntegrityError("duplicate")
        DummyModel.objects.filter.return_value.first.return_value = existing

        with patch("api.serializers.base.transaction.atomic", return_value=nullcontext()):
            returned = DummySerializer().create({"id": "different", "name": "A", "uri": "u"})
        self.assertIs(returned, existing)

    def test_nested_get_or_create_raises_when_existing_differs(self) -> None:
        """If non-excluded fields differ, raise ValidationError with field details."""

        class Existing:
            name = "A"
            uri = "u"

        class DummyModel:
            objects = Mock()

        class DummySerializer(NestedGetOrCreateMixin):
            class Meta:
                model = DummyModel

        DummyModel.objects.create.side_effect = IntegrityError("duplicate")
        DummyModel.objects.filter.return_value.first.return_value = Existing()

        with (
            patch("api.serializers.base.transaction.atomic", return_value=nullcontext()),
            self.assertRaises(serializers.ValidationError),
        ):
            DummySerializer().create({"name": "different", "uri": "u"})

    def test_strict_primary_key_related_field_rejects_dict(self) -> None:
        """StrictPrimaryKeyRelatedField should reject object payloads."""
        queryset = Mock()
        field = StrictPrimaryKeyRelatedField(queryset=queryset)
        with self.assertRaises(serializers.ValidationError):
            field.to_internal_value({"id": 1})

    def test_create_only_related_field_validation_and_representation(self) -> None:
        """CreateOnlyRelatedField should reject non-object/id payloads and remain write-only."""
        invalid_type = _SingleRelatedWrapperSerializer(data={"related": "bad"})
        self.assertFalse(invalid_type.is_valid())
        self.assertIn("Expected an object.", invalid_type.errors["related"])

        with_id = _SingleRelatedWrapperSerializer(data={"related": {"id": 1, "name": "cod"}})
        self.assertFalse(with_id.is_valid())
        self.assertIn("Do not include 'id' here.", str(with_id.errors["related"]))

        field = _SingleRelatedWrapperSerializer().fields["related"]
        self.assertIsNone(field.to_representation({"name": "unused"}))

    def test_create_only_related_list_field_validation_paths(self) -> None:
        """List field should return index-specific errors for invalid item kinds and serializer errors."""
        invalid_type = _ListRelatedWrapperSerializer(data={"related": "bad"})
        self.assertFalse(invalid_type.is_valid())
        self.assertIn("Expected a list of objects.", invalid_type.errors["related"])

        invalid_item = _ListRelatedWrapperSerializer(data={"related": ["bad"]})
        self.assertFalse(invalid_item.is_valid())
        self.assertIn("Each item must be an object.", str(invalid_item.errors["related"]))

        item_with_id = _ListRelatedWrapperSerializer(data={"related": [{"id": 1}]})
        self.assertFalse(item_with_id.is_valid())
        self.assertIn("Do not include 'id' inside items.", str(item_with_id.errors["related"]))

        serializer_error = _ListRelatedWrapperSerializer(data={"related": [{}]})
        self.assertFalse(serializer_error.is_valid())
        self.assertIn("This field is required.", str(serializer_error.errors["related"]))

        field = _ListRelatedWrapperSerializer().fields["related"]
        self.assertIsNone(field.to_representation([{"name": "unused"}]))

    def test_read_only_fields_mixin_unions_parent_and_common_fields(self) -> None:
        """ReadOnlyFieldsMixin should always include id/created/updated in addition to parent values."""

        class Parent:
            def get_read_only_fields(self) -> list[str]:
                return ["custom"]

        class Dummy(ReadOnlyFieldsMixin, Parent):
            pass

        result = Dummy().get_read_only_fields()
        self.assertIn("custom", result)
        self.assertIn("id", result)
        self.assertIn("created_at", result)
        self.assertIn("updated_at", result)
