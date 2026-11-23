"""API URL configuration module."""

from django.conf import settings
from django.urls import include, path

from api.views.debug import DebugDatabaseDumpView

from ..views import HealthView
from .annotation import router_annotation
from .fields import router_fields
from .image import router_image
from .label import router_label

urlpatterns = [
    path("taxonomy/", include("api.urls.taxonomy")),
    path("health/", HealthView.as_view(), name="Health"),
    path("images/", include(router_image.urls)),
    path("annotations/", include(router_annotation.urls)),
    path("labels/", include(router_label.urls)),
    path("fields/", include(router_fields.urls)),
    path("debug/db-dump/", DebugDatabaseDumpView.as_view(), name="debug-db-dump"),
]

if settings.ENABLE_ANNOTATION_INGEST:
    urlpatterns.append(path("ingest/", include("api.urls.ingest"), name="ingest-ifdo-image-set"))
