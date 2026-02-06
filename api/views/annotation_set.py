"""ViewSet for the AnnotationSet model."""

from rest_framework import viewsets

from api.models import AnnotationSet
from api.serializers import AnnotationSetSerializer


class AnnotationSetViewSet(viewsets.ModelViewSet):
    """ViewSet for the AnnotationSet model."""

    queryset = AnnotationSet.objects.all().order_by("id")
    serializer_class = AnnotationSetSerializer
