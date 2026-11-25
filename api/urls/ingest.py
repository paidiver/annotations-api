"""URL configuration for bulk data ingestion."""

from django.urls import path

from api.views.annotation import UploadAnnotationsView
from api.views.ingest_imagery import ingest_ifdo_image_set
from api.views.ingest_labels import UploadLabelsView

urlpatterns = [
    path("image-sets/", ingest_ifdo_image_set, name="ingest-image-sets"),
    path(
        "annotation-sets/",
        UploadAnnotationsView.as_view({"post": "create"}),
        name="ingest-annotation-sets",
    ),
    path(
        "label-sets/",
        UploadLabelsView.as_view({"post": "create"}),
        name="ingest-label-sets",
    ),
]
