"""Routes for the API viewsets."""

from rest_framework.routers import DefaultRouter

from .views import ContextViewSet, CreatorViewSet

router = DefaultRouter()
router.register("creators", CreatorViewSet, basename="creator")
router.register("contexts", ContextViewSet, basename="context")
