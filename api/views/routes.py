"""Routes for the API viewsets."""

from rest_framework.routers import DefaultRouter

from .views import (
    AnnotatorViewSet,
    ContextViewSet,
    CreatorViewSet,
    EventViewSet,
    LicenseViewSet,
    PIViewSet,
    PlatformViewSet,
    ProjectViewSet,
    SensorViewSet,
)

router = DefaultRouter()
router.register("annotators", AnnotatorViewSet, basename="annotator")
router.register("creators", CreatorViewSet, basename="creator")
router.register("contexts", ContextViewSet, basename="context")
router.register("pis", PIViewSet, basename="pi")
router.register("events", EventViewSet, basename="event")
router.register("licenses", LicenseViewSet, basename="license")
router.register("platforms", PlatformViewSet, basename="platform")
router.register("projects", ProjectViewSet, basename="project")
router.register("sensors", SensorViewSet, basename="sensor")
