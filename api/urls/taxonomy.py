"""URL configuration for taxonomy lookups."""

from django.urls import path

from api.views.worms_cache import WormsTaxaViewSet

urlpatterns = [
    path("worms/taxa/", WormsTaxaViewSet.as_view({"get": "list"}), name="worms-taxa-list"),
]
