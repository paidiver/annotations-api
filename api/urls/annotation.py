"""URL configuration for the Annotations API endpoints."""

from django.conf import settings
from rest_framework.routers import DefaultRouter

from api.views import (
    AnnotationSetModelViewSet,
    AnnotationSetViewSet,
    AnnotationViewSet,
)

router_annotation = DefaultRouter()

# annotation related routes
router_annotation.register(
    r"annotations",
    AnnotationViewSet,
    basename="annotation",
)
# annotatiion_set endpoints are registered here
router_annotation.register(
    r"annotation_sets",
    AnnotationSetViewSet,
    basename="annotation_set",
)

router_annotation.register(
    r"annotation_models",
    AnnotationSetModelViewSet,
    basename="annotation_model",
)

if settings.ENABLE_ANNOTATION_SEARCH:
    from api.views.search import AnnotationSearchViewSet

    router_annotation.register(
        r"search",
        AnnotationSearchViewSet,
        basename="search",
    )
