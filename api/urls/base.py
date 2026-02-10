"""API URL configuration module."""

from django.urls import include, path

from api.views.debug import DebugDatabaseDumpView

from ..views import HealthView
from .annotation import router_annotation
from .annotation_set import router_annotation_set
from .fields import router_fields
from .image import router_image
from .image_set import router_image_set
from .label import router_label

urlpatterns = [
    path("health/", HealthView.as_view(), name="Health"),
    path("images/", include(router_image_set.urls)),
    path("images/", include(router_image.urls)),
    path("annotations/", include(router_annotation.urls)),
    path("annotations/", include(router_annotation_set.urls)),
    path("labels/", include(router_label.urls)),
    path("fields/", include(router_fields.urls)),
    path("debug/db-dump/", DebugDatabaseDumpView.as_view(), name="debug-db-dump"),
]
