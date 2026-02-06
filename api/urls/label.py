"""URL configuration for the Label API endpoints."""

from rest_framework.routers import DefaultRouter

from api.views import LabelViewSet

router_label = DefaultRouter()
router_label.register(
    r"",
    LabelViewSet,
)
