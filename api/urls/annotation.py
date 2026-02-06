"""URL configuration for the Annotation API endpoints."""

from rest_framework.routers import DefaultRouter

from api.views import AnnotationViewSet

router_annotation = DefaultRouter()
router_annotation.register(
    r"",
    AnnotationViewSet,
)
