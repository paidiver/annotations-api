"""Serializers for the Fields."""

from rest_framework import serializers

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
from api.serializers.base import NestedGetOrCreateMixin, ReadOnlyFieldsMixin


class CreatorSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for the Creator model."""

    key_field = "name"

    class Meta:
        """Meta class for CreatorSerializer."""

        model = Creator
        fields = "__all__"


class ContextSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for the Context model."""

    key_field = "name"

    class Meta:
        """Meta class for ContextSerializer."""

        model = Context
        fields = "__all__"


class ProjectSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for Project instances from object payloads."""

    key_field = "name"

    class Meta:
        """Meta class for ProjectSerializer."""

        model = Project
        fields = "__all__"


class PISerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for the PI model."""

    key_field = "name"

    class Meta:
        """Meta class for PISerializer."""

        model = PI
        fields = "__all__"


class LicenseSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for the License model."""

    key_field = "name"

    class Meta:
        """Meta class for LicenseSerializer."""

        model = License
        fields = "__all__"


class EventSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for the Event model."""

    key_field = "name"

    class Meta:
        """Meta class for EventSerializer."""

        model = Event
        fields = "__all__"


class PlatformSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for the Platform model."""

    key_field = "name"

    class Meta:
        """Meta class for PlatformSerializer."""

        model = Platform
        fields = "__all__"


class SensorSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for the Sensor model."""

    key_field = "name"

    class Meta:
        """Meta class for SensorSerializer."""

        model = Sensor
        fields = "__all__"


class RelatedMaterialSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for related material that can be represented by either an ID or an object payload."""

    class Meta:
        """Meta class for RelatedMaterialSerializer."""

        model = RelatedMaterial
        fields = "__all__"


class ImageCameraPoseSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for ImageCameraPose model."""

    class Meta:
        """Meta class for ImageCameraPoseSerializer."""

        model = ImageCameraPose
        fields = "__all__"


class ImageCameraHousingViewportSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for ImageCameraHousingViewport model."""

    class Meta:
        """Meta class for ImageCameraHousingViewportSerializer."""

        model = ImageCameraHousingViewport
        fields = "__all__"


class ImageFlatportParameterSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for ImageFlatportParameter model."""

    class Meta:
        """Meta class for ImageFlatportParameterSerializer."""

        model = ImageFlatportParameter
        fields = "__all__"


class ImageDomeportParameterSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for ImageDomeportParameter model."""

    class Meta:
        """Meta class for ImageDomeportParameterSerializer."""

        model = ImageDomeportParameter
        fields = "__all__"


class ImageCameraCalibrationModelSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for ImageCameraCalibrationModel model."""

    class Meta:
        """Meta class for ImageCameraCalibrationModelSerializer."""

        model = ImageCameraCalibrationModel
        fields = "__all__"


class ImagePhotometricCalibrationSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Serializer for ImagePhotometricCalibration model."""

    class Meta:
        """Meta class for ImagePhotometricCalibrationSerializer."""

        model = ImagePhotometricCalibration
        fields = "__all__"
