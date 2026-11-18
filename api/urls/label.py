"""URL configuration for the Labels API endpoints."""

from rest_framework.routers import DefaultRouter

from api.views import LabelSetViewSet, LabelViewSet

router_label = DefaultRouter()
router_label.register(
    r"labels",
    LabelViewSet,
    basename="label",
)
router_label.register(
    r"label_sets",
    LabelSetViewSet,
    basename="label_set",
)
