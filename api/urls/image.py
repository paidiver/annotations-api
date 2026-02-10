"""URL configuration for the Images API endpoints."""

from rest_framework.routers import DefaultRouter

from api.views import ImageViewSet

router_image = DefaultRouter()
router_image.register(
    r"images",
    ImageViewSet,
    basename="image",
)
