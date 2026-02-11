"""ViewSet for the Label model."""

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from api.models import Label
from api.serializers import LabelSerializer


@extend_schema(tags=["Labels API"])
class LabelViewSet(viewsets.ModelViewSet):
    """ViewSet for the Label model."""

    queryset = Label.objects.all().order_by("id")
    serializer_class = LabelSerializer
