"""App URLs for the API."""

from django.urls import include, path

from ..views.routes import router

urlpatterns = [
    path("", include(router.urls)),
]
