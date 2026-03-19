"""Unit tests for annotation parsing functions in api/util/annotation.py."""

from unittest import TestCase
from unittest.mock import patch

import numpy as np
import pandas as pd
from django.test import TransactionTestCase

from api.utils.annotation import (
    _parse_coordinates,
    ingest_annotation_data,
    parse_annodation_set_metadata,
    parse_annotation_data,
    parse_label_set,
)


class TestAnnotationParsers(TestCase):
    """Parsing tests for annotation."""

    def test_parse_annotation_set_metadata_success(self):
        """Test parsing metadata with merged-cell style."""
        # Col 0: iFDO fields, Col 1: subfields, Col 2: Value
        data = [
            ["annotation-set-name", np.nan, "Trial Data"],
            ["annotation-project", "name", "Trial Data"],
            [np.nan, "uri", "http://example.com"],
            ["annotation-context", "name", "Trial Data"],
            [np.nan, "uri", np.nan],
            ["annotation-abstract", np.nan, "Trial Data"],
            ["annotation-pi", "name", "Test User"],
            [np.nan, "uri", "user@example.com"],
        ]
        df = pd.DataFrame(data)

        mock_keys = [
            "annotation-set-name",
            "annotation-project-name",
            "annotation-project-uri",
            "annotation-context-name",
            "annotation-pi-name",
            "annotation-pi-uri",
            "annotation-abstract",
        ]

        with patch("api.utils.annotation.ANNOTATION_METADATA_KEYS", mock_keys):
            result = parse_annodation_set_metadata(df)

        self.assertEqual(result["annotation-set-name"], "Trial Data")
        self.assertEqual(result["annotation-project-name"], "Trial Data")
        self.assertEqual(result["annotation-project-uri"], "http://example.com")
        self.assertEqual(result["annotation-pi-uri"], "user@example.com")

        # Ensure that keys with no value are NOT in the dict
        self.assertNotIn("annotation-context-uri", result)

    def test_parse_label_set(self):
        """Test parsing label set."""
        data = [
            [
                "Field",
                "label_name",
                "parent_label_name",
                "lowest_taxonomic_name",
                "lowest_AphiaID",
                "label_name_is_lowest",
                "identificationQualifier",
            ],  # noqa: E501
            ["Expected value", "Text", "Text", "Text", "Integer", "Yes, No", "Text"],
            [
                "Explanation",
                "name of label",
                "name of parent",
                "Most detailed",
                "AphiaID",
                "If No...",
                "Open nomenclature",
            ],  # noqa: E501
            ["Value", "antedon", "Echinodermata", "Antedon", 123349, "Yes", "sp.indet."],
            [np.nan, "anthozoa_34", "Cnidaria", "Anthozoa", 1292, "No", "class indet.34"],
            [np.nan, "coarse", "habitat", np.nan, np.nan, np.nan, np.nan],
            [np.nan, " ", " ", " ", " ", " ", " "],
        ]

        df = pd.DataFrame(data)

        result = parse_label_set(df)

        self.assertEqual(len(result), 3)

        self.assertEqual(result[0]["name"], "antedon")
        self.assertEqual(result[0]["is_lowest"], True)
        self.assertEqual(result[0]["lowest_aphia_id"], 123349)
        self.assertEqual(result[0]["identification_qualifier"], "sp.indet.")

        self.assertEqual(result[1]["name"], "anthozoa_34")
        self.assertEqual(result[1]["is_lowest"], False)

        self.assertEqual(result[2]["name"], "coarse")
        self.assertEqual(result[2]["parent_label_name"], "habitat")

    @patch("api.utils.annotation._parse_coordinates")
    def test_parse_annotation_data(self, mock_parse_coords):
        """Test parsing the main annotation data sheet based on image structure."""
        mock_parse_coords.return_value = [1427, 8163]

        data = [
            [
                "image-uuid",
                "annotation-platform",
                "image-filename",
                "annotation-human-creator",
                "annotation-creation-datetime",
                "annotation-label-name",
                "annotation-shape-name",
                "annotation-coordinates",
                "annotation-dimension-pixels",
            ],
            ["", "", "", "", "", "", "", "", ""],  # Grey info rows
            ["", "", "", "", "", "", "", "", ""],  # Grey info rows
            [
                "0c3bc9cd",
                "ImagePro",
                "M58_1044.jpg",
                "Noelie Benoist",
                "31122012",
                "reteporella",
                "rectangle",
                "1427,8163",
                5850,
            ],
            [
                np.nan,
                "ImagePro",
                "M58_1044.jpg",
                "Noelie Benoist",
                "31122012",
                "bryozoa_01",
                "rectangle",
                "1731,8308",
                384.06,
            ],
            [np.nan, "", "", "", "", "", "", "", ""],  # Empty row to test skipping
        ]

        df = pd.DataFrame(data)

        with (
            patch("api.utils.annotation.ANNOTATION_DATA_START_ROW", 3),
            patch("api.utils.annotation.ANNOTATION_DATA_START_COL", 0),
            patch("api.utils.annotation.ANNOTATION_DATA_END_COL", 9),
        ):
            result = parse_annotation_data(df)

        self.assertEqual(len(result), 2)

        self.assertEqual(result[0]["image_id"], "0c3bc9cd")
        self.assertEqual(result[0]["image_filename"], "M58_1044.jpg")
        self.assertEqual(result[0]["dimension_pixels"], 5850.0)

        self.assertEqual(result[1]["image_id"], "")
        self.assertEqual(result[1]["label_name"], "bryozoa_01")
        self.assertEqual(result[1]["dimension_pixels"], 384.06)

        self.assertTrue(mock_parse_coords.called)


class TestParseCoordinates(TestCase):
    """Test for parsing coordinates."""

    def test_parse_comma_separated_string(self):
        """Test standard 'x, y' string format."""
        input_val = "1427.5, 8163.2"
        expected = [[1427.5, 8163.2]]
        self.assertEqual(_parse_coordinates(input_val), expected)

    def test_parse_json_list_format(self):
        """Test if it handles stringified JSON lists (common in some exports)."""
        input_val = "[10, 20, 30, 40]"
        expected = [10, 20, 30, 40]
        self.assertEqual(_parse_coordinates(input_val), expected)

    def test_parse_empty_or_nan(self):
        """Test that empty inputs return an empty list."""
        self.assertEqual(_parse_coordinates(""), [])
        self.assertEqual(_parse_coordinates(None), [])


class TestIngestAnnotationData(TransactionTestCase):
    """Test class for testing data ingestion."""

    @patch("api.utils.annotation.insert_annotations_into_tables")
    @patch("api.utils.annotation.insert_label_data")
    @patch("api.utils.annotation.insert_annotations_data")
    def test_ingest_annotation_data_success(self, mock_insert_annot, mock_insert_label, mock_insert_set):
        """Test the orchestration of the ingestion process."""
        mock_insert_set.return_value = {"id": 1, "name": "Test Set"}
        mock_insert_label.return_value = [{"id": 10, "name": "Coral"}]
        mock_insert_annot.return_value = [{"id": 100, "image_id": "ABC"}]

        annotation_set_df = {"name": "Test Set"}
        label_list = [{"name": "Coral"}]
        annot_list = [{"image_id": "ABC"}]

        result = ingest_annotation_data(annotation_set_df, label_list, annot_list)

        mock_insert_set.assert_called_once_with(annotation_set_df)
        mock_insert_label.assert_called_once_with(label_list, 1)
        mock_insert_annot.assert_called_once_with(annot_list, 1)

        self.assertEqual(result["annotation_set"]["id"], 1)
        self.assertEqual(len(result["label_set"]), 1)
