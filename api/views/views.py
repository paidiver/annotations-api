"""Viewsets classes for the API."""

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from ..models.fields import PI, Context, Creator, Event, License, Platform, Project, RelatedMaterial, Sensor
from ..serializers.serializers import (
    ContextSerializer,
    CreatorSerializer,
    EventSerializer,
    LicenseSerializer,
    PISerializer,
    PlatformSerializer,
    ProjectSerializer,
    RelatedMaterialSerializer,
    SensorSerializer,
)


class CreatorViewSet(viewsets.ViewSet):
    """ViewSet for the Creator model."""

    def get_queryset(self):
        """Get the queryset for the Creator model."""
        queryset = Creator.objects.all()
        return queryset

    def create(self, request) -> Response:
        """Create new creator object."""
        data = CreatorSerializer(data=request.data)
        if data.is_valid():
            creator = data.save()
            return Response(CreatorSerializer(creator).data, status=HTTP_201_CREATED)
        return Response(data.errors, status=HTTP_400_BAD_REQUEST)

    def list(self, request) -> Response:
        """List all creators."""
        serializer_class = CreatorSerializer(self.get_queryset(), many=True)
        return Response(serializer_class.data, status=HTTP_200_OK)

    def retrieve(self, request, pk: int=None) -> Response:
        """Get a specific creator by ID."""
        creator = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = CreatorSerializer(creator)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk: int=None) -> Response:
        """Update specific creator by id."""
        creator = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = CreatorSerializer(creator, data=request.data)
        if serializer.is_valid():
            updated_creator = serializer.save()
            return Response(CreatorSerializer(updated_creator).data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk: int=None) -> Response:
        """Delete creator by id."""
        creator = get_object_or_404(self.get_queryset(), pk=pk)
        creator.delete()
        return Response(status=HTTP_204_NO_CONTENT)

class ContextViewSet(viewsets.ModelViewSet):
    """ViewSet for the Context model."""

    queryset = Context.objects.all()
    serializer_class = ContextSerializer


class PIViewSet(viewsets.ModelViewSet):
    """ViewSet for the PI model."""

    queryset = PI.objects.all()
    serializer_class = PISerializer


class EventViewSet(viewsets.ModelViewSet):
    """ViewSet for the Event model."""

    queryset = Event.objects.all()
    serializer_class = EventSerializer


class LicenseViewSet(viewsets.ModelViewSet):
    """ViewSet for the License model."""

    queryset = License.objects.all()
    serializer_class = LicenseSerializer


class PlatformViewSet(viewsets.ModelViewSet):
    """ViewSet for the Platform model."""

    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for the Project model."""

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class SensorViewSet(viewsets.ModelViewSet):
    """ViewSet for the Sensor model."""

    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer


class RelatedMaterialViewSet(viewsets.ModelViewSet):
    """ViewSet for the RelatedMaterial model."""

    queryset = RelatedMaterial.objects.all()
    serializer_class = RelatedMaterialSerializer
