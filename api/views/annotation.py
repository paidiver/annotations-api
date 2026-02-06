"""ViewSet for the Annotation model."""

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from api.models import Annotation, AnnotationLabel, Annotator
from api.serializers import AnnotationLabelSerializer, AnnotationSerializer, AnnotatorSerializer


@extend_schema(tags=["Annotations API"])
class AnnotatorViewSet(viewsets.ModelViewSet):
    """ViewSet for the Annotator model."""

    queryset = Annotator.objects.all()
    serializer_class = AnnotatorSerializer


@extend_schema(tags=["Annotations API"])
class AnnotationViewSet(viewsets.ModelViewSet):
    """ViewSet for the Annotation model."""

    queryset = Annotation.objects.all().order_by("id")
    serializer_class = AnnotationSerializer


@extend_schema(tags=["Annotations API"])
class AnnotationLabelViewSet(viewsets.ModelViewSet):
    """ViewSet for the AnnotationLabel model."""

    queryset = AnnotationLabel.through.objects.all().order_by("id")
    serializer_class = AnnotationLabelSerializer
