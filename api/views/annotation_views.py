"""Annotations API views."""

from rest_framework import viewsets

from ..models.annotation import Annotator
from ..serializers.annotation_serializers import AnnotatorSerializer


class AnnotatorViewSet(viewsets.ModelViewSet):
    """ViewSet for the Annotator model."""

    queryset = Annotator.objects.all()
    serializer_class = AnnotatorSerializer
