"""Integration tests for label-set and annotation-set index filters."""

from django.urls import reverse
from rest_framework import status

from api.models import AnnotationSet, Context, ImageSet, LabelSet, Platform, Project, Sensor
from api.tests.utils.auth_utils import AuthenticatedAPITestCase


class ImageAnnotationLabelSetFilterTests(AuthenticatedAPITestCase):
    """Tests for image, annotation, and label set index query parameters."""

    def test_label_set_filters_text_fields_case_insensitively_and_combines_them(self) -> None:
        """Text filters use partial matches and are combined with AND."""
        project = Project.objects.create(name="Atlantic Survey")
        context = Context.objects.create(name="Deep Ocean")
        expected = LabelSet.objects.create(
            name="Benthic Animals",
            project=project,
            context=context,
            abstract="Species catalogue",
            objective="Identify fauna",
            handle="https://example.test/labels/one",
        )
        LabelSet.objects.create(name="Pelagic Animals", project=project)

        response = self.client.get(
            reverse("label_set-list"),
            {"name": "BENTHIC", "project": "atlantic", "context": "ocean", "objective": "fauna"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(expected.id))

    def test_label_set_filters_by_exact_uuid(self) -> None:
        """The uuid parameter selects exactly one label set."""
        expected = LabelSet.objects.create(name="Wanted")
        LabelSet.objects.create(name="Other")

        response = self.client.get(reverse("label_set-list"), {"uuid": str(expected.id)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(expected.id))

    def test_annotation_set_filters_metadata_obis_and_target_fields(self) -> None:
        """All annotation-set query parameters map to current schema fields."""
        expected = AnnotationSet.objects.create(
            name="Fauna annotations",
            abstract="Expert-reviewed observations",
            obis_handles=["https://obis.example/dataset-123"],
            target_environment="Abyssal seafloor",
            target_timescale="Summer 2025",
        )
        AnnotationSet.objects.create(name="Other annotations")

        response = self.client.get(
            reverse("annotation_set-list"),
            {
                "name": "FAUNA",
                "abstract": "reviewed",
                "obis_data": "dataset-123",
                "target_environment": "seafloor",
                "target_timescale": "2025",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(expected.id))

    def test_annotation_set_filters_by_exact_uuid(self) -> None:
        """The uuid parameter selects exactly one annotation set."""
        expected = AnnotationSet.objects.create(name="Wanted annotations")
        AnnotationSet.objects.create(name="Other annotations")

        response = self.client.get(reverse("annotation_set-list"), {"uuid": str(expected.id)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(expected.id))

    def test_image_set_filters_text_fields_and_coordinates(self) -> None:
        """Text fields use partial matching while coordinates use numeric equality."""
        project = Project.objects.create(name="Atlantic Survey")
        context = Context.objects.create(name="Deep Ocean")
        platform = Platform.objects.create(name="Autonomous Vehicle")
        sensor = Sensor.objects.create(name="Stereo Camera")
        expected = ImageSet.objects.create(
            name="Benthic imagery",
            project=project,
            context=context,
            platform=platform,
            sensor=sensor,
            abstract="Abyssal survey images",
            objective="Map seafloor fauna",
            target_timescale="Summer 2025",
            handle="https://example.test/images/one",
            longitude=-4.25,
            latitude=50.75,
        )
        ImageSet.objects.create(name="Other imagery", project=project)

        response = self.client.get(
            reverse("image_set-list"),
            {
                "name": "BENTHIC",
                "project": "atlantic",
                "context": "ocean",
                "abstract": "survey",
                "objective": "fauna",
                "target_timescale": "2025",
                "handle": "images/one",
                "platform": "vehicle",
                "sensor": "camera",
                "longitude": "-4.25",
                "latitude": "50.75",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(expected.id))

    def test_image_set_filters_by_exact_uuid(self) -> None:
        """The uuid parameter selects exactly one image set."""
        expected = ImageSet.objects.create(name="Wanted imagery")
        ImageSet.objects.create(name="Other imagery")

        response = self.client.get(reverse("image_set-list"), {"uuid": str(expected.id)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(expected.id))

    def test_image_set_filters_rejects_invalid_coordinate(self) -> None:
        """Invalid numeric parameters produce a client error instead of a server error."""
        response = self.client.get(reverse("image_set-list"), {"latitude": "north"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
