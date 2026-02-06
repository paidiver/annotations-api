"""URL configuration for the Image API endpoints."""

from rest_framework.routers import DefaultRouter

from api.views import ImageViewSet

router_image = DefaultRouter()
router_image.register(
    r"",
    ImageViewSet,
)
