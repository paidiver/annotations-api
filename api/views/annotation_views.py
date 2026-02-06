"""Annotations API views."""

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from ..models.annotation import Annotator
from ..serializers.annotation_serializers import AnnotatorSerializer


@extend_schema(tags=["Annotations API"])
class AnnotatorViewSet(viewsets.ModelViewSet):
    """ViewSet for the Annotator model."""

    queryset = Annotator.objects.all()
    serializer_class = AnnotatorSerializer
