"""Integration tests for label-set and annotation-set index filters."""

from django.urls import reverse
from rest_framework import status

from api.models import AnnotationSet, Context, ImageSet, Label, LabelSet, Platform, Project, Sensor
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

    def test_label_set_filters_by_part_of_uuid(self) -> None:
        """A partial UUID selects matching label sets without UUID parsing."""
        expected = LabelSet.objects.create(name="Wanted")
        LabelSet.objects.create(name="Other")

        response = self.client.get(reverse("label_set-list"), {"uuid": str(expected.id)[8:20]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(expected.id))

    def test_label_set_filters_by_label_metadata(self) -> None:
        """Label metadata filters find associated label sets and combine on one matching label."""
        expected = LabelSet.objects.create(name="Benthic label set")
        Label.objects.create(
            label_set=expected,
            name="Gadus",
            parent_label_name="Fish",
            lowest_taxonomic_name="Gadus morhua",
            lowest_aphia_id=126436,
        )
        Label.objects.create(
            label_set=expected,
            name="Cod",
            parent_label_name="Fish",
            lowest_taxonomic_name="Gadus morhua",
            lowest_aphia_id=126436,
        )
        other = LabelSet.objects.create(name="Other label set")
        Label.objects.create(label_set=other, name="Gadus", lowest_aphia_id=126436)
        split_match = LabelSet.objects.create(name="Split match")
        Label.objects.create(label_set=split_match, name="Gadus")
        Label.objects.create(
            label_set=split_match,
            name="Other species",
            parent_label_name="Fish",
            lowest_taxonomic_name="Gadus morhua",
            lowest_aphia_id=126436,
        )

        response = self.client.get(
            reverse("label_set-list"),
            {
                "label-name": "gad",
                "label-parent-name": "fish",
                "label-lowest-taxonomic-name": "morhua",
                "label-lowest-AphiaID": "264",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(expected.id))

    def test_label_set_filters_by_part_of_aphia_id(self) -> None:
        """AphiaID filtering matches a substring of the stored integer."""
        expected = LabelSet.objects.create(name="Wanted label set")
        Label.objects.create(label_set=expected, name="Cod", lowest_aphia_id=126436)
        LabelSet.objects.create(name="Other label set")

        response = self.client.get(reverse("label_set-list"), {"label-lowest-AphiaID": "264"})

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

    def test_annotation_set_filters_by_label_name(self) -> None:
        """Annotation sets match names of labels in their linked label sets."""
        label_set = LabelSet.objects.create(name="Fish taxonomy")
        Label.objects.create(label_set=label_set, name="Atlantic cod")
        Label.objects.create(label_set=label_set, name="Atlantic pollock")
        expected = AnnotationSet.objects.create(name="Fish annotations")
        expected.label_sets.add(label_set)
        other_label_set = LabelSet.objects.create(name="Coral taxonomy")
        Label.objects.create(label_set=other_label_set, name="Acropora")
        AnnotationSet.objects.create(name="Coral annotations").label_sets.add(other_label_set)

        response = self.client.get(reverse("annotation_set-list"), {"label-name": "atlantic"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(expected.id))

    def test_annotation_set_filters_by_part_of_uuid(self) -> None:
        """A partial UUID selects matching annotation sets without UUID parsing."""
        expected = AnnotationSet.objects.create(name="Wanted annotations")
        AnnotationSet.objects.create(name="Other annotations")

        response = self.client.get(reverse("annotation_set-list"), {"uuid": str(expected.id)[8:20]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(expected.id))

    def test_annotation_set_metadata_search_matches_any_field(self) -> None:
        """The grouped metadata search matches annotation sets by any configured field."""
        expected_by_project = AnnotationSet.objects.create(
            name="Project match",
            project=Project.objects.create(name="Reef project"),
        )
        expected_by_target = AnnotationSet.objects.create(name="Target match", target_environment="Coral reef")
        AnnotationSet.objects.create(name="Unrelated annotations")

        response = self.client.get(reverse("annotation_set-list"), {"metadata_search": "reef"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {item["id"] for item in response.data["results"]},
            {str(expected_by_project.id), str(expected_by_target.id)},
        )

    def test_image_set_filters_text_fields_and_partial_coordinates(self) -> None:
        """Text fields and coordinates use case-insensitive partial matching."""
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
                "longitude": "-4.2",
                "latitude": "50",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(expected.id))

    def test_image_set_metadata_search_matches_any_field(self) -> None:
        """The grouped metadata search matches image sets by any configured field."""
        expected_by_context = ImageSet.objects.create(
            name="Context match", context=Context.objects.create(name="Reef survey")
        )
        expected_by_objective = ImageSet.objects.create(name="Objective match", objective="Protect coral reefs")
        ImageSet.objects.create(name="Unrelated imagery")

        response = self.client.get(reverse("image_set-list"), {"metadata_search": "reef"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {item["id"] for item in response.data["results"]},
            {str(expected_by_context.id), str(expected_by_objective.id)},
        )

    def test_image_set_filters_by_part_of_uuid(self) -> None:
        """A partial UUID selects matching image sets without UUID parsing."""
        expected = ImageSet.objects.create(name="Wanted imagery")
        ImageSet.objects.create(name="Other imagery")

        response = self.client.get(reverse("image_set-list"), {"uuid": str(expected.id)[8:20]})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(expected.id))

    def test_image_set_coordinate_filters_accept_partial_content(self) -> None:
        """Coordinate filters treat their inputs as text rather than numeric values."""
        response = self.client.get(reverse("image_set-list"), {"latitude": "north"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_label_set_metadata_search_matches_any_field(self) -> None:
        """The grouped metadata search matches label sets by any configured field."""
        expected_by_abstract = LabelSet.objects.create(name="Abstract match", abstract="Reef catalogue")
        expected_by_objective = LabelSet.objects.create(name="Objective match", objective="Protect coral reefs")
        LabelSet.objects.create(name="Unrelated labels")

        response = self.client.get(reverse("label_set-list"), {"metadata_search": "reef"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {item["id"] for item in response.data["results"]},
            {str(expected_by_abstract.id), str(expected_by_objective.id)},
        )

    def test_label_set_label_search_matches_any_label_field_including_aphia_id(self) -> None:
        """The grouped label search matches label properties and partial AphiaIDs."""
        expected_by_name = LabelSet.objects.create(name="Name match")
        Label.objects.create(label_set=expected_by_name, name="Needlefish")
        expected_by_parent = LabelSet.objects.create(name="Parent match")
        Label.objects.create(label_set=expected_by_parent, parent_label_name="Needlefish")
        expected_by_taxon = LabelSet.objects.create(name="Taxonomy match")
        Label.objects.create(label_set=expected_by_taxon, lowest_taxonomic_name="Needlefish")
        expected_by_aphia_id = LabelSet.objects.create(name="Aphia match")
        Label.objects.create(label_set=expected_by_aphia_id, lowest_aphia_id=123456)
        LabelSet.objects.create(name="Unrelated labels")

        response = self.client.get(reverse("label_set-list"), {"label_search": "needle"})
        aphia_response = self.client.get(reverse("label_set-list"), {"label_search": "345"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {item["id"] for item in response.data["results"]},
            {str(expected_by_name.id), str(expected_by_parent.id), str(expected_by_taxon.id)},
        )
        self.assertEqual(aphia_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item["id"] for item in aphia_response.data["results"]],
            [str(expected_by_aphia_id.id)],
        )
