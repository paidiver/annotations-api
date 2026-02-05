"""API URL configuration module."""

from django.urls import path

from ..views import AnnotationsView, HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("annotations/", AnnotationsView.as_view(), name="import"),
]
