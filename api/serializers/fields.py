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


class BaseFieldsSerializer(NestedGetOrCreateMixin, ReadOnlyFieldsMixin, serializers.ModelSerializer):
    """Base serializer for the fields models, with common configuration and validation logic."""

    class Meta:
        """Meta class for BaseFieldsSerializer."""

        model = None  # This will be set by subclasses
        fields = "__all__"
        validators = []
        extra_kwargs = {"uri": {"required": False, "allow_null": True, "allow_blank": True}}


class CreatorSerializer(BaseFieldsSerializer):
    """Serializer for the Creator model."""

    class Meta(BaseFieldsSerializer.Meta):
        """Meta class for CreatorSerializer."""

        model = Creator


class ContextSerializer(BaseFieldsSerializer):
    """Serializer for the Context model."""

    class Meta(BaseFieldsSerializer.Meta):
        """Meta class for ContextSerializer."""

        model = Context


class ProjectSerializer(BaseFieldsSerializer):
    """Serializer for Project instances from object payloads."""

    class Meta(BaseFieldsSerializer.Meta):
        """Meta class for ProjectSerializer."""

        model = Project


class PISerializer(BaseFieldsSerializer):
    """Serializer for the PI model."""

    class Meta(BaseFieldsSerializer.Meta):
        """Meta class for PISerializer."""

        model = PI


class LicenseSerializer(BaseFieldsSerializer):
    """Serializer for the License model."""

    class Meta(BaseFieldsSerializer.Meta):
        """Meta class for LicenseSerializer."""

        model = License


class EventSerializer(BaseFieldsSerializer):
    """Serializer for the Event model."""

    class Meta(BaseFieldsSerializer.Meta):
        """Meta class for EventSerializer."""

        model = Event


class PlatformSerializer(BaseFieldsSerializer):
    """Serializer for the Platform model."""

    class Meta(BaseFieldsSerializer.Meta):
        """Meta class for PlatformSerializer."""

        model = Platform


class SensorSerializer(BaseFieldsSerializer):
    """Serializer for the Sensor model."""

    class Meta(BaseFieldsSerializer.Meta):
        """Meta class for SensorSerializer."""

        model = Sensor


class RelatedMaterialSerializer(BaseFieldsSerializer):
    """Serializer for related material that can be represented by either an ID or an object payload."""

    key_fields = ["uri", "title", "relation"]  # Override key_fields to use a combination of fields for uniqueness.

    class Meta(BaseFieldsSerializer.Meta):
        """Meta class for RelatedMaterialSerializer."""

        model = RelatedMaterial
        extra_kwargs = {
            "title": {"required": False, "allow_null": True, "allow_blank": True},
            "relation": {"required": False, "allow_null": True, "allow_blank": True},
        }


class ImageCameraPoseSerializer(BaseFieldsSerializer):
    """Serializer for ImageCameraPose model."""

    key_fields = None

    class Meta:
        """Meta class for ImageCameraPoseSerializer."""

        model = ImageCameraPose
        fields = "__all__"


class ImageCameraHousingViewportSerializer(BaseFieldsSerializer):
    """Serializer for ImageCameraHousingViewport model."""

    key_fields = None

    class Meta:
        """Meta class for ImageCameraHousingViewportSerializer."""

        model = ImageCameraHousingViewport
        fields = "__all__"


class ImageFlatportParameterSerializer(BaseFieldsSerializer):
    """Serializer for ImageFlatportParameter model."""

    key_fields = None

    class Meta:
        """Meta class for ImageFlatportParameterSerializer."""

        model = ImageFlatportParameter
        fields = "__all__"


class ImageDomeportParameterSerializer(BaseFieldsSerializer):
    """Serializer for ImageDomeportParameter model."""

    key_fields = None

    class Meta:
        """Meta class for ImageDomeportParameterSerializer."""

        model = ImageDomeportParameter
        fields = "__all__"


class ImageCameraCalibrationModelSerializer(BaseFieldsSerializer):
    """Serializer for ImageCameraCalibrationModel model."""

    key_fields = None

    class Meta:
        """Meta class for ImageCameraCalibrationModelSerializer."""

        model = ImageCameraCalibrationModel
        fields = "__all__"


class ImagePhotometricCalibrationSerializer(BaseFieldsSerializer):
    """Serializer for ImagePhotometricCalibration model."""

    key_fields = None

    class Meta:
        """Meta class for ImagePhotometricCalibrationSerializer."""

        model = ImagePhotometricCalibration
        fields = "__all__"
