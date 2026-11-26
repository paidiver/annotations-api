"""Unit tests for annotation parsing functions in api/util/annotation.py."""

from unittest import TestCase
from uuid import UUID

import pandas as pd

from api.utils.annotations_parser import (
    SpreadsheetValue,
    parse_annotation_data,
    parse_annotation_models,
    parse_annotation_set_metadata,
)


class TestAnnotationParsers(TestCase):
    """Parsing tests for annotation."""

    mock_keys = [
        "annotation-set-name",
        "annotation-project-name",
        "annotation-project-uri",
        "annotation-license-name",
        "annotation-image-set-name",
        "annotation-image-set-uuid",
        "annotation-pi-name",
        "annotation-pi-uri",
        "annotation-abstract",
    ]


ANNOTATION_SET_ID = UUID("733b90be-1539-4ba2-8aeb-41a4aa2d1507")
IMAGE_SET_ID = UUID("36a6eb08-cd1d-4cb4-a24b-f6ff7a380ac3")
LABEL_SET_ID = UUID("1b6bbe2c-6ea2-4d36-927a-7544f2156336")
CONNECTED_SET_ID = UUID("72569b9f-d527-4381-9b69-c10615adc6e1")
ANNOTATION_ID = UUID("b52d0f14-cc91-4059-9538-e02cc48e7824")
IMAGE_ID = UUID("81f3f807-3bed-4b45-8d28-8d413f746af9")


def make_annotation_set_dataframe() -> pd.DataFrame:
    """Create annotation-set metadata using the v3 worksheet structure."""
    return pd.DataFrame(
        [
            ["Attribute name", "Value"],
            ["annotation-set-template-version", "3"],
            ["annotation-set-name", "Test annotations"],
            ["annotation-set-project", "Test project"],
            [None, "https://example.com/projects/test"],
            ["annotation-set-context", "Test survey"],
            [None, "https://example.com/surveys/test"],
            ["annotation-set-abstract", "Test annotation-set abstract"],
            ["annotation-set-objective", "Test annotation-set objective"],
            ["annotation-set-creators", "Alice Example, Bob Example"],
            [
                None,
                "https://orcid.org/0000-0001-0000-0001, " "https://orcid.org/0000-0002-0000-0002",
            ],
            ["annotation-set-pi", "Pat Example"],
            [None, "https://orcid.org/0000-0003-0000-0003"],
            ["annotation-set-license", "CC-BY"],
            [None, "https://creativecommons.org/licenses/by/4.0/"],
            ["annotation-set-copyright", "Test copyright"],
            ["annotation-set-uuid", str(ANNOTATION_SET_ID)],
            ["annotation-set-handle", "https://example.com/annotation-sets/test"],
            ["annotation-set-image-set-name", "Test image set"],
            ["annotation-set-image-set-UUIDs", str(IMAGE_SET_ID)],
            [
                "annotation-set-image-set-handles",
                "https://example.com/image-sets/test",
            ],
            ["annotation-set-label-set-names", "Test label set"],
            ["annotation-set-label-set-UUIDs", str(LABEL_SET_ID)],
            ["annotation-set-connected-set-UUIDs", str(CONNECTED_SET_ID)],
            ["annotation-set-machine-scope", "Human annotations only"],
            [
                "annotation-set-related-material",
                "https://doi.org/10.1234/example",
            ],
            ["annotation-set-quantitative-or-qualitative", "Quantitative"],
            ["annotation-set-quantification-type", "Count"],
            ["annotation-set-biological-metrics", "Abundance"],
            ["annotation-set-biological-stats", "Comparison by survey"],
            [
                "annotation-set-OBIS-handles",
                "https://example.com/obis/test",
            ],
            ["annotation-set-funding", "Test funding"],
        ]
    )


def set_metadata_value(
    dataframe: pd.DataFrame,
    field_name: str,
    value: SpreadsheetValue,
) -> None:
    """Replace a primary metadata value in a test dataframe."""
    row_index = dataframe.index[dataframe.iloc[:, 0] == field_name][0]
    dataframe.iloc[row_index, 1] = value


def set_paired_metadata_value(
    dataframe: pd.DataFrame,
    field_name: str,
    value: SpreadsheetValue,
) -> None:
    """Replace the paired URI row immediately following a metadata field."""
    row_index = dataframe.index[dataframe.iloc[:, 0] == field_name][0]
    dataframe.iloc[row_index + 1, 1] = value


class AnnotationSetMetadataParserTests(TestCase):
    """Tests for parsing v3 annotation-set metadata."""

    def test_returns_serializer_payload_and_references(self) -> None:
        """Parse metadata into its UUID, serializer payload and references."""
        dataframe = make_annotation_set_dataframe()

        annotation_set_id, payload, references = parse_annotation_set_metadata(dataframe)

        self.assertEqual(annotation_set_id, ANNOTATION_SET_ID)
        self.assertEqual(payload["name"], "Test annotations")
        self.assertEqual(payload["project"]["name"], "Test project")
        self.assertEqual(
            payload["project"]["uri"],
            "https://example.com/projects/test",
        )
        self.assertEqual(
            payload["creators"],
            [
                {
                    "name": "Alice Example",
                    "uri": "https://orcid.org/0000-0001-0000-0001",
                },
                {
                    "name": "Bob Example",
                    "uri": "https://orcid.org/0000-0002-0000-0002",
                },
            ],
        )
        self.assertEqual(payload["quantitative_or_qualitative"], ["quantitative"])
        self.assertEqual(payload["quantification_type"], ["count"])
        self.assertEqual(
            payload["connected_set_ids"],
            [CONNECTED_SET_ID],
        )
        self.assertEqual(
            payload["related_materials"],
            [{"uri": "https://doi.org/10.1234/example"}],
        )

        self.assertEqual(references["image_set_names"], ["Test image set"])
        self.assertEqual(references["image_set_ids"], [IMAGE_SET_ID])
        self.assertEqual(references["label_set_names"], ["Test label set"])
        self.assertEqual(references["label_set_ids"], [LABEL_SET_ID])

    def test_parses_multiple_quantification_choices(self) -> None:
        """Parse comma-separated quantification choices into arrays."""
        dataframe = make_annotation_set_dataframe()
        set_metadata_value(
            dataframe,
            "annotation-set-quantitative-or-qualitative",
            "Qualitative, Quantitative",
        )
        set_metadata_value(
            dataframe,
            "annotation-set-quantification-type",
            "Presence, Absence, Count",
        )

        _, payload, _ = parse_annotation_set_metadata(dataframe)

        self.assertEqual(payload["quantitative_or_qualitative"], ["qualitative", "quantitative"])
        self.assertEqual(payload["quantification_type"], ["presence", "absence", "count"])

    def test_allows_image_set_uuid_to_be_omitted(self) -> None:
        """Allow image sets to be resolved by their required names."""
        dataframe = make_annotation_set_dataframe()
        set_metadata_value(
            dataframe,
            "annotation-set-image-set-UUIDs",
            None,
        )

        _, _, references = parse_annotation_set_metadata(dataframe)

        self.assertEqual(references["image_set_names"], ["Test image set"])
        self.assertEqual(references["image_set_ids"], [])

    def test_allows_image_set_uuid_without_name(self) -> None:
        """Allow image sets to be resolved by UUID without a name."""
        dataframe = make_annotation_set_dataframe()
        set_metadata_value(dataframe, "annotation-set-image-set-name", None)
        set_metadata_value(dataframe, "annotation-set-image-set-handles", None)

        _, _, references = parse_annotation_set_metadata(dataframe)

        self.assertEqual(references["image_set_names"], [])
        self.assertEqual(references["image_set_ids"], [IMAGE_SET_ID])

    def test_allows_empty_image_set_references_and_generates_uuid(self) -> None:
        """Allow empty image-set references and generate a UUID."""
        dataframe = make_annotation_set_dataframe()
        set_metadata_value(dataframe, "annotation-set-uuid", None)
        set_metadata_value(dataframe, "annotation-set-image-set-name", None)
        set_metadata_value(dataframe, "annotation-set-image-set-UUIDs", None)
        set_metadata_value(dataframe, "annotation-set-image-set-handles", None)

        annotation_set_id, _, references = parse_annotation_set_metadata(dataframe)

        self.assertIsInstance(annotation_set_id, UUID)
        self.assertNotEqual(annotation_set_id, ANNOTATION_SET_ID)
        self.assertEqual(references["image_set_names"], [])
        self.assertEqual(references["image_set_ids"], [])

    def test_allows_image_set_handle_without_name_or_uuid(self) -> None:
        """Allow an external image-set handle without database identifiers."""
        dataframe = make_annotation_set_dataframe()
        set_metadata_value(dataframe, "annotation-set-image-set-name", None)
        set_metadata_value(dataframe, "annotation-set-image-set-UUIDs", None)

        _, _, references = parse_annotation_set_metadata(dataframe)

        self.assertEqual(references["image_set_names"], [])
        self.assertEqual(references["image_set_ids"], [])
        self.assertEqual(references["image_set_handles"], ["https://example.com/image-sets/test"])

    def test_rejects_empty_annotation_set_funding(self) -> None:
        """Require funding metadata for annotation-set ingestion."""
        dataframe = make_annotation_set_dataframe()
        set_metadata_value(dataframe, "annotation-set-funding", None)

        with self.assertRaisesRegex(ValueError, "annotation-set-funding"):
            parse_annotation_set_metadata(dataframe)

    def test_rejects_missing_required_metadata(self) -> None:
        """Reject a missing required annotation-set field."""
        dataframe = make_annotation_set_dataframe()
        set_metadata_value(dataframe, "annotation-set-name", None)

        with self.assertRaisesRegex(
            ValueError,
            "annotation-set-name",
        ):
            parse_annotation_set_metadata(dataframe)

    def test_rejects_invalid_annotation_set_uuid(self) -> None:
        """Reject an invalid annotation-set UUID."""
        dataframe = make_annotation_set_dataframe()
        set_metadata_value(
            dataframe,
            "annotation-set-uuid",
            "not-a-uuid",
        )

        with self.assertRaisesRegex(
            ValueError,
            "annotation-set-uuid must be a valid UUID",
        ):
            parse_annotation_set_metadata(dataframe)

    def test_rejects_mismatched_creator_uris(self) -> None:
        """Require one URI per creator when creator URIs are supplied."""
        dataframe = make_annotation_set_dataframe()
        set_paired_metadata_value(
            dataframe,
            "annotation-set-creators",
            "https://orcid.org/0000-0001-0000-0001",
        )

        with self.assertRaisesRegex(
            ValueError,
            "creator URIs must match",
        ):
            parse_annotation_set_metadata(dataframe)

    def test_rejects_mismatched_label_set_references(self) -> None:
        """Require one label-set UUID for every label-set name."""
        dataframe = make_annotation_set_dataframe()
        set_metadata_value(
            dataframe,
            "annotation-set-label-set-names",
            "First label set, Second label set",
        )

        with self.assertRaisesRegex(
            ValueError,
            "label-set UUIDs must match",
        ):
            parse_annotation_set_metadata(dataframe)

    def test_rejects_multiple_pi_uris(self) -> None:
        """Reject more than one URI for the annotation-set PI."""
        dataframe = make_annotation_set_dataframe()
        set_paired_metadata_value(
            dataframe,
            "annotation-set-pi",
            "https://example.com/pi/one, https://example.com/pi/two",
        )

        with self.assertRaisesRegex(
            ValueError,
            "pi must have no more than one URI",
        ):
            parse_annotation_set_metadata(dataframe)


def make_annotation_model_row() -> list[SpreadsheetValue]:
    """Create one valid annotation-model worksheet row."""
    return [
        None,
        "detector-1",
        "Test detector",
        "1.0",
        "Detection",
        "https://example.com/models/detector-1",
        "a" * 64,
        "Test model description",
        "objectness",
        0.75,
        str(LABEL_SET_ID),
        "https://example.com/training/images",
        "https://example.com/training/annotations",
        "https://example.com/validation/images",
        "https://example.com/validation/annotations",
    ]


def make_annotation_models_dataframe(
    model_rows: list[list[SpreadsheetValue]] | None = None,
) -> pd.DataFrame:
    """Create a v3 annotation-model worksheet."""
    header = [
        "Attribute name",
        "annotation-model-id",
        "annotation-model-name",
        "annotation-model-version",
        "annotation-model-task",
        "annotation-model-handle",
        "annotation-model-weights-sha256",
        "annotation-model-description",
        "annotation-model-score-type",
        "annotation-model-confidence-threshold",
        "annotation-model-label-set-uuid",
        "annotation-model-training-image-set",
        "annotation-model-training-annotation-set",
        "annotation-model-validation-image-set",
        "annotation-model-validation-annotation-set",
    ]

    return pd.DataFrame(
        [
            header,
            ["Allowed values", *([None] * 14)],
            ["Description", *([None] * 14)],
            ["Usage", *([None] * 14)],
            *(model_rows or []),
        ]
    )


class AnnotationModelParserTests(TestCase):
    """Tests for parsing annotation-set model records."""

    def test_returns_serializer_payloads(self) -> None:
        """Parse valid model rows into serializer payloads."""
        dataframe = make_annotation_models_dataframe([make_annotation_model_row()])

        result = parse_annotation_models(dataframe)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["model_id"], "detector-1")
        self.assertEqual(result[0]["name"], "Test detector")
        self.assertEqual(result[0]["version"], "1.0")
        self.assertEqual(result[0]["task"], "detection")
        self.assertEqual(result[0]["confidence_threshold"], 0.75)
        self.assertEqual(result[0]["label_set_id"], LABEL_SET_ID)
        self.assertEqual(result[0]["weights_sha256"], "a" * 64)

    def test_returns_empty_list_when_no_models_are_supplied(self) -> None:
        """Allow annotation sets that do not use machine models."""
        dataframe = make_annotation_models_dataframe()

        self.assertEqual(parse_annotation_models(dataframe), [])

    def test_rejects_missing_required_model_field(self) -> None:
        """Reject a populated model row missing a required value."""
        row = make_annotation_model_row()
        row[2] = None
        dataframe = make_annotation_models_dataframe([row])

        with self.assertRaisesRegex(
            ValueError,
            "annotation-model-name",
        ):
            parse_annotation_models(dataframe)

    def test_rejects_duplicate_model_ids(self) -> None:
        """Reject duplicate model identifiers within an annotation set."""
        first_row = make_annotation_model_row()
        second_row = make_annotation_model_row()
        second_row[2] = "Another detector"

        dataframe = make_annotation_models_dataframe([first_row, second_row])

        with self.assertRaisesRegex(
            ValueError,
            "duplicate annotation-model-id 'detector-1'",
        ):
            parse_annotation_models(dataframe)

    def test_rejects_non_numeric_confidence_threshold(self) -> None:
        """Reject a confidence threshold that is not numeric."""
        row = make_annotation_model_row()
        row[9] = "high"
        dataframe = make_annotation_models_dataframe([row])

        with self.assertRaisesRegex(
            ValueError,
            "confidence-threshold must be a number",
        ):
            parse_annotation_models(dataframe)

    def test_rejects_confidence_threshold_outside_range(self) -> None:
        """Reject a confidence threshold outside zero through one."""
        row = make_annotation_model_row()
        row[9] = 1.5
        dataframe = make_annotation_models_dataframe([row])

        with self.assertRaisesRegex(
            ValueError,
            "confidence-threshold must be between 0 and 1",
        ):
            parse_annotation_models(dataframe)

    def test_rejects_invalid_label_set_uuid(self) -> None:
        """Reject a malformed model label-set UUID."""
        row = make_annotation_model_row()
        row[10] = "not-a-uuid"
        dataframe = make_annotation_models_dataframe([row])

        with self.assertRaisesRegex(
            ValueError,
            "annotation-model-label-set-uuid must be a valid UUID",
        ):
            parse_annotation_models(dataframe)


def make_annotation_row() -> list[SpreadsheetValue]:
    """Create one valid human-created annotation row."""
    return [
        None,
        str(ANNOTATION_ID),
        "test-image.jpg",
        str(IMAGE_ID),
        "Human",
        "Alice Example",
        "https://orcid.org/0000-0001-0000-0001",
        "2026-11-23T10:00:00Z",
        "test-fish",
        "Line",
        "[100, 200, 150, 250]",
        12.5,
        "None",
        None,
        None,
        "Test annotation",
        None,
        None,
        None,
        None,
        None,
    ]


def make_annotations_dataframe(
    annotation_rows: list[list[SpreadsheetValue]] | None = None,
) -> pd.DataFrame:
    """Create a v3 annotation-attributes worksheet."""
    header = [
        "Attribute name",
        "annotation-uuid",
        "image-filename",
        "image-UUID",
        "annotation-human-or-machine",
        "annotation-creator",
        None,
        "annotation-creation-datetime",
        "annotation-label-name",
        "annotation-shape-name",
        "annotation-coordinates",
        "annotation-measurement",
        "annotation-human-reviewer",
        None,
        "annotation-machine-training-validation",
        "annotation-additional-info",
        "annotation-detection-model",
        "annotation-classification-model",
        "annotation-detection-confidence",
        "annotation-classification-confidence",
        "annotation-mask",
    ]

    return pd.DataFrame(
        [
            header,
            ["Allowed values", *([None] * 20)],
            ["Description", *([None] * 20)],
            ["Usage", *([None] * 20)],
            *(annotation_rows or []),
        ]
    )


class AnnotationDataParserTests(TestCase):
    """Tests for parsing v3 annotation records."""

    def test_returns_annotation_payloads(self) -> None:
        """Parse a valid human-created annotation."""
        dataframe = make_annotations_dataframe([make_annotation_row()])

        result = parse_annotation_data(dataframe)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], ANNOTATION_ID)
        self.assertEqual(result[0]["image_id"], IMAGE_ID)
        self.assertEqual(result[0]["image_filename"], "test-image.jpg")
        self.assertEqual(result[0]["human_or_machine"], "human")
        self.assertEqual(result[0]["label_name"], "test-fish")
        self.assertEqual(result[0]["shape"], "line")
        self.assertEqual(
            result[0]["coordinates"],
            [100, 200, 150, 250],
        )
        self.assertEqual(result[0]["dimension_pixels"], 12.5)
        self.assertEqual(
            result[0]["creator"],
            {
                "name": "Alice Example",
                "uri": "https://orcid.org/0000-0001-0000-0001",
            },
        )
        self.assertIsNone(result[0]["human_reviewer"])

    def test_parses_algorithm_annotation(self) -> None:
        """Allow an algorithm annotation without a human creator."""
        row = make_annotation_row()
        row[4] = "Algorithm"
        row[5] = None
        row[6] = None
        row[16] = "detector-1"
        row[18] = 0.8

        result = parse_annotation_data(make_annotations_dataframe([row]))

        self.assertIsNone(result[0]["creator"])
        self.assertEqual(result[0]["detection_model_ref"], "detector-1")
        self.assertEqual(result[0]["detection_confidence"], 0.8)

    def test_allows_image_filename_without_uuid(self) -> None:
        """Allow ingestion to resolve an image by filename."""
        row = make_annotation_row()
        row[3] = None

        result = parse_annotation_data(make_annotations_dataframe([row]))

        self.assertIsNone(result[0]["image_id"])
        self.assertEqual(result[0]["image_filename"], "test-image.jpg")

    def test_rejects_empty_annotation_worksheet(self) -> None:
        """Require at least one annotation record."""
        dataframe = make_annotations_dataframe()

        with self.assertRaisesRegex(
            ValueError,
            "No annotations were found",
        ):
            parse_annotation_data(dataframe)

    def test_rejects_missing_required_annotation_field(self) -> None:
        """Reject a populated row missing a required value."""
        row = make_annotation_row()
        row[8] = None

        with self.assertRaisesRegex(
            ValueError,
            "annotation-label-name",
        ):
            parse_annotation_data(make_annotations_dataframe([row]))

    def test_rejects_missing_image_identifier(self) -> None:
        """Require an image UUID or filename."""
        row = make_annotation_row()
        row[2] = None
        row[3] = None

        with self.assertRaisesRegex(
            ValueError,
            "either image-UUID or image-filename is required",
        ):
            parse_annotation_data(make_annotations_dataframe([row]))

    def test_rejects_duplicate_annotation_uuids(self) -> None:
        """Reject repeated annotation UUIDs within a workbook."""
        first_row = make_annotation_row()
        second_row = make_annotation_row()
        second_row[8] = "another-label"

        with self.assertRaisesRegex(
            ValueError,
            "duplicate annotation-uuid",
        ):
            parse_annotation_data(make_annotations_dataframe([first_row, second_row]))

    def test_requires_creator_for_human_annotation(self) -> None:
        """Require a creator for human and combination annotations."""
        row = make_annotation_row()
        row[5] = None
        row[6] = None

        with self.assertRaisesRegex(
            ValueError,
            "annotation-creator is required",
        ):
            parse_annotation_data(make_annotations_dataframe([row]))

    def test_requires_model_for_algorithm_annotation(self) -> None:
        """Require a referenced model for algorithm annotations."""
        row = make_annotation_row()
        row[4] = "Algorithm"
        row[5] = None
        row[6] = None

        with self.assertRaisesRegex(
            ValueError,
            "requires a detection or classification model",
        ):
            parse_annotation_data(make_annotations_dataframe([row]))

    def test_rejects_invalid_coordinates(self) -> None:
        """Reject coordinates that are not numeric."""
        row = make_annotation_row()
        row[10] = '[100, "not-a-number"]'

        with self.assertRaisesRegex(
            ValueError,
            "annotation-coordinates must be a numeric array",
        ):
            parse_annotation_data(make_annotations_dataframe([row]))

    def test_requires_mask_for_mask_shape(self) -> None:
        """Require mask data when the annotation shape is mask."""
        row = make_annotation_row()
        row[9] = "Mask"
        row[10] = None

        with self.assertRaisesRegex(
            ValueError,
            "annotation-mask is required",
        ):
            parse_annotation_data(make_annotations_dataframe([row]))

    def test_parses_mask_json(self) -> None:
        """Parse a COCO RLE mask JSON object."""
        row = make_annotation_row()
        row[9] = "Mask"
        row[10] = None
        row[20] = '{"encoding": "rle", "width": 100, ' '"height": 50, "counts": "test"}'

        result = parse_annotation_data(make_annotations_dataframe([row]))

        self.assertEqual(
            result[0]["mask"],
            {
                "encoding": "rle",
                "width": 100,
                "height": 50,
                "counts": "test",
            },
        )
