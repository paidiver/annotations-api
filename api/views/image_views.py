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
from ..serializers.image_serializers import ImageCameraCalibrationModelSerializer, ImageCameraHousingViewportSerializer


class ImageCameraCalibrationModelViewSet(viewsets.ModelViewSet):
    """ViewSet for the ImageCameraCalibrationModel model."""
    serializer_class = ImageCameraCalibrationModelSerializer
    queryset = ImageCameraCalibrationModel.objects.all()


class ImageCameraHousingViewportViewSet(viewsets.ModelViewSet):
    """ViewSet for the ImageCameraHousingViewport model."""
    serializer_class = ImageCameraHousingViewportSerializer
    queryset = ImageCameraHousingViewport.objects.all()
