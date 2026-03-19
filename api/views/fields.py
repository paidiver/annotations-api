"""Image related view endpoints."""

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


class CreatorViewSet(BaseFieldsViewSets):
    """ViewSet for the Creator model."""

    queryset = Creator.objects.all()
    serializer_class = CreatorSerializer


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
