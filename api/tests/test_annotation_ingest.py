"""Tests for annotation data ingestion functions."""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from django.test import TestCase

from api.utils.annotations_ingest import (
    ingest_annotation_data,
    insert_annotations_data,
    insert_annotations_set,
    insert_label_data,
)


def make_annotation_set_data(**overrides) -> dict:
    """Helper function to create input data for annotation set."""
    base = {
        "annotation-set-name": "Test Set",
        "annotation-abstract": "An abstract",
        "annotation-objective": "An objective",
        "annotation-target-environment": "Marine",
        "annotation-target-timescale": "2024",
        "annotation-curation-protocol": "Protocol v1",
        "annotation-set-version": "1",
        "annotation-context-name": "Context Name",
        "annotation-context-uri": "http://context.example.com",
        "annotation-project-name": "Project Name",
        "annotation-project-uri": "http://project.example.com",
        "annotation-pi-name": "Dr. Smith",
        "annotation-pi-uri": "http://pi.example.com",
        "annotation-license-name": "CC-BY-4.0",
        "annotation-license-uri": "http://license.example.com",
    }
    base.update(overrides)
    return base


def make_annotation_entry(**overrides) -> dict:
    """Helper function to create input data for new annotation."""
    base = {
        "image_id": str(uuid.uuid4()),
        "image_filename": "image_001.jpg",
        "label_name": "fish",
        "annotator_name": "Alice",
        "annotation_platform": "BIIGLE",
        "shape": "point",
        "coordinates": {"x": 100, "y": 200},
        "dimension_pixels": {"width": 1920, "height": 1080},
        "creation_datetime": "01012024 12:00:00",
    }
    base.update(overrides)
    return base


def make_label_list() -> list[dict]:
    """Helper function to create input data for labels."""
    return [
        {"name": "fish"},
        {"name": "coral"},
    ]


class InsertAnnotationsSetTests(TestCase):
    """Tests for inserting annotation sets from file upload."""

    def _mock_serializer(self, saved_data: dict, annotation_set_inst: Mock) -> MagicMock:
        """Return a mock AnnotationSetSerializer."""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = annotation_set_inst
        mock_serializer.data = saved_data
        return mock_serializer

    @patch("api.utils.annotations_ingest.AnnotationSetSerializer")
    def test_basic_insert_returns_serializer_data(self, mock_serializer: Mock) -> None:
        """Test that annotation set data is passed to serializer."""
        annotation_set_inst = MagicMock()
        annotation_set_inst.id = uuid.uuid4()
        annotation_set_inst.creators = MagicMock()
        annotation_set_inst.image_sets = MagicMock()

        expected_data = {"id": str(annotation_set_inst.id), "name": "Test Set"}
        mock_serializer.return_value = self._mock_serializer(expected_data, annotation_set_inst)

        result = insert_annotations_set(make_annotation_set_data())

        self.assertEqual(result, expected_data)

    @patch("api.utils.annotations_ingest.Creator")
    @patch("api.utils.annotations_ingest.AnnotationSetSerializer")
    def test_creators_are_added(self, mock_serializer: Mock, mock_get_creator: Mock) -> None:
        """Test that new creators for annotation set are inserted."""
        annotation_set_inst = MagicMock()
        annotation_set_inst.id = uuid.uuid4()
        annotation_set_inst.image_sets = MagicMock()

        mock_serializer.return_value = self._mock_serializer({"id": str(annotation_set_inst.id)}, annotation_set_inst)
        mock_creator = MagicMock()
        mock_get_creator.objects.get_or_create.return_value = (mock_creator, True)

        data = make_annotation_set_data(
            **{
                "annotation-creators-names": "Alice, Bob",
                "annotation-creators-uris": "http://alice.example.com, http://bob.example.com",
            }
        )
        insert_annotations_set(data)

        self.assertEqual(mock_get_creator.objects.get_or_create.call_count, 2)
        self.assertEqual(annotation_set_inst.creators.add.call_count, 2)

    @patch("api.utils.annotations_ingest.Creator")
    @patch("api.utils.annotations_ingest.AnnotationSetSerializer")
    def test_creators_with_fewer_uris_than_names(self, mock_serializer: Mock, mock_creator: Mock) -> None:
        """Test that missing creator URIs are filled with None."""
        annotation_set_inst = MagicMock()
        annotation_set_inst.id = uuid.uuid4()
        annotation_set_inst.image_sets = MagicMock()

        mock_serializer.return_value = self._mock_serializer({}, annotation_set_inst)
        mock_creator.objects.get_or_create.return_value = (MagicMock(), True)

        data = make_annotation_set_data(
            **{"annotation-creators-names": "Alice, Bob", "annotation-creators-uris": "http://alice.example.com"}
        )
        insert_annotations_set(data)

        calls = mock_creator.objects.get_or_create.call_args_list
        self.assertEqual(len(calls), 2)
        # Second creator should have uri=None
        self.assertEqual(calls[1].kwargs.get("uri") or calls[1][1].get("uri"), "")

    @patch("api.utils.annotations_ingest.ImageSet")
    @patch("api.utils.annotations_ingest.AnnotationSetSerializer")
    def test_image_set_resolved_by_uuid(self, mock_serializer: Mock, mock_get_image_set: Mock) -> None:
        """Test that image set for annotation set is retrieved by UUID."""
        image_set_id = uuid.uuid4()
        annotation_set_inst = MagicMock()
        annotation_set_inst.id = uuid.uuid4()
        annotation_set_inst.creators = MagicMock()

        mock_serializer.return_value = self._mock_serializer({}, annotation_set_inst)
        mock_image_set = MagicMock()
        mock_get_image_set.objects.filter.return_value.first.return_value = mock_image_set

        data = make_annotation_set_data(
            **{
                "annotation-image-set-uuid": str(image_set_id),
                "annotation-image-set-name": "My Image Set",
            }
        )
        insert_annotations_set(data)

        annotation_set_inst.image_sets.add.assert_called_once_with(mock_image_set)

    @patch("api.utils.annotations_ingest.ImageSet")
    @patch("api.utils.annotations_ingest.AnnotationSetSerializer")
    def test_image_set_resolved_by_name_when_uuid_missing(
        self, mock_serializer: Mock, mock_get_image_set: Mock
    ) -> None:
        """Test that image set for annotation set is retrieved by name if no UUID given."""
        annotation_set_inst = MagicMock()
        annotation_set_inst.id = uuid.uuid4()
        annotation_set_inst.creators = MagicMock()

        mock_serializer.return_value = self._mock_serializer({}, annotation_set_inst)

        named_image_set = MagicMock()
        named_image_set.id = "12345"
        named_image_set.name = "My Image Set"

        # No UUID lookup for empty value; name lookup succeeds
        mock_get_image_set.objects.filter.return_value = named_image_set

        data = make_annotation_set_data(
            **{"annotation-image-set-uuid": "", "annotation-image-set-name": "My Image Set"}
        )
        insert_annotations_set(data)

        mock_get_image_set.objects.filter.assert_called_once_with(name="My Image Set")
        annotation_set_inst.image_sets.add.assert_called_once()

    @patch("api.utils.annotations_ingest.ImageSet")
    @patch("api.utils.annotations_ingest.AnnotationSetSerializer")
    def test_raises_when_image_set_uuid_and_name_mismatch(
        self, mock_serializer: Mock, mock_get_image_set: Mock
    ) -> None:
        """Test that a ValueError is found if image set name matches a different UUID than what is given."""
        annotation_set_inst = MagicMock()
        annotation_set_inst.id = uuid.uuid4()
        annotation_set_inst.creators = MagicMock()

        mock_serializer.return_value = self._mock_serializer({}, annotation_set_inst)

        conflicting_record = MagicMock()
        conflicting_record.id = "12345"
        conflicting_record.name = "Image Set Name"

        # UUID lookup misses; name lookup hits a *different* record
        mock_get_image_set.objects.filter.return_value.first.side_effect = [None, conflicting_record]

        data = make_annotation_set_data(
            **{
                "annotation-image-set-uuid": "678910",
                "annotation-image-set-name": "Image Set Name",
            }
        )
        with self.assertRaisesMessage(
            ValueError,
            "ImageSet not found with id=678910 but name='Image Set Name' matched a different record (id=12345)",
        ):
            insert_annotations_set(data)

    @patch("api.utils.annotations_ingest.ImageSet")
    @patch("api.utils.annotations_ingest.AnnotationSetSerializer")
    def test_raises_when_image_set_not_found(self, mock_serializer: Mock, mock_get_image_set: Mock) -> None:
        """Test that a ValueError is raised when given image set is not found."""
        annotation_set_inst = MagicMock()
        annotation_set_inst.id = uuid.uuid4()
        annotation_set_inst.creators = MagicMock()

        mock_serializer.return_value = self._mock_serializer({}, annotation_set_inst)
        mock_get_image_set.objects.filter.return_value.first.return_value = None

        data = make_annotation_set_data(
            **{
                "annotation-image-set-uuid": str(uuid.uuid4()),
                "annotation-image-set-name": "Missing Set",
            }
        )
        with self.assertRaises(ValueError):
            insert_annotations_set(data)


class InsertLabelDataTests(TestCase):
    """Tests for inserting label data from file upload."""

    @patch("api.utils.annotations_ingest.LabelSerializer")
    @patch("api.utils.annotations_ingest.Label")
    def test_inserts_new_labels(self, mock_get_label: Mock, mock_label_serializer: Mock) -> None:
        """Test that new labels for the annotation set are created in DB."""
        annotation_set_id = uuid.uuid4()
        mock_get_label.objects.filter.return_value.first.return_value = None  # no existing labels

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {"id": str(uuid.uuid4()), "name": "fish"}
        mock_label_serializer.return_value = mock_serializer

        labels = make_label_list()
        result = insert_label_data(labels, annotation_set_id)

        self.assertEqual(len(result), len(labels))
        self.assertEqual(mock_label_serializer.call_count, len(labels))

    @patch("api.utils.annotations_ingest.LabelSerializer")
    @patch("api.utils.annotations_ingest.Label")
    def test_skips_existing_labels(self, mock_get_label: Mock, mock_label_serializer: Mock) -> None:
        """Test that existing labels for the annotation set are not recreated."""
        annotation_set_id = uuid.uuid4()
        # Simulate all labels already existing
        mock_get_label.objects.filter.return_value.first.return_value = MagicMock()

        result = insert_label_data(make_label_list(), annotation_set_id)

        mock_label_serializer.assert_not_called()
        self.assertEqual(result, [])

    @patch("api.utils.annotations_ingest.LabelSerializer")
    @patch("api.utils.annotations_ingest.Label")
    def test_partial_existing_labels_only_inserts_new(self, mock_get_label: Mock, mock_label_serializer: Mock) -> None:
        """Test that only required new labels are created for the annotation set if some exist."""
        annotation_set_id = uuid.uuid4()

        # First label exists, second does not
        mock_get_label.objects.filter.return_value.first.side_effect = [MagicMock(), None]

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {"name": "coral"}
        mock_label_serializer.return_value = mock_serializer

        labels = [
            {"name": "fish"},
            {"name": "coral"},
        ]
        result = insert_label_data(labels, annotation_set_id)

        self.assertEqual(mock_label_serializer.call_count, 1)
        self.assertEqual(len(result), 1)


class InsertAnnotationsDataTests(TestCase):
    """Tests for inserting annotation data from file upload."""

    def _setup_mocks(  # noqa: PLR0913
        self,
        mock_get_image: Mock,
        mock_get_name: Mock,
        mock_get_annotator: Mock,
        mock_annotation_serializer: Mock,
        mock_annotation_label_serializer: Mock,
        mock_annotator_serializer: Mock,
    ) -> tuple[Mock, Mock, Mock]:
        """Set up mocks for required objects to insert annotation data."""
        image_id = uuid.uuid4()
        label_id = uuid.uuid4()
        annotator_id = uuid.uuid4()

        mock_image = MagicMock()
        mock_image.id = image_id
        mock_get_image.objects.filter.return_value.first.return_value = mock_image

        mock_label = MagicMock()
        mock_label.id = label_id
        mock_get_name.objects.filter.return_value.first.return_value = mock_label

        mock_annotator = MagicMock()
        mock_annotator.id = annotator_id
        mock_get_annotator.objects.get_or_create.return_value = (mock_annotator, True)

        mock_anno_obj = MagicMock()
        mock_anno_obj.id = uuid.uuid4()
        anno_ser = MagicMock()
        anno_ser.is_valid.return_value = True
        anno_ser.save.return_value = mock_anno_obj
        anno_ser.data = {"id": str(mock_anno_obj.id)}
        mock_annotation_serializer.return_value = anno_ser

        anno_label_ser = MagicMock()
        anno_label_ser.is_valid.return_value = True
        anno_label_ser.data = {}
        mock_annotation_label_serializer.return_value = anno_label_ser

        annotator_ser = MagicMock()
        annotator_ser.data = {"name": "Alice"}
        mock_annotator_serializer.return_value = annotator_ser

        return mock_image, mock_label, mock_annotator

    @patch("api.utils.annotations_ingest.AnnotatorSerializer")
    @patch("api.utils.annotations_ingest.AnnotationLabelSerializer")
    @patch("api.utils.annotations_ingest.AnnotationSerializer")
    @patch("api.utils.annotations_ingest.Annotator")
    @patch("api.utils.annotations_ingest.Label")
    @patch("api.utils.annotations_ingest.Image")
    def test_insert_annotations(  # noqa: PLR0913
        self,
        mock_get_image: Mock,
        mock_get_name: Mock,
        mock_get_annotator: Mock,
        mock_annotation_serializer: Mock,
        mock_annotation_label_serializer: Mock,
        mock_annotator_serializer: Mock,
    ) -> None:
        """Test that annotation data can be inserted successfully."""
        self._setup_mocks(
            mock_get_image,
            mock_get_name,
            mock_get_annotator,
            mock_annotation_serializer,
            mock_annotation_label_serializer,
            mock_annotator_serializer,
        )
        annotation_set_id = uuid.uuid4()
        entries = [make_annotation_entry() for _ in range(5)]
        result = insert_annotations_data(entries, annotation_set_id)

        self.assertEqual(result["created"], 5)

    @patch("api.utils.annotations_ingest.Image")
    def test_raises_when_image_not_found(self, mock_get_image: Mock) -> None:
        """Test that a ValueError is raised when an image within the annotation data isn't found."""
        mock_get_image.objects.filter.return_value.first.return_value = None
        annotation_set_id = uuid.uuid4()

        with self.assertRaises(ValueError) as ctx:
            insert_annotations_data([make_annotation_entry()], annotation_set_id)

        self.assertIn("Image not found", str(ctx.exception))

    @patch("api.utils.annotations_ingest.Image")
    def test_raises_when_image_uuid_and_filename_conflict(self, mock_get_image: Mock) -> None:
        """Test that a ValueError is raised when the image UUID and filename don't point to the same record."""
        conflicting_image = MagicMock()
        conflicting_image.id = uuid.uuid4()
        # UUID miss, name hit (different record)
        mock_get_image.objects.filter.return_value.first.side_effect = [None, conflicting_image]

        entry = make_annotation_entry(image_id=str(uuid.uuid4()), image_filename="conflict.jpg")
        with self.assertRaises(ValueError):
            insert_annotations_data([entry], uuid.uuid4())

    @patch("api.utils.annotations_ingest.Label")
    @patch("api.utils.annotations_ingest.Image")
    def test_raises_when_label_not_found(self, mock_get_image: Mock, mock_get_label: Mock) -> None:
        """Test that a ValueError is raised when a label is not found for an annotation."""
        mock_image = MagicMock()
        mock_get_image.objects.filter.return_value.first.return_value = mock_image
        mock_get_label.objects.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as ctx:
            insert_annotations_data([make_annotation_entry()], uuid.uuid4())

        self.assertIn("Label", str(ctx.exception))
        self.assertIn("not found", str(ctx.exception))

    @patch("api.utils.annotations_ingest.AnnotatorSerializer")
    @patch("api.utils.annotations_ingest.AnnotationLabelSerializer")
    @patch("api.utils.annotations_ingest.AnnotationSerializer")
    @patch("api.utils.annotations_ingest.Annotator")
    @patch("api.utils.annotations_ingest.Label")
    @patch("api.utils.annotations_ingest.Image")
    def test_creation_datetime_parsed_from_string(  # noqa: PLR0913
        self,
        mock_get_image: Mock,
        mock_get_name: Mock,
        mock_get_annotator: Mock,
        mock_annotation_serializer: Mock,
        mock_annotation_label_serializer: Mock,
        mock_annotator_serializer: Mock,
    ) -> None:
        """Test that creation datetime for an annotation is parsed correctly."""
        self._setup_mocks(
            mock_get_image,
            mock_get_name,
            mock_get_annotator,
            mock_annotation_serializer,
            mock_annotation_label_serializer,
            mock_annotator_serializer,
        )
        entry = make_annotation_entry(creation_datetime="15062023 09:30:00")
        insert_annotations_data([entry], uuid.uuid4())

        anno_label_call_data = (
            mock_annotation_label_serializer.call_args[1]["data"]
            if mock_annotation_label_serializer.call_args[1]
            else mock_annotation_label_serializer.call_args[0][0]
        )

        self.assertIsInstance(anno_label_call_data["creation_datetime"], datetime)
        self.assertEqual(anno_label_call_data["creation_datetime"].day, 15)
        self.assertEqual(anno_label_call_data["creation_datetime"].month, 6)
        self.assertEqual(anno_label_call_data["creation_datetime"].year, 2023)

    @patch("api.utils.annotations_ingest.AnnotatorSerializer")
    @patch("api.utils.annotations_ingest.AnnotationLabelSerializer")
    @patch("api.utils.annotations_ingest.AnnotationSerializer")
    @patch("api.utils.annotations_ingest.Annotator")
    @patch("api.utils.annotations_ingest.Label")
    @patch("api.utils.annotations_ingest.Image")
    def test_invalid_datetime_falls_back_to_now(  # noqa: PLR0913
        self,
        mock_get_image: Mock,
        mock_get_name: Mock,
        mock_get_annotator: Mock,
        mock_annotation_serializer: Mock,
        mock_annotation_label_serializer: Mock,
        mock_annotator_serializer: Mock,
    ) -> None:
        """Test that creation datetime for an annotation falls back to now if input data can't be parsed."""
        self._setup_mocks(
            mock_get_image,
            mock_get_name,
            mock_get_annotator,
            mock_annotation_serializer,
            mock_annotation_label_serializer,
            mock_annotator_serializer,
        )
        entry = make_annotation_entry(creation_datetime="not-a-date")
        before = datetime.now()
        insert_annotations_data([entry], uuid.uuid4())
        after = datetime.now()

        anno_label_call_data = (
            mock_annotation_label_serializer.call_args[1]["data"]
            if mock_annotation_label_serializer.call_args[1]
            else mock_annotation_label_serializer.call_args[0][0]
        )

        dt = anno_label_call_data["creation_datetime"]
        self.assertIsInstance(dt, datetime)
        self.assertGreaterEqual(dt, before)
        self.assertLessEqual(dt, after)

    @patch("api.utils.annotations_ingest.AnnotatorSerializer")
    @patch("api.utils.annotations_ingest.AnnotationLabelSerializer")
    @patch("api.utils.annotations_ingest.AnnotationSerializer")
    @patch("api.utils.annotations_ingest.Annotator")
    @patch("api.utils.annotations_ingest.Label")
    @patch("api.utils.annotations_ingest.Image")
    def test_annotator_created_if_not_exists(  # noqa: PLR0913
        self,
        mock_get_image: Mock,
        mock_get_name: Mock,
        mock_get_annotator: Mock,
        mock_annotation_serializer: Mock,
        mock_annotation_label_serializer: Mock,
        mock_annotator_serializer: Mock,
    ) -> None:
        """Test that a record is created for a new annotator."""
        self._setup_mocks(
            mock_get_image,
            mock_get_name,
            mock_get_annotator,
            mock_annotation_serializer,
            mock_annotation_label_serializer,
            mock_annotator_serializer,
        )
        insert_annotations_data([make_annotation_entry(annotator_name="NewGuy")], uuid.uuid4())
        mock_get_annotator.objects.get_or_create.assert_called_once_with(name="NewGuy")

    @patch("api.utils.annotations_ingest.Image")
    def test_error_message_includes_row_number(self, mock_get_image: Mock) -> None:
        """Test that row numbers in error messages are 1-indexed."""
        mock_get_image.objects.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as ctx:
            insert_annotations_data([make_annotation_entry()], uuid.uuid4())

        self.assertIn("Row 1", str(ctx.exception))


class IngestAnnotationDataTests(TestCase):
    """Test for ingesting combined annotation set metadata, annotation data and labels."""

    @patch("api.utils.annotations_ingest.insert_annotations_set")
    @patch("api.utils.annotations_ingest.insert_label_data")
    @patch("api.utils.annotations_ingest.insert_annotations_data")
    def test_returns_combined_dict(self, mock_annos: Mock, mock_labels: Mock, mock_set: Mock) -> None:
        """Test that results of all three inserts are returned."""
        annotation_set_id = uuid.uuid4()
        mock_set.return_value = {"id": str(annotation_set_id), "name": "Test Set"}
        mock_labels.return_value = [{"name": "fish"}]
        mock_annos.return_value = {"created": 2, "data": [{}, {}]}

        result = ingest_annotation_data(
            annotation_set_df=make_annotation_set_data(),
            label_list=make_label_list(),
            annotation_data=[make_annotation_entry(), make_annotation_entry()],
        )

        self.assertIn("annotation_set", result)
        self.assertIn("label_set", result)
        self.assertIn("annotation_data", result)
        self.assertEqual(result["annotation_data"]["created"], 2)

    @patch("api.utils.annotations_ingest.insert_annotations_set")
    @patch("api.utils.annotations_ingest.insert_label_data")
    @patch("api.utils.annotations_ingest.insert_annotations_data")
    def test_annotation_set_id_forwarded_to_label_and_annotation_inserts(
        self, mock_annos: Mock, mock_labels: Mock, mock_set: Mock
    ) -> None:
        """Test that newly created annotation set ID is passed to label and annotation data insert operations."""
        annotation_set_id = uuid.uuid4()
        mock_set.return_value = {"id": str(annotation_set_id)}
        mock_labels.return_value = []
        mock_annos.return_value = {"created": 0, "data": []}

        ingest_annotation_data(
            annotation_set_df={},
            label_list=[],
            annotation_data=[],
        )

        mock_labels.assert_called_once_with([], str(annotation_set_id))
        mock_annos.assert_called_once_with([], str(annotation_set_id))

    @patch("api.utils.annotations_ingest.insert_annotations_set")
    @patch("api.utils.annotations_ingest.insert_label_data")
    def test_transaction_rolls_back_on_failure(self, mock_labels: Mock, mock_set: Mock) -> None:
        """Test that transaction is rolled back if a sub-call raises."""
        mock_set.return_value = {"id": str(uuid.uuid4())}
        mock_labels.side_effect = ValueError("DB exploded")

        with self.assertRaises(ValueError):
            ingest_annotation_data(
                annotation_set_df={},
                label_list=[],
                annotation_data=[],
            )

    @patch("api.utils.annotations_ingest.insert_annotations_set")
    @patch("api.utils.annotations_ingest.insert_label_data")
    @patch("api.utils.annotations_ingest.insert_annotations_data")
    def test_empty_inputs_do_not_raise(self, mock_annos: Mock, mock_labels: Mock, mock_set: Mock) -> None:
        """Test that empty inputs do not raise a ValueError."""
        mock_set.return_value = {"id": str(uuid.uuid4())}
        mock_labels.return_value = []
        mock_annos.return_value = {"created": 0, "data": []}

        result = ingest_annotation_data({}, [], [])

        self.assertEqual(result["label_set"], [])
        self.assertEqual(result["annotation_data"]["created"], 0)
