"""ViewSet for the Image model."""

from rest_framework import viewsets

from api.models import Image
from api.serializers import ImageSerializer


class ImageViewSet(viewsets.ModelViewSet):
    """ViewSet for the Image model."""

    queryset = Image.objects.all().order_by("id")
    serializer_class = ImageSerializer
