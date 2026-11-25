"""Tests for label submission workbook parsing."""

from unittest import TestCase
from unittest.mock import Mock, patch
from uuid import UUID

import pandas as pd

from api.utils.labels_parser import parse_label_set_metadata, parse_labels

LABEL_UUID = UUID("e90a8bd7-5706-4ee0-bc9a-f36e5caf8216")


def build_label_dataframe(*rows: list[object]) -> pd.DataFrame:
    """Build a DataFrame matching the label-attributes worksheet layout."""
    return pd.DataFrame(
        [
            [
                "Attribute name",
                "label-name",
                "label-parent-name",
                "label-lowest-taxonomic-name",
                "label-lowest-AphiaID",
                "label-name-is-lowest-taxon",
                "label-identification-qualifier",
                "label-name-uuid",
            ],
            ["Allowed value(s)", "", "", "", "", "", "", ""],
            ["Description", "", "", "", "", "", "", ""],
            ["Updated requirement", "", "", "", "", "", "", ""],
            *[["", *row] for row in rows],
        ]
    )


def build_label_set_dataframe(*rows: list[object]) -> pd.DataFrame:
    """Build a DataFrame matching the label-set-attributes worksheet."""
    return pd.DataFrame(
        [
            ["Attribute name", "Value"],
            *rows,
        ]
    )


class LabelParserTests(TestCase):
    """Tests for parsing label-attributes worksheets."""

    def test_parse_labels_returns_cleaned_label_records(self) -> None:
        """Parse valid label rows and clean their values."""
        dataframe = build_label_dataframe(
            [
                " ACT000 ",
                "",
                " Actiniaria ",
                1360.0,
                " Yes ",
                "",
                str(LABEL_UUID),
            ],
            [
                "ACT009",
                " ACT000 ",
                "Actiniaria",
                "1360",
                "No",
                " suborder.indet.009 ",
                "",
            ],
            ["", "", "", "", "", "", ""],
        )

        result = parse_labels(dataframe)

        self.assertEqual(
            result,
            [
                {
                    "id": LABEL_UUID,
                    "name": "ACT000",
                    "parent_label_name": None,
                    "lowest_taxonomic_name": "Actiniaria",
                    "lowest_aphia_id": 1360,
                    "name_is_lowest": True,
                    "identification_qualifier": None,
                },
                {
                    "id": None,
                    "name": "ACT009",
                    "parent_label_name": "ACT000",
                    "lowest_taxonomic_name": "Actiniaria",
                    "lowest_aphia_id": 1360,
                    "name_is_lowest": False,
                    "identification_qualifier": "suborder.indet.009",
                },
            ],
        )

    def test_parse_labels_rejects_non_empty_row_without_name(self) -> None:
        """Reject a populated row that has no label name."""
        dataframe = build_label_dataframe(
            ["", "Parent label", "", "", "", "", ""],
        )

        with self.assertRaisesRegex(
            ValueError,
            "Validation error at row 5: label-name is required",
        ):
            parse_labels(dataframe)

    def test_parse_labels_rejects_duplicate_names_after_cleaning(self) -> None:
        """Reject duplicate label names within the same workbook."""
        dataframe = build_label_dataframe(
            ["ACT000", "", "", "", "", "", ""],
            [" ACT000 ", "", "", "", "", "", ""],
        )

        with self.assertRaisesRegex(
            ValueError,
            "Validation error at row 6: duplicate label-name 'ACT000'",
        ):
            parse_labels(dataframe)

    def test_parse_labels_rejects_invalid_aphia_id(self) -> None:
        """Reject Aphia IDs that are not whole numbers."""
        for invalid_value in ["not-an-integer", 10.5]:
            with self.subTest(invalid_value=invalid_value):
                dataframe = build_label_dataframe(
                    ["ACT000", "", "", invalid_value, "", "", ""],
                )

                with self.assertRaisesRegex(
                    ValueError,
                    "label-lowest-AphiaID must be an integer",
                ):
                    parse_labels(dataframe)

    def test_parse_labels_rejects_invalid_boolean(self) -> None:
        """Reject unsupported name-is-lowest values."""
        dataframe = build_label_dataframe(
            ["ACT000", "", "", "", "Sometimes", "", ""],
        )

        with self.assertRaisesRegex(
            ValueError,
            "must be Yes, No, True or False",
        ):
            parse_labels(dataframe)

    def test_parse_labels_rejects_invalid_uuid(self) -> None:
        """Reject malformed label UUIDs."""
        dataframe = build_label_dataframe(
            ["ACT000", "", "", "", "", "", "not-a-uuid"],
        )

        with self.assertRaisesRegex(
            ValueError,
            "label-name-uuid must be a valid UUID",
        ):
            parse_labels(dataframe)

    def test_parse_labels_rejects_worksheet_without_labels(self) -> None:
        """Reject a worksheet containing no label records."""
        dataframe = build_label_dataframe(
            ["", "", "", "", "", "", ""],
        )

        with self.assertRaisesRegex(
            ValueError,
            "No labels were found in the label-attributes worksheet",
        ):
            parse_labels(dataframe)


class LabelSetMetadataParserTests(TestCase):
    """Tests for parsing label-set metadata."""

    def build_required_rows(self) -> list[list[object]]:
        """Return the required label-set metadata rows."""
        return [
            ["label-set-name", "Test label set"],
            ["label-set-abstract", "Test abstract"],
            ["label-set-objective", "Test objective"],
            ["label-set-creators", "Alice Example, Bob Example"],
            [
                "",
                "https://orcid.org/0000-0001, " "https://orcid.org/0000-0002",
            ],
            ["label-set-pi", "Pat Investigator"],
            ["", "https://orcid.org/0000-0003"],
            ["label-set-license", "CC-BY"],
            ["", "https://creativecommons.org/licenses/by/4.0/"],
            ["label-set-uuid", str(LABEL_UUID)],
            ["label-set-funding", "Test funding"],
        ]

    def test_parse_label_set_metadata_returns_serializer_payload(self) -> None:
        """Parse metadata into its UUID and serializer payload."""
        dataframe = build_label_set_dataframe(
            ["label-set-template-version", "3"],
            ["label-set-name", "Test label set"],
            ["label-set-project", "Test project"],
            ["", "https://example.com/project"],
            ["label-set-context", "Test cruise"],
            ["", "https://example.com/context"],
            ["label-set-abstract", "Test abstract"],
            ["label-set-objective", "Test objective"],
            ["label-set-creators", "Alice Example, Bob Example"],
            [
                "",
                "https://orcid.org/0000-0001, " "https://orcid.org/0000-0002",
            ],
            ["label-set-pi", "Pat Investigator"],
            ["", "https://orcid.org/0000-0003"],
            ["label-set-license", "CC-BY"],
            ["", "https://creativecommons.org/licenses/by/4.0/"],
            ["label-set-copyright", "Test copyright"],
            ["label-set-uuid", str(LABEL_UUID)],
            [
                "label-set-related-material",
                "https://example.com/a, https://example.com/b",
            ],
            ["label-set-handle", "https://example.com/label-set"],
            ["label-set-catalogue", "https://example.com/catalogue"],
            ["label-set-funding", "Test funding"],
        )

        label_set_id, payload = parse_label_set_metadata(dataframe)

        self.assertEqual(label_set_id, LABEL_UUID)
        self.assertEqual(payload["name"], "Test label set")
        self.assertEqual(payload["abstract"], "Test abstract")
        self.assertEqual(payload["objective"], "Test objective")
        self.assertEqual(payload["funding"], "Test funding")
        self.assertEqual(payload["handle"], "https://example.com/label-set")
        self.assertEqual(payload["copyright"], "Test copyright")
        self.assertEqual(
            payload["catalogue"],
            "https://example.com/catalogue",
        )

        self.assertEqual(
            payload["project"],
            {
                "name": "Test project",
                "uri": "https://example.com/project",
            },
        )
        self.assertEqual(
            payload["context"],
            {
                "name": "Test cruise",
                "uri": "https://example.com/context",
            },
        )
        self.assertEqual(
            payload["creators"],
            [
                {
                    "name": "Alice Example",
                    "uri": "https://orcid.org/0000-0001",
                },
                {
                    "name": "Bob Example",
                    "uri": "https://orcid.org/0000-0002",
                },
            ],
        )
        self.assertEqual(
            payload["pi"],
            {
                "name": "Pat Investigator",
                "uri": "https://orcid.org/0000-0003",
            },
        )
        self.assertEqual(
            payload["license"],
            {
                "name": "CC-BY",
                "uri": "https://creativecommons.org/licenses/by/4.0/",
            },
        )
        self.assertEqual(
            payload["related_materials"],
            [
                {"uri": "https://example.com/a"},
                {"uri": "https://example.com/b"},
            ],
        )
        self.assertNotIn("label-set-template-version", payload)

    def test_parse_label_set_metadata_allows_missing_optional_values(self) -> None:
        """Allow omitted optional relationships and creator URIs."""
        rows = self.build_required_rows()
        rows[4] = ["", ""]
        dataframe = build_label_set_dataframe(*rows)

        _, payload = parse_label_set_metadata(dataframe)

        self.assertEqual(
            payload["creators"],
            [
                {"name": "Alice Example", "uri": None},
                {"name": "Bob Example", "uri": None},
            ],
        )
        self.assertNotIn("project", payload)
        self.assertNotIn("context", payload)
        self.assertNotIn("related_materials", payload)
        self.assertNotIn("handle", payload)
        self.assertNotIn("copyright", payload)
        self.assertNotIn("catalogue", payload)

    def test_parse_label_set_metadata_rejects_missing_required_value(self) -> None:
        """Reject missing required metadata."""
        rows = self.build_required_rows()
        rows[0] = ["label-set-name", ""]
        dataframe = build_label_set_dataframe(*rows)

        with self.assertRaisesRegex(
            ValueError,
            "Missing required label-set metadata: label-set-name",
        ):
            parse_label_set_metadata(dataframe)

    def test_parse_label_set_metadata_rejects_mismatched_creator_uris(self) -> None:
        """Require one URI for each creator when URIs are supplied."""
        rows = self.build_required_rows()
        rows[4] = ["", "https://orcid.org/0000-0001"]
        dataframe = build_label_set_dataframe(*rows)

        with self.assertRaisesRegex(
            ValueError,
            "number of label-set creator URIs must match",
        ):
            parse_label_set_metadata(dataframe)

    def test_parse_label_set_metadata_rejects_multiple_pi_uris(self) -> None:
        """Reject more than one URI for the PI."""
        rows = self.build_required_rows()
        rows[6] = [
            "",
            "https://orcid.org/0000-0003, investigator@example.com",
        ]
        dataframe = build_label_set_dataframe(*rows)

        with self.assertRaisesRegex(
            ValueError,
            "label-set-pi must have no more than one URI",
        ):
            parse_label_set_metadata(dataframe)

    def test_parse_label_set_metadata_rejects_uri_without_name(self) -> None:
        """Reject a related-object URI that has no corresponding name."""
        rows = self.build_required_rows()
        rows.extend(
            [
                ["label-set-project", ""],
                ["", "https://example.com/project"],
            ]
        )
        dataframe = build_label_set_dataframe(*rows)

        with self.assertRaisesRegex(
            ValueError,
            "label-set-project has a URI but no corresponding name",
        ):
            parse_label_set_metadata(dataframe)

    @patch("api.utils.labels_parser._parse_optional_uuid", return_value=None)
    def test_parse_label_set_metadata_defensively_rejects_missing_uuid(
        self,
        mock_parse_optional_uuid: Mock,
    ) -> None:
        """Retain the defensive check if UUID parsing returns None."""
        dataframe = build_label_set_dataframe(*self.build_required_rows())

        with self.assertRaisesRegex(
            ValueError,
            "label-set-uuid is required",
        ):
            parse_label_set_metadata(dataframe)
