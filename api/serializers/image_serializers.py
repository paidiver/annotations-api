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


class ImageCameraHousingViewportSerializer(serializers.ModelSerializer):
    """Serializer for ImageCameraHousingViewport model."""

    class Meta:
        """Meta class for ImageCameraHousingViewportSerializer."""

        model = ImageCameraHousingViewport
        fields = "__all__"

        # Set read-only fields
        read_only_fields = ["id", "created_at", "updated_at"]


class ImageCameraPoseSerializer(serializers.ModelSerializer):
    """Serializer for ImageCameraPose model."""

    class Meta:
        """Meta class for ImageCameraPoseSerializer."""

        model = ImageCameraPose
        fields = "__all__"

        # Set read-only fields
        read_only_fields = ["id", "created_at", "updated_at"]


class ImagePhotometricCalibrationSerializer(serializers.ModelSerializer):
    """Serializer for ImagePhotometricCalibration model."""

    class Meta:
        """Meta class for ImagePhotometricCalibrationSerializer."""

        model = ImagePhotometricCalibration
        fields = "__all__"

        # Set read-only fields
        read_only_fields = ["id", "created_at", "updated_at"]


class ImageDomeportParameterSerializer(serializers.ModelSerializer):
    """Serializer for ImageDomeportParameter model."""

    class Meta:
        """Meta class for ImageDomeportParameterSerializer."""

        model = ImageDomeportParameter
        fields = "__all__"

        # Set read-only fields
        read_only_fields = ["id", "created_at", "updated_at"]


class ImageFlatportParameterSerializer(serializers.ModelSerializer):
    """Serializer for ImageFlatportParameter model."""

    class Meta:
        """Meta class for ImageFlatportParameterSerializer."""

        model = ImageFlatportParameter
        fields = "__all__"

        # Set read-only fields
        read_only_fields = ["id", "created_at", "updated_at"]
