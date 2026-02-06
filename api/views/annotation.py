"""ViewSet for the Annotation model."""

from rest_framework import viewsets

from api.models import Annotation
from api.serializers import AnnotationSerializer


class AnnotationViewSet(viewsets.ModelViewSet):
    """ViewSet for the Annotation model."""

    queryset = Annotation.objects.all().order_by("id")
    serializer_class = AnnotationSerializer
