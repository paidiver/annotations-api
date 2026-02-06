"""Serializers for image-related models."""

from rest_framework import serializers

from ..models.fields import (
    ImageCameraCalibrationModel,
    ImageCameraHousingViewport,
    ImageCameraPose,
    ImageDomeportParameter,
    ImageFlatportParameter,
    ImagePhotometricCalibration,
)


class ImageCameraCalibrationModelSerializer(serializers.ModelSerializer):
    """Serializer for ImageCameraCalibrationModel model."""
    class Meta:
        """Meta class for ImageCameraCalibrationModelSerializer."""
        model = ImageCameraCalibrationModel
        fields = "__all__"

        # Set read-only fields
        read_only_fields = ["id", "created_at", "updated_at"]
