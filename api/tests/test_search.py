"""Tests for AnnotationSearchViewSet."""

from unittest.mock import Mock, PropertyMock, patch

import requests
from django.urls import reverse
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, APITestCase

from api.models import Annotation, AnnotationLabel, Image, Label
from api.models.annotation import Annotator
from api.models.annotation_set import AnnotationSet
from api.models.fields import Platform, Project
from api.models.image_set import ImageSet
from api.views.search import AnnotationSearchViewSet, _get_aphia_ids_by_name_part, _get_descendant_aphia_ids


class AnnotationSearchViewSetTests(APITestCase):
    """Integration tests for AnnotationSearchViewSet endpoints."""

    def setUp(self) -> None:
        """Set up test data and common variables."""
        self.annotation_set_1 = AnnotationSet.objects.create(name="Annotation Set 1")
        self.annotation_set_2 = AnnotationSet.objects.create(name="Annotation Set 2")

        self.project = Project.objects.create(name="Project Alpha")
        self.platform = Platform.objects.create(name="ROV")
        self.image_set_1 = ImageSet.objects.create(
            name="Image Set 1",
            deployment="mapping",
            fauna_attraction="none",
            marine_zone="seafloor",
            project=self.project,
            platform=self.platform,
        )
        self.image_set_2 = ImageSet.objects.create(
            name="Image Set 2",
            deployment="survey",
            fauna_attraction="baited",
            marine_zone="water column",
            project=self.project,
            platform=self.platform,
        )

        self.annotation_set_1.image_sets.set([self.image_set_1])
        self.annotation_set_2.image_sets.set([self.image_set_2])

        self.annotator = Annotator.objects.create(name="Test Annotator")

        self.image_1 = Image.objects.create(
            image_set=self.image_set_1,
            filename="image_1.jpg",
            latitude=10.0,
            longitude=20.0,
        )
        self.image_2 = Image.objects.create(
            image_set=self.image_set_2,
            filename="image_2.jpg",
            latitude=30.0,
            longitude=40.0,
        )

        self.annotation_1 = Annotation.objects.create(
            image=self.image_1,
            annotation_set=self.annotation_set_1,
            annotation_platform="platform-a",
            shape="polygon",
            coordinates=[[0, 0], [1, 1], [2, 2]],
            dimension_pixels=123,
        )
        self.annotation_2 = Annotation.objects.create(
            image=self.image_2,
            annotation_set=self.annotation_set_2,
            annotation_platform="platform-b",
            shape="rectangle",
            coordinates=[[10, 10], [20, 20]],
            dimension_pixels=456,
        )

        self.label_1 = Label.objects.create(
            annotation_set=self.annotation_set_1,
            name="Cod",
            parent_label_name="Fish",
            lowest_aphia_id=1001,
        )
        self.label_2 = Label.objects.create(
            annotation_set=self.annotation_set_2,
            name="Crab",
            parent_label_name="Crustacean",
            lowest_aphia_id=2002,
        )

        self.annotation_label_1 = AnnotationLabel.objects.create(
            annotation=self.annotation_1,
            label=self.label_1,
            annotator=self.annotator,
            creation_datetime="2024-01-01T00:00:00Z",
        )
        self.annotation_label_2 = AnnotationLabel.objects.create(
            annotation=self.annotation_2,
            label=self.label_2,
            annotator=self.annotator,
            creation_datetime="2024-01-01T00:00:00Z",
        )

        self.list_url = reverse("search-list")
        self.grouped_url = reverse("search-list-grouped")

    def test_list_requires_aphia_ids_or_name_part(self) -> None:
        """Test that list rejects requests without aphia_ids[] or name_part."""
        resp = self.client.get(self.list_url)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            resp.data["detail"],
            {"query": "At least one of 'aphia_ids[]' or 'name_part' query parameters must be provided."},
        )

    def test_list_filters_by_aphia_ids(self) -> None:
        """Test listing search results filtered by aphia_ids[]."""
        resp = self.client.get(self.list_url, {"aphia_ids[]": [1001]})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        self.assertEqual(set(data.keys()), {"count", "next", "previous", "results"})
        self.assertEqual(data["count"], 1)
        results = data["results"]
        self.assertEqual(set(results.keys()), {"summary", "annotations"})
        self.assertIsNone(results["summary"])
        self.assertEqual(len(results["annotations"]), 1)

        row = results["annotations"][0]
        self.assertEqual(str(row["uuid"]), str(self.annotation_label_1.id))
        self.assertEqual(row["image_filename"], "image_1.jpg")
        self.assertEqual(str(row["image_uuid"]), str(self.image_1.id))
        self.assertEqual(row["label_name"], "Cod")
        self.assertEqual(row["label_aphia_id"], 1001)
        self.assertEqual(row["annotation_platform"], "platform-a")
        self.assertEqual(row["annotation_shape"], "polygon")
        self.assertEqual(row["annotation_dimension_pixels"], 123)
        self.assertEqual(row["annotator_name"], "Test Annotator")
        self.assertEqual(str(row["annotation_set_uuid"]), str(self.annotation_set_1.id))
        self.assertEqual(row["annotation_set_name"], "Annotation Set 1")
        self.assertEqual(str(row["image_set_uuid"]), str(self.image_set_1.id))
        self.assertEqual(row["image_set_name"], "Image Set 1")

    def test_list_returns_summary_when_requested(self) -> None:
        """Test list includes summary when calculate_summary=true."""
        resp = self.client.get(
            self.list_url,
            {"aphia_ids[]": [1001, 2002], "calculate_summary": "true"},
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        self.assertEqual(data["count"], 2)

        summary = data["results"]["summary"]
        self.assertEqual(summary["n_annotations"], 2)
        self.assertEqual(summary["n_images"], 2)
        self.assertEqual(summary["n_annotation_sets"], 2)
        self.assertEqual(summary["n_image_sets"], 2)

        self.assertEqual(len(data["results"]["annotations"]), 2)

    def test_list_ignores_invalid_aphia_ids_in_query(self) -> None:
        """Test invalid aphia_ids[] values are ignored and valid ones are still used."""
        resp = self.client.get(
            self.list_url,
            [("aphia_ids[]", "not-an-int"), ("aphia_ids[]", "1001"), ("aphia_ids[]", "also-bad")],
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"]["annotations"][0]["label_aphia_id"], 1001)

    @patch("api.views.search._get_aphia_ids_by_name_part")
    def test_list_filters_by_name_part(self, mocked_get_aphia_ids_by_name_part: Mock) -> None:
        """Test listing search results using name_part lookup.

        Args:
            mocked_get_aphia_ids_by_name_part (Mock): Mock of the _get_aphia_ids_by_name_part function.
        """
        mocked_get_aphia_ids_by_name_part.return_value = [1001]

        resp = self.client.get(self.list_url, {"name_part": "cod"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertIsNone(resp.data["results"]["summary"])
        self.assertEqual(resp.data["results"]["annotations"][0]["label_name"], "Cod")
        mocked_get_aphia_ids_by_name_part.assert_called_once_with("cod")

    @patch("api.views.search._get_aphia_ids_by_name_part")
    def test_list_filters_by_label_name_when_name_part_finds_no_aphia_ids(
        self,
        mocked_get_aphia_ids_by_name_part: Mock,
    ) -> None:
        """Test list falls back to label name search when name_part produces no AphiaIDs.

        Args:
            mocked_get_aphia_ids_by_name_part (Mock): Mock of the _get_aphia_ids_by_name_part function.
        """
        mocked_get_aphia_ids_by_name_part.return_value = []

        resp = self.client.get(self.list_url, {"name_part": "cod"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"]["annotations"][0]["label_name"], "Cod")
        mocked_get_aphia_ids_by_name_part.assert_called_once_with("cod")

    @patch("api.views.search._get_aphia_ids_by_name_part")
    def test_list_returns_404_when_name_part_finds_no_aphia_ids_or_label_name(
        self,
        mocked_get_aphia_ids_by_name_part: Mock,
    ) -> None:
        """Test list returns 404 when neither AphiaIDs nor label names match.

        Args:
            mocked_get_aphia_ids_by_name_part (Mock): Mock of the _get_aphia_ids_by_name_part function.
        """
        mocked_get_aphia_ids_by_name_part.return_value = []

        resp = self.client.get(self.list_url, {"name_part": "does-not-exist"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resp.data, {"count": 0, "next": None, "previous": None, "results": {"summary": None, "annotations": []}}
        )

    @patch("api.views.search._get_descendant_aphia_ids")
    def test_list_include_descendants_adds_results(self, mocked_get_descendant_aphia_ids: Mock) -> None:
        """Test include_descendants=true includes descendant AphiaIDs in the search.

        Args:
            mocked_get_descendant_aphia_ids (Mock): Mock of the _get_descendant_aphia_ids function.
        """
        mocked_get_descendant_aphia_ids.return_value = [2002]

        resp = self.client.get(
            self.list_url,
            {"aphia_ids[]": [1001], "include_descendants": "true"},
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)
        self.assertIsNone(resp.data["results"]["summary"])

        returned_aphia_ids = sorted(item["label_aphia_id"] for item in resp.data["results"]["annotations"])
        self.assertEqual(returned_aphia_ids, [1001, 2002])
        mocked_get_descendant_aphia_ids.assert_called_once_with([1001])

    @patch("api.views.search._get_aphia_ids_by_name_part")
    @patch("api.views.search._get_descendant_aphia_ids")
    def test_list_deduplicates_aphia_ids_from_query_name_part_and_descendants(
        self,
        mocked_get_descendant_aphia_ids: Mock,
        mocked_get_aphia_ids_by_name_part: Mock,
    ) -> None:
        """Test AphiaIDs are deduplicated before querying.

        Args:
            mocked_get_descendant_aphia_ids (Mock): Mock of the _get_descendant_aphia_ids function.
            mocked_get_aphia_ids_by_name_part (Mock): Mock of the _get_aphia_ids_by_name_part function.
        """
        mocked_get_aphia_ids_by_name_part.return_value = [1001, 2002]
        mocked_get_descendant_aphia_ids.return_value = [1001, 2002]

        resp = self.client.get(
            self.list_url,
            {
                "aphia_ids[]": [1001],
                "name_part": "test",
                "include_descendants": "true",
            },
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)

        returned_aphia_ids = sorted(item["label_aphia_id"] for item in resp.data["results"]["annotations"])
        self.assertEqual(returned_aphia_ids, [1001, 2002])

    def test_grouped_requires_aphia_ids_or_name_part(self) -> None:
        """Test grouped rejects requests without aphia_ids[] or name_part."""
        resp = self.client.get(self.grouped_url)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            resp.data["detail"],
            {"query": "At least one of 'aphia_ids[]' or 'name_part' query parameters must be provided."},
        )

    def test_grouped_filters_by_aphia_ids(self) -> None:
        """Test grouped endpoint returns grouped rows keyed by annotation set id."""
        resp = self.client.get(self.grouped_url, {"aphia_ids[]": [1001]})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        self.assertEqual(set(data.keys()), {"count", "next", "previous", "results"})
        self.assertEqual(data["count"], 1)

        grouped = data["results"]["annotations"]
        self.assertEqual(list(grouped.keys()), [str(self.annotation_set_1.id)])
        self.assertEqual(len(grouped[str(self.annotation_set_1.id)]), 1)

        row = grouped[str(self.annotation_set_1.id)][0]
        self.assertEqual(str(row["uuid"]), str(self.annotation_label_1.id))
        self.assertEqual(row["annotation_set_name"], "Annotation Set 1")
        self.assertEqual(row["image_set_name"], "Image Set 1")
        self.assertEqual(str(row["image_set_uuid"]), str(self.image_set_1.id))
        self.assertEqual(row["image_filename"], "image_1.jpg")
        self.assertEqual(str(row["image_uuid"]), str(self.image_1.id))
        self.assertEqual(row["label_name"], "Cod")
        self.assertEqual(row["label_aphia_id"], 1001)
        self.assertEqual(row["annotation_platform"], "platform-a")
        self.assertEqual(row["annotation_shape"], "polygon")
        self.assertEqual(row["annotation_dimension_pixels"], 123)
        self.assertEqual(row["annotator_name"], "Test Annotator")

    def test_grouped_returns_summary_when_requested(self) -> None:
        """Test grouped includes summary when calculate_summary=true."""
        resp = self.client.get(
            self.grouped_url,
            {"aphia_ids[]": [1001, 2002], "calculate_summary": "true"},
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        self.assertEqual(data["count"], 2)

        summary = data["results"]["summary"]
        self.assertEqual(summary["n_annotations"], 2)
        self.assertEqual(summary["n_images"], 2)
        self.assertEqual(summary["n_annotation_sets"], 2)
        self.assertEqual(summary["n_image_sets"], 2)

        grouped = data["results"]["annotations"]
        self.assertEqual(set(grouped.keys()), {str(self.annotation_set_1.id), str(self.annotation_set_2.id)})

    @patch("api.views.search._get_aphia_ids_by_name_part")
    def test_grouped_filters_by_name_part(self, mocked_get_aphia_ids_by_name_part: Mock) -> None:
        """Test grouped endpoint supports name_part lookup.

        Args:
            mocked_get_aphia_ids_by_name_part (Mock): Mock of the _get_aphia_ids_by_name_part function.
        """
        mocked_get_aphia_ids_by_name_part.return_value = [2002]

        resp = self.client.get(self.grouped_url, {"name_part": "cra"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

        grouped = resp.data["results"]["annotations"]
        self.assertEqual(list(grouped.keys()), [str(self.annotation_set_2.id)])
        self.assertEqual(grouped[str(self.annotation_set_2.id)][0]["label_name"], "Crab")

    @patch("api.views.search._get_aphia_ids_by_name_part")
    def test_grouped_filters_by_label_name_when_name_part_finds_no_aphia_ids(
        self,
        mocked_get_aphia_ids_by_name_part: Mock,
    ) -> None:
        """Test grouped falls back to label name search when name_part produces no AphiaIDs.

        Args:
            mocked_get_aphia_ids_by_name_part (Mock): Mock of the _get_aphia_ids_by_name_part function.
        """
        mocked_get_aphia_ids_by_name_part.return_value = []

        resp = self.client.get(self.grouped_url, {"name_part": "cra"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

        grouped = resp.data["results"]["annotations"]
        self.assertEqual(list(grouped.keys()), [str(self.annotation_set_2.id)])
        self.assertEqual(grouped[str(self.annotation_set_2.id)][0]["label_name"], "Crab")

    @patch("api.views.search._get_aphia_ids_by_name_part")
    def test_grouped_returns_404_when_name_part_finds_no_aphia_ids_or_label_name(
        self,
        mocked_get_aphia_ids_by_name_part: Mock,
    ) -> None:
        """Test grouped returns 404 when neither AphiaIDs nor label names match.

        Args:
            mocked_get_aphia_ids_by_name_part (Mock): Mock of the _get_aphia_ids_by_name_part function.
        """
        mocked_get_aphia_ids_by_name_part.return_value = []

        resp = self.client.get(self.grouped_url, {"name_part": "does-not-exist"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resp.data, {"count": 0, "next": None, "previous": None, "results": {"summary": None, "annotations": {}}}
        )

    @patch("api.views.search.CachedWoRMSClient")
    def test_get_descendant_aphia_ids_returns_empty_list_on_request_exception(self, mocked_client_cls: Mock) -> None:
        """Test descendant helper returns empty list when the WoRMS client raises RequestException.

        Args:
            mocked_client_cls (Mock): Mock of the CachedWoRMSClient class.
        """
        mocked_client = mocked_client_cls.return_value
        mocked_client.descendants_aphia_ids.side_effect = requests.RequestException()

        result = _get_descendant_aphia_ids([1001])

        self.assertEqual(result, [])
        mocked_client.descendants_aphia_ids.assert_called_once_with([1001])

    @patch("api.views.search.CachedWoRMSClient")
    def test_get_aphia_ids_by_name_part_returns_empty_list_on_request_exception(self, mocked_client_cls: Mock) -> None:
        """Test name-part helper returns empty list when the WoRMS client raises RequestException.

        Args:
            mocked_client_cls (Mock): Mock of the CachedWoRMSClient class.
        """
        mocked_client = mocked_client_cls.return_value
        mocked_client.aphia_ids_by_name_part.side_effect = requests.RequestException()

        result = _get_aphia_ids_by_name_part("cod")

        self.assertEqual(result, [])
        mocked_client.aphia_ids_by_name_part.assert_called_once_with("cod", combine_vernaculars=True)

    @patch("api.views.search.AnnotationSearchViewSet.paginator", new_callable=PropertyMock)
    @patch("api.views.search._get_aphia_ids_by_name_part")
    def test_list_filters_by_name_part_with_no_pagination(
        self, mocked_get_aphia_ids_by_name_part: Mock, mocked_paginator: Mock
    ) -> None:
        """Test listing search results using name_part lookup.

        Args:
            mocked_get_aphia_ids_by_name_part (Mock): Mock of the _get_aphia_ids_by_name_part function.
            mocked_paginator (Mock): Mock of the paginator property.
        """
        mocked_get_aphia_ids_by_name_part.return_value = [1001]

        fake_paginator = Mock()
        fake_paginator.paginate_queryset.return_value = None
        mocked_paginator.return_value = fake_paginator

        resp = self.client.get(self.list_url, {"name_part": "cod"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(resp.data["summary"])
        annotations = resp.data["annotations"]

        self.assertIsInstance(annotations, list)
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0]["label_name"], "Cod")

        resp = self.client.get(self.grouped_url, {"name_part": "cod"})

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIsInstance(resp.data, dict)
        self.assertIn(str(self.annotation_set_1.id), resp.data["annotations"].keys())
        self.assertEqual(len(resp.data["annotations"][str(self.annotation_set_1.id)]), 1)

    @patch("api.views.search.AnnotationSearchViewSet._get_all_aphia_ids_from_request")
    def test_list_returns_response_from_get_all_aphia_ids_from_request(
        self,
        mocked_get_all_aphia_ids: Mock,
    ) -> None:
        """Test list returns the Response object from _get_all_aphia_ids_from_request when it returns a Response.

        Args:
            mocked_get_all_aphia_ids (Mock): Mock of the _get_all_aphia_ids_from_request method.
        """
        mocked_get_all_aphia_ids.return_value = Response(
            {"detail": "mocked error"},
            status=status.HTTP_404_NOT_FOUND,
        )

        resp = self.client.get(self.list_url, {"aphia_ids[]": [1001]})

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data, {"detail": "mocked error"})

    @patch("api.views.search.AnnotationSearchViewSet._get_all_aphia_ids_from_request")
    def test_grouped_returns_response_from_get_all_aphia_ids_from_request(
        self,
        mocked_get_all_aphia_ids: Mock,
    ) -> None:
        """Test grouped returns the Response object from _get_all_aphia_ids_from_request when it returns a Response.

        Args:
            mocked_get_all_aphia_ids (Mock): Mock of the _get_all_aphia_ids_from_request method.
        """
        mocked_get_all_aphia_ids.return_value = Response(
            {"detail": "mocked error"},
            status=status.HTTP_404_NOT_FOUND,
        )

        resp = self.client.get(self.grouped_url, {"aphia_ids[]": [1001]})

        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data, {"detail": "mocked error"})

    def test_list_filters_by_all_optional_query_params(self) -> None:
        """Test listing search results filtered by all optional query parameters together."""
        resp = self.client.get(
            self.list_url,
            {
                "aphia_ids[]": [1001],
                "image_set_name": "Image Set 1",
                "project": "Project Alpha",
                "platform": "ROV",
                "deployment": self.image_set_1.deployment,
                "fauna_attraction": self.image_set_1.fauna_attraction,
                "marine_zone": self.image_set_1.marine_zone,
                "min_lat": self.image_1.latitude,
                "max_lat": self.image_1.latitude,
                "min_lon": self.image_1.longitude,
                "max_lon": self.image_1.longitude,
            },
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(
            resp.data["results"]["annotations"][0]["label_aphia_id"],
            1001,
        )

    def test_list_rejects_invalid_choice_params(self) -> None:
        """Test list rejects invalid values for choice-based query parameters."""
        resp = self.client.get(
            self.list_url,
            {
                "aphia_ids[]": [1001],
                "deployment": "invalid-deployment",
                "fauna_attraction": "invalid-fauna",
                "marine_zone": "invalid-zone",
            },
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("deployment", resp.data["detail"])
        self.assertIn("fauna_attraction", resp.data["detail"])
        self.assertIn("marine_zone", resp.data["detail"])

    def test_list_rejects_short_length_params(self) -> None:
        """Test list rejects values for string-based query parameters that are too short."""
        resp = self.client.get(
            self.list_url,
            {
                "aphia_ids[]": [1001],
                "name_part": "ab",
                "project": "xy",
                "platform": "zz",
                "image_set_name": "qw",
            },
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            resp.data["detail"]["name_part"],
            "'name_part' must contain at least 3 characters.",
        )
        self.assertEqual(
            resp.data["detail"]["project"],
            "'project' must contain at least 3 characters.",
        )
        self.assertEqual(
            resp.data["detail"]["platform"],
            "'platform' must contain at least 3 characters.",
        )
        self.assertEqual(
            resp.data["detail"]["image_set_name"],
            "'image_set_name' must contain at least 3 characters.",
        )

    def test_list_rejects_non_numeric_bbox_params(self) -> None:
        """Test list rejects non-numeric values for bounding box query parameters."""
        resp = self.client.get(
            self.list_url,
            {
                "aphia_ids[]": [1001],
                "min_lat": "abc",
                "max_lat": "def",
                "min_lon": "ghi",
                "max_lon": "jkl",
            },
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["detail"]["min_lat"], "'min_lat' must be a valid number.")
        self.assertEqual(resp.data["detail"]["max_lat"], "'max_lat' must be a valid number.")
        self.assertEqual(resp.data["detail"]["min_lon"], "'min_lon' must be a valid number.")
        self.assertEqual(resp.data["detail"]["max_lon"], "'max_lon' must be a valid number.")

    def test_list_rejects_invalid_bbox_ranges(self) -> None:
        """Test list rejects values for bounding box query parameters that are out of valid ranges."""
        resp = self.client.get(
            self.list_url,
            {
                "aphia_ids[]": [1001],
                "min_lat": "91",
                "max_lat": "-91",
                "min_lon": "181",
                "max_lon": "-181",
            },
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["detail"]["min_lat"], "'min_lat' must be between -90 and 90.")
        self.assertEqual(resp.data["detail"]["max_lat"], "'max_lat' must be between -90 and 90.")
        self.assertEqual(resp.data["detail"]["min_lon"], "'min_lon' must be between -180 and 180.")
        self.assertEqual(resp.data["detail"]["max_lon"], "'max_lon' must be between -180 and 180.")
        self.assertEqual(
            resp.data["detail"]["latitude_range"],
            "'min_lat' must be less than or equal to 'max_lat'.",
        )
        self.assertEqual(
            resp.data["detail"]["longitude_range"],
            "'min_lon' must be less than or equal to 'max_lon'.",
        )

    def test_get_float_query_param_returns_none_and_float(self) -> None:
        """Test _get_float_query_param returns None for missing or empty params and returns float for valid input."""
        factory = APIRequestFactory()
        view = AnnotationSearchViewSet()

        request = Request(factory.get("/fake", {}))
        self.assertIsNone(view._get_float_query_param(request, "min_lat"))

        request = Request(factory.get("/fake", {"min_lat": ""}))
        self.assertIsNone(view._get_float_query_param(request, "min_lat"))

        request = Request(factory.get("/fake", {"min_lat": "12.5"}))
        self.assertEqual(view._get_float_query_param(request, "min_lat"), 12.5)
