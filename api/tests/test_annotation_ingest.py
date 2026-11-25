"""Tests for annotation-set workbook ingestion."""

from uuid import UUID, uuid4

from django.test import TransactionTestCase
from rest_framework import serializers

from api.factories.annotation_set import AnnotationSetFactory
from api.factories.image import ImageFactory
from api.factories.image_set import ImageSetFactory
from api.factories.label import LabelFactory
from api.factories.label_set import LabelSetFactory
from api.models import Annotation, AnnotationSet
from api.utils.annotations_ingest import ingest_annotation_data


def make_annotation_data(
    annotation_id: UUID,
    image_id: UUID | None,
    image_filename: str | None,
    label_name: str,
) -> dict:
    """Create parsed annotation data for ingestion tests."""
    return {
        "id": annotation_id,
        "image_id": image_id,
        "image_filename": image_filename,
        "human_or_machine": "human",
        "creator": {
            "name": "Alice Example",
            "uri": "https://orcid.org/0000-0001-0000-0001",
        },
        "creation_datetime": "2026-11-23T10:00:00Z",
        "label_name": label_name,
        "shape": "point",
        "coordinates": [100, 200],
        "dimension_pixels": None,
        "human_reviewer": None,
        "machine_training_validation": None,
        "additional_info": "Test annotation",
        "detection_model_ref": None,
        "classification_model_ref": None,
        "detection_confidence": None,
        "classification_confidence": None,
        "mask": None,
    }


class IngestAnnotationDataTests(TransactionTestCase):
    """Tests for atomic annotation-set ingestion."""

    def setUp(self) -> None:
        """Create the image and label records referenced by workbooks."""
        self.image_set = ImageSetFactory(
            name="Test image set",
            handle="https://example.com/image-sets/test",
        )
        self.image = ImageFactory(
            image_set=self.image_set,
            filename="test-image.jpg",
        )
        self.label_set = LabelSetFactory(name="Test label set")
        self.label = LabelFactory(
            label_set=self.label_set,
            name="test-fish",
        )

        self.annotation_set_id = uuid4()
        self.annotation_id = uuid4()

        self.annotation_set_data = {
            "name": "Test annotation set",
            "abstract": "Test abstract",
            "objective": "Test objective",
            "funding": "Test funding",
        }
        self.references = {
            "image_set_names": [self.image_set.name],
            "image_set_ids": [self.image_set.id],
            "image_set_handles": [self.image_set.handle],
            "label_set_names": [self.label_set.name],
            "label_set_ids": [self.label_set.id],
        }
        self.annotations_data = [
            make_annotation_data(
                self.annotation_id,
                self.image.id,
                self.image.filename,
                self.label.name,
            )
        ]

    def test_creates_annotation_set_and_annotations(self) -> None:
        """Create and link an annotation set and human annotation."""
        result = ingest_annotation_data(
            self.annotation_set_id,
            self.annotation_set_data,
            self.references,
            [],
            self.annotations_data,
        )

        annotation_set = AnnotationSet.objects.get(pk=self.annotation_set_id)
        annotation = Annotation.objects.get(pk=self.annotation_id)

        self.assertEqual(
            result["annotation_set"]["id"],
            str(self.annotation_set_id),
        )
        self.assertEqual(len(result["models"]), 0)
        self.assertEqual(len(result["annotations"]), 1)

        self.assertEqual(
            list(annotation_set.image_sets.all()),
            [self.image_set],
        )
        self.assertEqual(
            list(annotation_set.label_sets.all()),
            [self.label_set],
        )
        self.assertEqual(annotation.image, self.image)
        self.assertEqual(annotation.label, self.label)
        self.assertEqual(annotation.creator.name, "Alice Example")
        self.assertEqual(annotation.shape, "single-pixel")

    def test_creates_model_and_algorithm_annotation(self) -> None:
        """Create an annotation model and resolve its workbook ID."""
        models_data = [
            {
                "model_id": "detector-1",
                "name": "Test detector",
                "version": "1.0",
                "task": "detection",
                "score_type": "objectness",
                "confidence_threshold": 0.5,
                "label_set_id": self.label_set.id,
            }
        ]

        annotation_data = make_annotation_data(
            self.annotation_id,
            self.image.id,
            self.image.filename,
            self.label.name,
        )
        annotation_data.update(
            {
                "human_or_machine": "algorithm",
                "creator": None,
                "detection_model_ref": "detector-1",
                "detection_confidence": 0.8,
            }
        )

        result = ingest_annotation_data(
            self.annotation_set_id,
            self.annotation_set_data,
            self.references,
            models_data,
            [annotation_data],
        )

        annotation = Annotation.objects.get(pk=self.annotation_id)

        self.assertEqual(len(result["models"]), 1)
        self.assertEqual(
            annotation.detection_model.model_id,
            "detector-1",
        )
        self.assertEqual(annotation.detection_confidence, 0.8)
        self.assertIsNone(annotation.creator)

    def test_resolves_image_by_filename(self) -> None:
        """Resolve an image by filename when its UUID is omitted."""
        annotation_data = make_annotation_data(
            self.annotation_id,
            None,
            self.image.filename,
            self.label.name,
        )

        ingest_annotation_data(
            self.annotation_set_id,
            self.annotation_set_data,
            self.references,
            [],
            [annotation_data],
        )

        annotation = Annotation.objects.get(pk=self.annotation_id)
        self.assertEqual(annotation.image, self.image)

    def test_rejects_existing_annotation_set_uuid(self) -> None:
        """Reject an annotation-set UUID already in the database."""
        AnnotationSetFactory(id=self.annotation_set_id)

        with self.assertRaises(serializers.ValidationError):
            ingest_annotation_data(
                self.annotation_set_id,
                self.annotation_set_data,
                self.references,
                [],
                self.annotations_data,
            )

    def test_rejects_existing_annotation_uuid(self) -> None:
        """Reject an annotation UUID already in the database."""
        existing_set = AnnotationSetFactory(
            image_set_ids=[self.image_set.id],
            label_set_ids=[self.label_set.id],
        )
        Annotation.objects.create(
            id=self.annotation_id,
            image=self.image,
            annotation_set=existing_set,
            label=self.label,
            human_or_machine="human",
            shape="single-pixel",
        )

        with self.assertRaises(serializers.ValidationError):
            ingest_annotation_data(
                self.annotation_set_id,
                self.annotation_set_data,
                self.references,
                [],
                self.annotations_data,
            )

        self.assertFalse(AnnotationSet.objects.filter(pk=self.annotation_set_id).exists())

    def test_rejects_undefined_model_reference(self) -> None:
        """Reject an annotation referencing an undefined model."""
        annotation_data = make_annotation_data(
            self.annotation_id,
            self.image.id,
            self.image.filename,
            self.label.name,
        )
        annotation_data.update(
            {
                "human_or_machine": "algorithm",
                "creator": None,
                "detection_model_ref": "missing-model",
            }
        )

        with self.assertRaises(serializers.ValidationError):
            ingest_annotation_data(
                self.annotation_set_id,
                self.annotation_set_data,
                self.references,
                [],
                [annotation_data],
            )

    def test_rejects_ambiguous_label_name(self) -> None:
        """Reject a label name found in multiple linked label sets."""
        second_label_set = LabelSetFactory(name="Second label set")
        LabelFactory(
            label_set=second_label_set,
            name=self.label.name,
        )

        references = self.references.copy()
        references["label_set_names"] = [
            self.label_set.name,
            second_label_set.name,
        ]
        references["label_set_ids"] = [
            self.label_set.id,
            second_label_set.id,
        ]

        with self.assertRaises(serializers.ValidationError):
            ingest_annotation_data(
                self.annotation_set_id,
                self.annotation_set_data,
                references,
                [],
                self.annotations_data,
            )

    def test_rolls_back_if_later_annotation_is_invalid(self) -> None:
        """Roll back all records when a later annotation cannot resolve."""
        second_annotation_id = uuid4()
        invalid_annotation = make_annotation_data(
            second_annotation_id,
            self.image.id,
            self.image.filename,
            "missing-label",
        )

        with self.assertRaises(serializers.ValidationError):
            ingest_annotation_data(
                self.annotation_set_id,
                self.annotation_set_data,
                self.references,
                [],
                [
                    self.annotations_data[0],
                    invalid_annotation,
                ],
            )

        self.assertFalse(AnnotationSet.objects.filter(pk=self.annotation_set_id).exists())
        self.assertFalse(Annotation.objects.filter(pk=self.annotation_id).exists())
        self.assertFalse(Annotation.objects.filter(pk=second_annotation_id).exists())
