"""Routes for the API viewsets."""

from rest_framework.routers import DefaultRouter

from .views import ContextViewSet, CreatorViewSet, EventViewSet, LicenseViewSet, PIViewSet

router = DefaultRouter()
router.register("creators", CreatorViewSet, basename="creator")
router.register("contexts", ContextViewSet, basename="context")
router.register("pis", PIViewSet, basename="pi")
router.register("events", EventViewSet, basename="event")
router.register("licenses", LicenseViewSet, basename="license")
