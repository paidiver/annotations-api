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
            "annotation-abstract"
        ]

        with patch('api.utils.annotation.ANNOTATION_METADATA_KEYS', mock_keys):
            result = parse_annodation_set_metadata(df)

        self.assertEqual(result["annotation-set-name"], "Trial Data")
        self.assertEqual(result["annotation-project-name"], "Trial Data")
        self.assertEqual(result["annotation-project-uri"], "http://example.com")
        self.assertEqual(result["annotation-pi-uri"], "user@example.com")

        # Ensure that keys with no value are NOT in the dict
        self.assertNotIn("annotation-context-uri", result)
