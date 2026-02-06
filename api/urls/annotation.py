"""URL configuration for the Annotations API endpoints."""

from rest_framework.routers import DefaultRouter

from api.views import AnnotationLabelViewSet, AnnotationViewSet, AnnotatorViewSet

router_annotation = DefaultRouter()
router_annotation.register(
    r"annotations",
    AnnotationViewSet,
)
router_annotation.register(
    r"annotators",
    AnnotatorViewSet,
)

router_annotation.register(
    r"annotation_labels",
    AnnotationLabelViewSet,
)
