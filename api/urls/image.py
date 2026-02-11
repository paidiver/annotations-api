"""URL configuration for the Images API endpoints."""

from rest_framework.routers import DefaultRouter

from api.views import ImageViewSet
from api.views.image_set import ImageSetViewSet

router_image = DefaultRouter()
# image relaed endpoints
router_image.register(
    r"images",
    ImageViewSet,
    basename="image",
)

# image set related endpoints
router_image.register(
    r"image_sets",
    ImageSetViewSet,
    basename="image_set",
)
