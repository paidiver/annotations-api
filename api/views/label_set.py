"""ViewSet for the Label model."""

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from api.models import LabelSet
from api.serializers import LabelSetSerializer

@extend_schema(tags=["Labels API"])
class LabelSetViewSet(viewsets.ModelViewSet):
    """ViewSet for the LabelSet model."""

    queryset = LabelSet.objects.all().order_by("id")
    serializer_class = LabelSetSerializer
