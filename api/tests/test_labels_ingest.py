"""Tests for label-set workbook ingestion."""

from uuid import UUID, uuid4

from django.test import TestCase
from rest_framework import serializers

from api.factories.label import LabelFactory
from api.factories.label_set import LabelSetFactory
from api.models import Label, LabelSet
from api.utils.labels_ingest import ingest_label_data


def make_label(
    name: str,
    *,
    label_id: UUID | None = None,
) -> dict:
    """Create parsed label data suitable for ingestion."""
    return {
        "id": label_id,
        "name": name,
        "parent_label_name": None,
        "lowest_taxonomic_name": None,
        "lowest_aphia_id": None,
        "name_is_lowest": False,
        "identification_qualifier": None,
    }


class IngestLabelDataTests(TestCase):
    """Tests for creating label sets and labels atomically."""

    def test_creates_label_set_and_labels(self) -> None:
        """Create labels with supplied and generated UUIDs."""
        label_set_id = uuid4()
        supplied_label_id = uuid4()

        result = ingest_label_data(
            label_set_id,
            {"name": "Test label set"},
            [
                make_label("Fish", label_id=supplied_label_id),
                make_label("Coral"),
            ],
        )

        label_set = LabelSet.objects.get(pk=label_set_id)
        labels = Label.objects.filter(label_set=label_set).order_by("name")

        self.assertEqual(label_set.name, "Test label set")
        self.assertEqual(labels.count(), 2)

        supplied_label = labels.get(name="Fish")
        generated_label = labels.get(name="Coral")

        self.assertEqual(supplied_label.id, supplied_label_id)
        self.assertIsNotNone(generated_label.id)
        self.assertEqual(supplied_label.label_set_id, label_set_id)
        self.assertEqual(generated_label.label_set_id, label_set_id)

        self.assertEqual(str(result["label_set"]["id"]), str(label_set_id))
        self.assertEqual(len(result["labels"]), 2)

    def test_rejects_existing_label_set_uuid(self) -> None:
        """Reject a label-set UUID that already exists."""
        existing_label_set = LabelSetFactory()

        with self.assertRaises(serializers.ValidationError) as exc_info:
            ingest_label_data(
                existing_label_set.id,
                {"name": "Replacement label set"},
                [make_label("Fish")],
            )

        self.assertIn("label-set-uuid", exc_info.exception.detail)
        self.assertIn(
            str(existing_label_set.id),
            str(exc_info.exception.detail["label-set-uuid"]),
        )

        self.assertEqual(LabelSet.objects.count(), 1)
        self.assertFalse(Label.objects.exists())

    def test_rejects_existing_label_uuid(self) -> None:
        """Reject a supplied label UUID that already exists."""
        existing_label = LabelFactory()
        new_label_set_id = uuid4()

        with self.assertRaises(serializers.ValidationError) as exc_info:
            ingest_label_data(
                new_label_set_id,
                {"name": "New label set"},
                [make_label("Fish", label_id=existing_label.id)],
            )

        self.assertIn("label-name-uuid", exc_info.exception.detail)
        self.assertIn(
            str(existing_label.id),
            str(exc_info.exception.detail["label-name-uuid"]),
        )

        self.assertFalse(LabelSet.objects.filter(pk=new_label_set_id).exists())

    def test_rolls_back_if_a_label_is_invalid(self) -> None:
        """Roll back the label set and earlier labels if any label fails."""
        label_set_id = uuid4()
        first_label_id = uuid4()

        with self.assertRaises(serializers.ValidationError):
            ingest_label_data(
                label_set_id,
                {"name": "Rollback test label set"},
                [
                    make_label("Valid label", label_id=first_label_id),
                    make_label("x" * 256),
                ],
            )

        self.assertFalse(LabelSet.objects.filter(pk=label_set_id).exists())
        self.assertFalse(Label.objects.filter(pk=first_label_id).exists())

    def test_rejects_duplicate_label_uuids_in_workbook(self) -> None:
        """Reject a label UUID used by multiple workbook rows."""
        label_set_id = uuid4()
        duplicate_label_id = uuid4()

        with self.assertRaises(serializers.ValidationError) as exc_info:
            ingest_label_data(
                label_set_id,
                {"name": "Duplicate UUID label set"},
                [
                    make_label("Fish", label_id=duplicate_label_id),
                    make_label("Coral", label_id=duplicate_label_id),
                ],
            )

        self.assertIn("label-name-uuid", exc_info.exception.detail)
        self.assertIn(
            str(duplicate_label_id),
            str(exc_info.exception.detail["label-name-uuid"]),
        )
        self.assertFalse(LabelSet.objects.filter(pk=label_set_id).exists())

    def test_generates_label_set_uuid_when_omitted(self) -> None:
        """Generate a label-set UUID when the workbook does not supply one."""
        result = ingest_label_data(
            None,
            {"name": "Generated UUID label set"},
            [make_label("Fish")],
        )

        label_set = LabelSet.objects.get(name="Generated UUID label set")

        self.assertIsNotNone(label_set.pk)
        self.assertEqual(
            str(result["label_set"]["id"]),
            str(label_set.pk),
        )
