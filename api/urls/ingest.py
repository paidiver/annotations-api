"""URL configuration for the Ingest endpoints."""

from django.urls import path

from api.views.ingest_imagery import ingest_ifdo_image_set

urlpatterns = [
    path("image-set", ingest_ifdo_image_set),
]
