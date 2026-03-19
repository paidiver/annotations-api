"""URL configuration for the Annotations API endpoints."""

from rest_framework.routers import DefaultRouter

from api.views import (
    AnnotationLabelViewSet,
    AnnotationSetViewSet,
    AnnotationViewSet,
    AnnotatorViewSet,
    UploadAnnotationsView,
)

router_annotation = DefaultRouter()

# annotation related routes
router_annotation.register(
    r"annotations",
    AnnotationViewSet,
    basename="annotation",
)
router_annotation.register(
    r"annotators",
    AnnotatorViewSet,
    basename="annotator",
)

router_annotation.register(
    r"annotation_labels",
    AnnotationLabelViewSet,
    basename="annotation_label",
)

# annotatiion_set endpoints are registered here
router_annotation.register(
    r"annotation_sets",
    AnnotationSetViewSet,
    basename="annotation_set",
)

# route for uploading annotation data from XLSX file
router_annotation.register(
    "upload_annotation",
    UploadAnnotationsView,
    basename="upload_annotation",
)
