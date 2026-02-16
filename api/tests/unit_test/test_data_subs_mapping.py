"""Unit tests for iFDO data_subs_mapping adapter functions."""

from datetime import UTC, datetime

from django.test import TestCase

from api.ingest.data_subs_mapping import (
    IFDOAdaptError,
    adapt_ifdo_image_set_to_serializer_payload,
    adapt_ifdo_item_to_image_serializer_payload,
)


class TestDataSubsMapping(TestCase):
    """Unit tests for api.ingest.data_subs_mapping."""

    def _base_ifdo(self, **header_overrides):
        header = {
            "image-set-name": "Set A",
            "image-set-handle": "h1",
            "image-set-min-latitude-degrees": "1.5",
            "image-particle-count": "7",
        }
        header.update(header_overrides)
        return {"image-set-header": header, "image-set-items": []}

    def test_imageset_requires_header(self):
        """Missing/empty image-set-header should raise."""
        with self.assertRaises(IFDOAdaptError) as ctx:
            adapt_ifdo_image_set_to_serializer_payload({})
        self.assertIn("ifdo.image-set-header is required", str(ctx.exception))

        with self.assertRaises(IFDOAdaptError) as ctx2:
            adapt_ifdo_image_set_to_serializer_payload({"image-set-header": {}})
        self.assertIn("ifdo.image-set-header is required", str(ctx2.exception))

    def test_imageset_requires_name_and_strips(self):
        """image-set-name must be a non-empty string and should be stripped."""
        payload = adapt_ifdo_image_set_to_serializer_payload(self._base_ifdo(**{"image-set-name": "  My Set  "}))
        self.assertEqual(payload["name"], "My Set")

        with self.assertRaises(IFDOAdaptError) as ctx:
            adapt_ifdo_image_set_to_serializer_payload(self._base_ifdo(**{"image-set-name": "   "}))
        self.assertIn("image-set-name is required", str(ctx.exception))

        with self.assertRaises(IFDOAdaptError) as ctx2:
            adapt_ifdo_image_set_to_serializer_payload(self._base_ifdo(**{"image-set-name": 123}))
        self.assertIn("must be a string", str(ctx2.exception))

    def test_imageset_converts_numbers_and_drops_none_keys(self):
        """Float/int-like strings should be converted; None values should be dropped."""
        ifdo = self._base_ifdo(
            **{
                "image-set-min-latitude-degrees": "1.5",
                "image-set-max-latitude-degrees": None,
                "image-entropy": "0.12",
                "image-particle-count": "7",
            }
        )
        payload = adapt_ifdo_image_set_to_serializer_payload(ifdo)

        self.assertEqual(payload["min_latitude_degrees"], 1.5)
        self.assertEqual(payload["entropy"], 0.12)
        self.assertEqual(payload["particle_count"], 7)

        self.assertNotIn("max_latitude_degrees", payload)

    def test_imageset_conditional_keys_only_added_if_present(self):
        """spatial/temporal/local_path keys are only considered if present in header."""
        ifdo = self._base_ifdo(
            **{
                "image-spatial-constraints": "  ",
                "image-temporal-constraints": "null",
                "image-set-local-path": "  ",
            }
        )
        payload = adapt_ifdo_image_set_to_serializer_payload(ifdo)

        self.assertNotIn("spatial_constraints", payload)
        self.assertNotIn("temporal_constraints", payload)
        self.assertNotIn("local_path", payload)

    def test_imageset_named_uri_objects_string_and_dict(self):
        """Named/URI fields accept string or dict{name, uri?}."""
        ifdo = self._base_ifdo(
            **{
                "image-project": "Project X",
                "image-platform": {"name": "ROV", "uri": "https://example.com/rov"},
            }
        )
        payload = adapt_ifdo_image_set_to_serializer_payload(ifdo)
        self.assertEqual(payload["project"], {"name": "Project X"})
        self.assertEqual(payload["platform"], {"name": "ROV", "uri": "https://example.com/rov"})

    def test_imageset_named_uri_object_dict_requires_name(self):
        """If dict is provided, name is required."""
        ifdo = self._base_ifdo(**{"image-project": {"uri": "https://example.com/p"}})
        with self.assertRaises(IFDOAdaptError) as ctx:
            adapt_ifdo_image_set_to_serializer_payload(ifdo)
        self.assertIn("ifdo.image-set-header.image-project.name must be a string", str(ctx.exception))

    def test_imageset_creators_list_happy_path_and_errors(self):
        """image-creators should become nested creators list; errors for bad types/blank items."""
        ifdo = self._base_ifdo(
            **{
                "image-creators": [
                    {"name": "Ada", "uri": "https://example.com/ada"},
                    "Grace Hopper",
                ]
            }
        )
        payload = adapt_ifdo_image_set_to_serializer_payload(ifdo)
        self.assertEqual(
            payload["creators"],
            [{"name": "Ada", "uri": "https://example.com/ada"}, {"name": "Grace Hopper"}],
        )

        ifdo_bad_type = self._base_ifdo(**{"image-creators": {"name": "nope"}})
        with self.assertRaises(IFDOAdaptError) as ctx:
            adapt_ifdo_image_set_to_serializer_payload(ifdo_bad_type)
        self.assertIn("image-creators must be a list", str(ctx.exception))

        ifdo_blank_item = self._base_ifdo(**{"image-creators": ["  "]})
        with self.assertRaises(IFDOAdaptError) as ctx2:
            adapt_ifdo_image_set_to_serializer_payload(ifdo_blank_item)
        self.assertIn(".name is required", str(ctx2.exception))

    def test_imageset_related_materials_happy_path_and_errors(self):
        """image-set-related-material becomes related_materials; validate types and required name."""
        ifdo = self._base_ifdo(
            **{
                "image-set-related-material": [
                    "Paper A",
                    {"name": "Dataset B", "uri": "https://example.com/ds"},
                ]
            }
        )
        payload = adapt_ifdo_image_set_to_serializer_payload(ifdo)
        self.assertEqual(payload["related_materials"][0], {"name": "Paper A"})
        self.assertEqual(payload["related_materials"][1]["name"], "Dataset B")
        self.assertEqual(payload["related_materials"][1]["uri"], "https://example.com/ds")

        ifdo_bad = self._base_ifdo(**{"image-set-related-material": "nope"})
        with self.assertRaises(IFDOAdaptError) as ctx:
            adapt_ifdo_image_set_to_serializer_payload(ifdo_bad)
        self.assertIn("must be a list", str(ctx.exception))

        ifdo_missing_name = self._base_ifdo(**{"image-set-related-material": [{"uri": "x"}]})
        with self.assertRaises(IFDOAdaptError) as ctx2:
            adapt_ifdo_image_set_to_serializer_payload(ifdo_missing_name)
        self.assertIn(".name is required", str(ctx2.exception))

        ifdo_bad_item = self._base_ifdo(**{"image-set-related-material": [123]})
        with self.assertRaises(IFDOAdaptError) as ctx3:
            adapt_ifdo_image_set_to_serializer_payload(ifdo_bad_item)
        self.assertIn("must be an object or string", str(ctx3.exception))

    def test_imageset_datetime_parsing_iso(self):
        """Datetime should parse ISO via pandas and EXIF-like format via strptime."""
        ifdo_iso = self._base_ifdo(**{"image-set-start-datetime": "2024-01-02T03:04:05Z"})
        payload = adapt_ifdo_image_set_to_serializer_payload(ifdo_iso)
        self.assertIsInstance(payload["date_time"], datetime)

        ifdo_bad = self._base_ifdo(**{"image-set-start-datetime": "not-a-date"})
        with self.assertRaises(IFDOAdaptError) as ctx:
            adapt_ifdo_image_set_to_serializer_payload(ifdo_bad)
        self.assertIn("Invalid datetime", str(ctx.exception))

        ifdo_bad = self._base_ifdo(**{"image-set-start-datetime": 1111111})
        with self.assertRaises(IFDOAdaptError) as ctx:
            adapt_ifdo_image_set_to_serializer_payload(ifdo_bad)
        self.assertIn("Expected datetime-like value", str(ctx.exception))

    def test_item_requires_filename(self):
        """image-filename is required and must be string."""
        with self.assertRaises(IFDOAdaptError) as ctx:
            adapt_ifdo_item_to_image_serializer_payload({"image-filename": "   "}, image_set_id=1)
        self.assertIn("image-filename is required", str(ctx.exception))

        with self.assertRaises(IFDOAdaptError) as ctx2:
            adapt_ifdo_item_to_image_serializer_payload({"image-filename": 123}, image_set_id=1)
        self.assertIn("must be a string", str(ctx2.exception))

    def test_item_basic_fields_and_drop_none(self):
        """Item adapter should convert types and drop None keys."""
        item = {
            "image-filename": "a.jpg",
            "image-latitude": "10.5",
            "image-particle-count": "3",
            "image-average-color": [1, 2, 3],
            "image-acquisition-settings": {"iso": 200},
            "image-hash-sha256": "abc",
            "image-datetime": "2024-01-02T03:04:05Z",
        }
        payload = adapt_ifdo_item_to_image_serializer_payload(item, image_set_id=42)

        self.assertEqual(payload["filename"], "a.jpg")
        self.assertEqual(payload["image_set_id"], 42)
        self.assertEqual(payload["latitude"], 10.5)
        self.assertEqual(payload["particle_count"], 3)
        self.assertEqual(payload["average_color"], [1, 2, 3])
        self.assertEqual(payload["acquisition_settings"], {"iso": 200})
        self.assertEqual(payload["sha256_hash"], "abc")
        self.assertIsInstance(payload["date_time"], datetime)

        self.assertNotIn("longitude", payload)

    def test_item_type_validation_errors(self):
        """List/dict/int/float validators should raise IFDOAdaptError on bad types."""
        with self.assertRaises(IFDOAdaptError) as ctx_list:
            adapt_ifdo_item_to_image_serializer_payload(
                {"image-filename": "a.jpg", "image-average-color": "nope"},
                image_set_id=1,
            )
        self.assertIn("Expected a list", str(ctx_list.exception))

        with self.assertRaises(IFDOAdaptError) as ctx_dict:
            adapt_ifdo_item_to_image_serializer_payload(
                {"image-filename": "a.jpg", "image-acquisition-settings": "nope"},
                image_set_id=1,
            )
        self.assertIn("Expected an object/dict", str(ctx_dict.exception))

        with self.assertRaises(IFDOAdaptError) as ctx_int:
            adapt_ifdo_item_to_image_serializer_payload(
                {"image-filename": "a.jpg", "image-particle-count": "x"},
                image_set_id=1,
            )
        self.assertIn("Expected an int-like value", str(ctx_int.exception))

        with self.assertRaises(IFDOAdaptError) as ctx_float:
            adapt_ifdo_item_to_image_serializer_payload(
                {"image-filename": "a.jpg", "image-latitude": "x"},
                image_set_id=1,
            )
        self.assertIn("Expected a float-like value", str(ctx_float.exception))

    def test_item_named_uri_and_creator_fallback(self):
        """Item adapter should map named/uri objects and prefer image-annotation-creators over image-creators."""
        item = {
            "image-filename": "a.jpg",
            "image-project": {"name": "Proj", "uri": "https://example.com/p"},
            "image-annotation-creators": [{"name": "Ann", "uri": "https://example.com/a"}],
            "image-creators": [{"name": "Ignored"}],
            "image-camera-pose": "Pose 1",
        }
        payload = adapt_ifdo_item_to_image_serializer_payload(item, image_set_id=1)

        self.assertEqual(payload["project"], {"name": "Proj", "uri": "https://example.com/p"})
        self.assertEqual(payload["creators"], [{"name": "Ann", "uri": "https://example.com/a"}])
        self.assertEqual(payload["camera_pose"], {"name": "Pose 1"})

    def test_item_maybe_string(self):
        """Fields that can be string or dict should be handled correctly, and dicts should require a name."""
        item = {
            "image-filename": "a.jpg",
            "image-copyright": 111111,
        }
        payload = adapt_ifdo_item_to_image_serializer_payload(item, image_set_id=1)

        self.assertEqual(payload["copyright"], "111111")
