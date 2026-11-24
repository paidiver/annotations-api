"""Regression tests for public routes and their Swagger groupings."""

from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import NoReverseMatch, Resolver404, resolve, reverse
from drf_spectacular.generators import SchemaGenerator
from rest_framework.test import APIClient


class RouteOrganizationTests(SimpleTestCase):
    """Check canonical routes, removed aliases, and query validation."""

    def test_schema_tags(self) -> None:
        """Document canonical endpoints under the intended tags."""
        paths = SchemaGenerator().get_schema(request=None, public=True)["paths"]
        routes = [("/api/taxonomy/worms/taxa/", "get", "Taxonomy", False)]
        if settings.ENABLE_ANNOTATION_INGEST:
            routes.extend(
                [
                    ("/api/ingest/image-sets/", "post", "Ingest", False),
                    ("/api/ingest/annotation-sets/", "post", "Ingest", False),
                    ("/api/ingest/label-sets/", "post", "Ingest", False),
                ]
            )
        if settings.ENABLE_ANNOTATION_SEARCH:
            routes.extend(
                [
                    ("/api/annotations/search/", "get", "Annotation Search", False),
                    ("/api/annotations/search/grouped/", "get", "Annotation Search", False),
                    ("/api/annotations/search/export/", "get", "Annotation Search", False),
                ]
            )
        for path, method, tag, deprecated in routes:
            with self.subTest(path=path):
                operation = paths[path][method]
                self.assertEqual(operation["tags"], [tag])
                self.assertEqual(operation.get("deprecated", False), deprecated)
        if not settings.ENABLE_ANNOTATION_INGEST:
            self.assertNotIn("/api/ingest/image-sets/", paths)
            self.assertNotIn("/api/ingest/annotation-sets/", paths)
            self.assertNotIn("/api/ingest/label-sets/", paths)
        if not settings.ENABLE_ANNOTATION_SEARCH:
            self.assertNotIn("/api/annotations/search/", paths)
            self.assertNotIn("/api/annotations/search/grouped/", paths)
            self.assertNotIn("/api/annotations/search/export/", paths)
        parameters = paths["/api/taxonomy/worms/taxa/"]["get"]["parameters"]
        name_part = next(parameter for parameter in parameters if parameter["name"] == "name_part")
        self.assertEqual(name_part["in"], "query")
        self.assertTrue(name_part["required"])

    def test_export_reverse_uses_canonical_url(self) -> None:
        """Keep the existing reverse name pointing at the new export URL."""
        if settings.ENABLE_ANNOTATION_SEARCH:
            self.assertEqual(reverse("search-export-data"), "/api/annotations/search/export/")
        else:
            with self.assertRaises(NoReverseMatch):
                reverse("search-export-data")

    def test_removed_routes_do_not_resolve(self) -> None:
        """Removed aliases must neither resolve nor appear in the schema."""
        paths = SchemaGenerator().get_schema(request=None, public=True)["paths"]
        for path in [
            "/api/ingest/image-set",
            "/api/annotations/upload_annotation/",
            "/api/annotations/worms_cache/ajax_by_name_part/{name_part}/",
            "/api/annotations/search/export-data/",
        ]:
            with self.subTest(path=path):
                self.assertNotIn(path, paths)
                with self.assertRaises(Resolver404):
                    resolve(path.replace("{name_part}", "lophi"))

    def test_taxonomy_requires_nonblank_name_part(self) -> None:
        """Invalid filters must not trigger an upstream lookup."""
        with patch("api.views.worms_cache.CachedWoRMSClient") as mocked:
            for params in [{}, {"name_part": ""}, {"name_part": "   "}]:
                response = APIClient().get(reverse("worms-taxa-list"), params)
                self.assertEqual(response.status_code, 400)
            mocked.assert_not_called()
