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
from api.serializers.base import NestedGetOrCreateMixin

uri_fields = ["name", "uri"]


class CreatorSerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for the Creator model."""

    key_field = "name"

    class Meta:
        """Meta class for CreatorSerializer."""

        model = Creator
        fields = uri_fields


class ContextSerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for the Context model."""

    key_field = "name"

    class Meta:
        """Meta class for ContextSerializer."""

        model = Context
        fields = uri_fields


class ProjectSerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for Project instances from object payloads."""

    key_field = "name"

    class Meta:
        """Meta class for ProjectSerializer."""

        model = Project
        fields = uri_fields


class PISerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for the PI model."""

    key_field = "name"

    class Meta:
        """Meta class for PISerializer."""

        model = PI
        fields = uri_fields


class LicenseSerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for the License model."""

    key_field = "name"

    class Meta:
        """Meta class for LicenseSerializer."""

        model = License
        fields = uri_fields


class EventSerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for the Event model."""

    key_field = "name"

    class Meta:
        """Meta class for EventSerializer."""

        model = Event
        fields = uri_fields


class PlatformSerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for the Platform model."""

    key_field = "name"

    class Meta:
        """Meta class for PlatformSerializer."""

        model = Platform
        fields = uri_fields


class SensorSerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for the Sensor model."""

    key_field = "name"

    class Meta:
        """Meta class for SensorSerializer."""

        model = Sensor
        fields = uri_fields


class RelatedMaterialSerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for related material that can be represented by either an ID or an object payload."""

    class Meta:
        """Meta class for RelatedMaterialSerializer."""

        model = RelatedMaterial
        fields = ["uri", "title", "relation"]


class ImageCameraPoseSerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for ImageCameraPose model."""

    class Meta:
        """Meta class for ImageCameraPoseSerializer."""

        model = ImageCameraPose
        fields = ["utm_zone", "utm_epsg", "utm_east_north_up_meters", "absolute_orientation_utm_matrix"]


class ImageCameraHousingViewportSerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for ImageCameraHousingViewport model."""

    class Meta:
        """Meta class for ImageCameraHousingViewportSerializer."""

        model = ImageCameraHousingViewport
        fields = ["viewport_type", "optical_density", "thickness_millimeters", "extra_description"]


class ImageFlatportParameterSerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for ImageFlatportParameter model."""

    class Meta:
        """Meta class for ImageFlatportParameterSerializer."""

        model = ImageFlatportParameter
        fields = ["lens_port_distance_millimeters", "interface_normal_direction", "extra_description"]


class ImageDomeportParameterSerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for ImageDomeportParameter model."""

    class Meta:
        """Meta class for ImageDomeportParameterSerializer."""

        model = ImageDomeportParameter
        fields = ["outer_radius_millimeters", "decentering_offset_xyz_millimeters", "extra_description"]


class ImageCameraCalibrationModelSerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for ImageCameraCalibrationModel model."""

    class Meta:
        """Meta class for ImageCameraCalibrationModelSerializer."""

        model = ImageCameraCalibrationModel
        fields = [
            "calibration_model_type",
            "focal_length_xy_pixel",
            "principal_point_xy_pixel",
            "distortion_coefficients",
            "approximate_field_of_view_water_xy_degree",
            "extra_description",
        ]


class ImagePhotometricCalibrationSerializer(NestedGetOrCreateMixin, serializers.ModelSerializer):
    """Serializer for ImagePhotometricCalibration model."""

    class Meta:
        """Meta class for ImagePhotometricCalibrationSerializer."""

        model = ImagePhotometricCalibration
        fields = [
            "sequence_white_balancing",
            "exposure_factor_rgb",
            "sequence_illumination_type",
            "sequence_illumination_description",
            "illumination_factor_rgb",
            "water_properties_description",
        ]
