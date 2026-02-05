"""Routes for the API viewsets."""

from rest_framework.routers import DefaultRouter

from .views import CreatorViewSet

router = DefaultRouter()
router.register("creators", CreatorViewSet, basename="creator")
