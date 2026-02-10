"""Image related view endpoints."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST

from api.models.fields import (
    PI,
    Context,
    Creator,
    Event,
    ImageCameraCalibrationModel,
    ImageCameraHousingViewport,
    ImageCameraPose,
    ImageDomeportParameter,
    ImageFlatportParameter,
    ImagePhotometricCalibration,
    License,
    Platform,
    Project,
    RelatedMaterial,
    Sensor,
)
from api.serializers import (
    ImageCameraCalibrationModelSerializer,
    ImageCameraHousingViewportSerializer,
    ImageCameraPoseSerializer,
    ImageDomeportParameterSerializer,
    ImageFlatportParameterSerializer,
    ImagePhotometricCalibrationSerializer,
)
from api.serializers.fields import (
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
from api.views.base import BaseFieldsViewSets


class ImageCameraCalibrationModelViewSet(BaseFieldsViewSets):
    """ViewSet for the ImageCameraCalibrationModel model."""

    serializer_class = ImageCameraCalibrationModelSerializer
    queryset = ImageCameraCalibrationModel.objects.all()


class ImageCameraHousingViewportViewSet(BaseFieldsViewSets):
    """ViewSet for the ImageCameraHousingViewport model."""

    serializer_class = ImageCameraHousingViewportSerializer
    queryset = ImageCameraHousingViewport.objects.all()


class ImageCameraPoseViewSet(BaseFieldsViewSets):
    """ViewSet for the ImageCameraPose model."""

    serializer_class = ImageCameraPoseSerializer
    queryset = ImageCameraPose.objects.all()


class ImageDomeportParameterViewSet(BaseFieldsViewSets):
    """ViewSet for the ImageDomeportParameter model."""

    serializer_class = ImageDomeportParameterSerializer
    queryset = ImageDomeportParameter.objects.all()


class ImageFlatportParameterViewSet(BaseFieldsViewSets):
    """ViewSet for the ImageFlatportParameter model."""

    serializer_class = ImageFlatportParameterSerializer
    queryset = ImageFlatportParameter.objects.all()


class ImagePhotometricCalibrationViewSet(BaseFieldsViewSets):
    """ViewSet for the ImagePhotometricCalibration model."""

    serializer_class = ImagePhotometricCalibrationSerializer
    queryset = ImagePhotometricCalibration.objects.all()


@extend_schema_view(
    create=extend_schema(
        summary="Create a new creator",
        tags=["Field Model API"],
    ),
    list=extend_schema(
        summary="List all creators",
        tags=["Field Model API"],
    ),
    retrieve=extend_schema(
        summary="Get a specific creator",
        tags=["Field Model API"],
    ),
    update=extend_schema(
        summary="Update a specific creator",
        tags=["Field Model API"],
    ),
    destroy=extend_schema(
        summary="Delete a specific creator",
        tags=["Field Model API"],
    ),
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

    def retrieve(self, request, pk: int = None) -> Response:
        """Get a specific creator by ID."""
        creator = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = CreatorSerializer(creator)
        return Response(serializer.data, status=HTTP_200_OK)

    def update(self, request, pk: int = None) -> Response:
        """Update specific creator by id."""
        creator = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = CreatorSerializer(creator, data=request.data)
        if serializer.is_valid():
            updated_creator = serializer.save()
            return Response(CreatorSerializer(updated_creator).data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk: int = None) -> Response:
        """Delete creator by id."""
        creator = get_object_or_404(self.get_queryset(), pk=pk)
        creator.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class ContextViewSet(BaseFieldsViewSets):
    """ViewSet for the Context model."""

    queryset = Context.objects.all()
    serializer_class = ContextSerializer


class PIViewSet(BaseFieldsViewSets):
    """ViewSet for the PI model."""

    queryset = PI.objects.all()
    serializer_class = PISerializer


class EventViewSet(BaseFieldsViewSets):
    """ViewSet for the Event model."""

    queryset = Event.objects.all()
    serializer_class = EventSerializer


class LicenseViewSet(BaseFieldsViewSets):
    """ViewSet for the License model."""

    queryset = License.objects.all()
    serializer_class = LicenseSerializer


class PlatformViewSet(BaseFieldsViewSets):
    """ViewSet for the Platform model."""

    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer


class ProjectViewSet(BaseFieldsViewSets):
    """ViewSet for the Project model."""

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class SensorViewSet(BaseFieldsViewSets):
    """ViewSet for the Sensor model."""

    queryset = Sensor.objects.all()
    serializer_class = SensorSerializer


class RelatedMaterialViewSet(BaseFieldsViewSets):
    """ViewSet for the RelatedMaterial model."""

    queryset = RelatedMaterial.objects.all()
    serializer_class = RelatedMaterialSerializer
