"""API URL configuration module."""

from django.urls import include, path

from ..views import HealthView
from .annotation import router_annotation
from .annotation_set import router_annotation_set
from .image import router_image
from .image_set import router_image_set
from .label import router_label

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("image-set/", include(router_image_set.urls)),
    path("image/", include(router_image.urls)),
    path("annotation/", include(router_annotation.urls)),
    path("annotation-set/", include(router_annotation_set.urls)),
    path("label/", include(router_label.urls)),
]
