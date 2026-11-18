"""ViewSet for the AnnotationSet model."""

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from api.models import AnnotationSet, AnnotationSetModel
from api.serializers import AnnotationSetModelSerializer, AnnotationSetSerializer


@extend_schema(tags=["Annotations API"])
class AnnotationSetViewSet(viewsets.ModelViewSet):
    """ViewSet for the AnnotationSet model."""

    queryset = AnnotationSet.objects.all().order_by("id")
    serializer_class = AnnotationSetSerializer


@extend_schema(tags=["Annotations API"])
class AnnotationSetModelViewSet(viewsets.ModelViewSet):
    """ViewSet for the AnnotationSetModel model."""

    queryset = AnnotationSetModel.objects.all().order_by("id")
    serializer_class = AnnotationSetModelSerializer
