"""URL configuration for the ImageSet API endpoints."""

from rest_framework.routers import DefaultRouter

from api.views import ImageSetViewSet

router_image_set = DefaultRouter()
router_image_set.register(
    r"image_sets",
    ImageSetViewSet,
)
