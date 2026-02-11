"""Serializer for the ImageSet model."""

from django.db import transaction
from rest_framework import serializers

from api.models import Creator, ImageSet, RelatedMaterial
from api.serializers.fields import (
    ContextSerializer,
    CreatorSerializer,
    EventSerializer,
    ImageCameraCalibrationModelSerializer,
    ImageCameraHousingViewportSerializer,
    ImageCameraPoseSerializer,
    ImageDomeportParameterSerializer,
    ImageFlatportParameterSerializer,
    ImagePhotometricCalibrationSerializer,
    LicenseSerializer,
    PISerializer,
    PlatformSerializer,
    ProjectSerializer,
    RelatedMaterialSerializer,
    SensorSerializer,
)

from .base import (
    BaseSerializer,
    CreateOnlyRelatedField,
    CreateOnlyRelatedListField,
    StrictPrimaryKeyRelatedField,
)

FK_PAIRS = [
    ("context", "context_id"),
    ("project", "project_id"),
    ("event", "event_id"),
    ("platform", "platform_id"),
    ("sensor", "sensor_id"),
    ("pi", "pi_id"),
    ("license", "license_id"),
    ("camera_pose", "camera_pose_id"),
    ("camera_housing_viewport", "camera_housing_viewport_id"),
    ("flatport_parameter", "flatport_parameter_id"),
    ("domeport_parameter", "domeport_parameter_id"),
    ("photometric_calibration", "photometric_calibration_id"),
    ("camera_calibration_model", "camera_calibration_model_id"),
    ("creators", "creators_ids"),
    ("related_materials", "related_materials_ids"),
]

GEOM_FIELDS = [
    "geom",
    "limits",
]


class ImageSetSerializer(BaseSerializer):
    """Serializer for the ImageSet model."""

    context_id = StrictPrimaryKeyRelatedField(
        source="context",
        queryset=ImageSet._meta.get_field("context").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    context = CreateOnlyRelatedField(
        create_serializer_class=ContextSerializer,
        write_only=True,
        required=False,
    )

    project_id = StrictPrimaryKeyRelatedField(
        source="project",
        queryset=ImageSet._meta.get_field("project").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )
    project = CreateOnlyRelatedField(
        create_serializer_class=ProjectSerializer,
        write_only=True,
        required=False,
    )

    event_id = StrictPrimaryKeyRelatedField(
        source="event",
        queryset=ImageSet._meta.get_field("event").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    event = CreateOnlyRelatedField(
        create_serializer_class=EventSerializer,
        write_only=True,
        required=False,
    )

    platform_id = StrictPrimaryKeyRelatedField(
        source="platform",
        queryset=ImageSet._meta.get_field("platform").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    platform = CreateOnlyRelatedField(
        create_serializer_class=PlatformSerializer,
        write_only=True,
        required=False,
    )

    sensor_id = StrictPrimaryKeyRelatedField(
        source="sensor",
        queryset=ImageSet._meta.get_field("sensor").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    sensor = CreateOnlyRelatedField(
        create_serializer_class=SensorSerializer,
        write_only=True,
        required=False,
    )

    pi_id = StrictPrimaryKeyRelatedField(
        source="pi",
        queryset=ImageSet._meta.get_field("pi").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    pi = CreateOnlyRelatedField(
        create_serializer_class=PISerializer,
        write_only=True,
        required=False,
    )

    license_id = StrictPrimaryKeyRelatedField(
        source="license",
        queryset=ImageSet._meta.get_field("license").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    license = CreateOnlyRelatedField(
        create_serializer_class=LicenseSerializer,
        write_only=True,
        required=False,
    )

    camera_pose_id = StrictPrimaryKeyRelatedField(
        source="camera_pose",
        queryset=ImageSet._meta.get_field("camera_pose").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    camera_pose = CreateOnlyRelatedField(
        create_serializer_class=ImageCameraPoseSerializer,
        write_only=True,
        required=False,
    )

    camera_housing_viewport_id = StrictPrimaryKeyRelatedField(
        source="camera_housing_viewport",
        queryset=ImageSet._meta.get_field("camera_housing_viewport").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    camera_housing_viewport = CreateOnlyRelatedField(
        create_serializer_class=ImageCameraHousingViewportSerializer,
        write_only=True,
        required=False,
    )

    flatport_parameter_id = StrictPrimaryKeyRelatedField(
        source="flatport_parameter",
        queryset=ImageSet._meta.get_field("flatport_parameter").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    flatport_parameter = CreateOnlyRelatedField(
        create_serializer_class=ImageFlatportParameterSerializer,
        write_only=True,
        required=False,
    )

    domeport_parameter_id = StrictPrimaryKeyRelatedField(
        source="domeport_parameter",
        queryset=ImageSet._meta.get_field("domeport_parameter").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    domeport_parameter = CreateOnlyRelatedField(
        create_serializer_class=ImageDomeportParameterSerializer,
        write_only=True,
        required=False,
    )

    photometric_calibration_id = StrictPrimaryKeyRelatedField(
        source="photometric_calibration",
        queryset=ImageSet._meta.get_field("photometric_calibration").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    photometric_calibration = CreateOnlyRelatedField(
        create_serializer_class=ImagePhotometricCalibrationSerializer,
        write_only=True,
        required=False,
    )

    camera_calibration_model_id = StrictPrimaryKeyRelatedField(
        source="camera_calibration_model",
        queryset=ImageSet._meta.get_field("camera_calibration_model").remote_field.model.objects.all(),
        required=False,
        allow_null=True,
    )

    camera_calibration_model = CreateOnlyRelatedField(
        create_serializer_class=ImageCameraCalibrationModelSerializer,
        write_only=True,
        required=False,
    )

    creators_ids = StrictPrimaryKeyRelatedField(
        source="creators",
        many=True,
        queryset=Creator.objects.all(),
        required=False,
    )

    creators = CreateOnlyRelatedListField(
        create_serializer_class=CreatorSerializer,
        write_only=True,
        required=False,
        source="_creators_deferred",
    )

    related_materials_ids = StrictPrimaryKeyRelatedField(
        source="related_materials",
        many=True,
        queryset=RelatedMaterial.objects.all(),
        required=False,
    )

    related_materials = CreateOnlyRelatedListField(
        create_serializer_class=RelatedMaterialSerializer,
        write_only=True,
        required=False,
        source="_related_materials_deferred",
    )

    class Meta:
        """Serializer for the ImageSet model."""

        model = ImageSet
        fields = [
            "id",
            "name",
            "handle",
            "copyright",
            "abstract",
            "objective",
            "target_environment",
            "target_timescale",
            "curation_protocol",
            "local_path",
            "min_latitude_degrees",
            "max_latitude_degrees",
            "min_longitude_degrees",
            "max_longitude_degrees",
            "sha256_hash",
            "date_time",
            "latitude",
            "longitude",
            "altitude_meters",
            "coordinate_uncertainty_meters",
            "entropy",
            "particle_count",
            "average_color",
            "mpeg7_color_layout",
            "mpeg7_color_statistic",
            "mpeg7_color_structure",
            "mpeg7_dominant_color",
            "mpeg7_edge_histogram",
            "mpeg7_homogeneous_texture",
            "mpeg7_scalable_color",
            "acquisition",
            "quality",
            "deployment",
            "navigation",
            "scale_reference",
            "illumination",
            "pixel_magnitude",
            "marine_zone",
            "spectral_resolution",
            "capture_mode",
            "fauna_attraction",
            "area_square_meters",
            "meters_above_ground",
            "acquisition_settings",
            "camera_yaw_degrees",
            "camera_pitch_degrees",
            "camera_roll_degrees",
            "overlap_fraction",
            "spatial_constraints",
            "temporal_constraints",
            "time_synchronisation",
            "item_identification_scheme",
            "visual_constraints",
            "context_id",
            "context",
            "project_id",
            "project",
            "event_id",
            "event",
            "platform_id",
            "platform",
            "sensor_id",
            "sensor",
            "pi_id",
            "pi",
            "license_id",
            "license",
            "camera_pose_id",
            "camera_pose",
            "camera_housing_viewport_id",
            "camera_housing_viewport",
            "flatport_parameter_id",
            "flatport_parameter",
            "domeport_parameter_id",
            "domeport_parameter",
            "photometric_calibration_id",
            "photometric_calibration",
            "camera_calibration_model_id",
            "camera_calibration_model",
            "creators_ids",
            "creators",
            "related_materials_ids",
            "related_materials",
        ]

    def validate(self, attrs) -> dict:
        """Perform cross-field validation to enforce constraints that can't be captured by field-level validation alone.

        Args:
            attrs: The dictionary of field values after field-level validation.

        Raise:
            serializers.ValidationError: If any of the cross-field validation rules are violated.

        Return:
            The validated attributes, if all checks pass.
        """
        errors = {}

        # forbid client from setting computed fields
        errors = self._validate_geom_fields(GEOM_FIELDS, errors)

        # forbid client from adding object + id together
        errors = self._validate_pairs(FK_PAIRS, errors)

        # validate min/max lat/lon logic
        errors = self._validate_min_max_lat_lon(attrs, errors)

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def _validate_min_max_lat_lon(self, attrs, errors):
        """Validate that min_latitude <= max_latitude and min_longitude <= max_longitude.

        Args:
            attrs: The dictionary of field values after field-level validation.
            errors: The dictionary of accumulated validation errors to which any new errors will be added.

        Return:
            The updated errors dictionary with any new errors added.
        """

        def get_val(name):
            if name in attrs:
                return attrs.get(name)
            if self.instance is not None:
                return getattr(self.instance, name)
            return None

        min_lat = get_val("min_latitude_degrees")
        max_lat = get_val("max_latitude_degrees")
        min_lon = get_val("min_longitude_degrees")
        max_lon = get_val("max_longitude_degrees")

        # Only validate each pair if both values are present (not None)
        if min_lat is not None and max_lat is not None and min_lat >= max_lat:
            errors["min_latitude_degrees"] = "Must be less than max_latitude_degrees."

        if min_lon is not None and max_lon is not None and min_lon >= max_lon:
            errors["min_longitude_degrees"] = "Must be less than max_longitude_degrees."

        return errors

    @transaction.atomic
    def create(self, validated_data) -> ImageSet:
        """Override create to handle nested creation of related objects and setting M2M relationships.

        Args:
            validated_data: The validated data from the serializer.

        Returns:
            The created ImageSet instance.
        """
        creators_deferred = validated_data.pop("_creators_deferred", None)
        related_deferred = validated_data.pop("_related_materials_deferred", None)

        self._materialize_deferred_related(validated_data, FK_PAIRS)

        instance = super().create(validated_data)

        if creators_deferred is not None:
            instance.creators.set(self._materialize_deferred_list(creators_deferred))

        if related_deferred is not None:
            instance.related_materials.set(self._materialize_deferred_list(related_deferred))

        return instance

    @transaction.atomic
    def update(self, instance, validated_data) -> ImageSet:
        """Override update to handle nested updates of related objects and setting M2M relationships.

        Args:
            instance: The existing ImageSet instance.
            validated_data: The validated data from the serializer.

        Returns:
            The updated ImageSet instance.
        """
        creators_deferred = validated_data.pop("_creators_deferred", None)
        related_deferred = validated_data.pop("_related_materials_deferred", None)

        self._materialize_deferred_related(validated_data, FK_PAIRS)

        instance = super().update(instance, validated_data)

        if creators_deferred is not None:
            instance.creators.set(self._materialize_deferred_list(creators_deferred))

        if related_deferred is not None:
            instance.related_materials.set(self._materialize_deferred_list(related_deferred))

        return instance
