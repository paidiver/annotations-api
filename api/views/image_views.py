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
from ..serializers.image_serializers import ImageCameraCalibrationModelSerializer


class ImageCameraCalibrationModelViewSet(viewsets.ModelViewSet):
    """ViewSet for the ImageCameraCalibrationModel model."""
    serializer_class = ImageCameraCalibrationModelSerializer
    queryset = ImageCameraCalibrationModel.objects.all()
