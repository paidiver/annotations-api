"""URL configuration for the AnnotationSet API endpoints."""

from rest_framework.routers import DefaultRouter

from api.views import AnnotationSetViewSet

router_annotation_set = DefaultRouter()
router_annotation_set.register(
    r"",
    AnnotationSetViewSet,
)
