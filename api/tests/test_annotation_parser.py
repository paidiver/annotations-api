"""Unit tests for annotation parsing functions in api/util/annotation.py."""

from unittest import TestCase
from unittest.mock import patch

import numpy as np
import pandas as pd

from api.utils.annotation import parse_annodation_set_metadata, parse_annotation_data, parse_label_set


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
    def test_parse_annotation_data_from_image_spec(self, mock_parse_coords):
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
