"""Image related view endpoints."""

from rest_framework import viewsets

from ..models.fields import (
    ImageCameraCalibrationModel,
    ImageCameraHousingViewport,
    ImageCameraPose,
    ImageDomeportParameter,
    ImageFlatportParameter,
    ImagePhotometricCalibration,
)
from ..serializers.image_serializers import (
    ImageCameraCalibrationModelSerializer,
    ImageCameraHousingViewportSerializer,
    ImageCameraPoseSerializer,
    ImageDomeportParameterSerializer,
    ImageFlatportParameterSerializer,
    ImagePhotometricCalibrationSerializer,
)


class ImageCameraCalibrationModelViewSet(viewsets.ModelViewSet):
    """ViewSet for the ImageCameraCalibrationModel model."""

    serializer_class = ImageCameraCalibrationModelSerializer
    queryset = ImageCameraCalibrationModel.objects.all()


class ImageCameraHousingViewportViewSet(viewsets.ModelViewSet):
    """ViewSet for the ImageCameraHousingViewport model."""

    serializer_class = ImageCameraHousingViewportSerializer
    queryset = ImageCameraHousingViewport.objects.all()


class ImageCameraPoseViewSet(viewsets.ModelViewSet):
    """ViewSet for the ImageCameraPose model."""

    serializer_class = ImageCameraPoseSerializer
    queryset = ImageCameraPose.objects.all()


class ImageDomeportParameterViewSet(viewsets.ModelViewSet):
    """ViewSet for the ImageDomeportParameter model."""

    serializer_class = ImageDomeportParameterSerializer
    queryset = ImageDomeportParameter.objects.all()


class ImageFlatportParameterViewSet(viewsets.ModelViewSet):
    """ViewSet for the ImageFlatportParameter model."""

    serializer_class = ImageFlatportParameterSerializer
    queryset = ImageFlatportParameter.objects.all()


class ImagePhotometricCalibrationViewSet(viewsets.ModelViewSet):
    """ViewSet for the ImagePhotometricCalibration model."""

    serializer_class = ImagePhotometricCalibrationSerializer
    queryset = ImagePhotometricCalibration.objects.all()
