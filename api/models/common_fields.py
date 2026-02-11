"""Common fields module for models."""

from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator

from .base import (
    AcquisitionEnum,
    CaptureModeEnum,
    DeploymentEnum,
    FaunaAttractionEnum,
    IlluminationEnum,
    MarineZoneEnum,
    NavigationEnum,
    PixelMagnitudeEnum,
    QualityEnum,
    ScaleReferenceEnum,
    SpectralResEnum,
    enum_choices,
)


class CommonFieldsAll(models.Model):
    """Common fields used across multiple tables."""

    handle = models.CharField(
        max_length=2048,
        null=True,
        blank=True,
        help_text="A Handle URL to point to the landing page of the image set, image or annotation set.",
    )

    copyright = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Copyright statement or contact person or office for the image set, image or annotation set.",
    )

    abstract = models.TextField(
        null=True,
        blank=True,
        help_text=(
            "500 - 2000 characters describing what, when, where, why and how the data was collected/annotated. "
            "Includes general information on the event (aka station, experiment), e.g. overlap between "
            "images/frames, parameters on platform movement, aims, purpose of image capture etc."
        ),
    )

    objective = models.TextField(
        null=True,
        blank=True,
        help_text="A general description of the aims and objectives...",
    )

    target_environment = models.TextField(
        null=True,
        blank=True,
        help_text="A description of the habitat or environment...",
    )

    target_timescale = models.TextField(
        null=True,
        blank=True,
        help_text="A description of the period or temporal environment...",
    )

    curation_protocol = models.TextField(
        null=True,
        blank=True,
        help_text="A description of the image/annotation and metadata curation...",
    )

    class Meta:
        """Meta class for CommonFieldsAll."""

        abstract = True


class CommonFieldsImagesImageSets(models.Model):
    """Common fields for image_sets and images."""

    sha256_hash = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="An SHA256 hash to represent the whole file for integrity verification",
    )

    date_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="UTC time of image acquisition (or start time of a video)",
    )

    geom = models.PointField(
        srid=4326,
        null=True,
        blank=True,
        help_text="Geographic location of the center of the image set, in WGS84 coordinates (EPSG:4326)",
    )

    latitude = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        help_text="Latitude of the camera center in degrees, WGS84 coordinates (EPSG:4326)",
    )

    longitude = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
        help_text="Longitude of the camera center in degrees, WGS84 coordinates (EPSG:4326)",
    )

    altitude_meters = models.FloatField(
        null=True,
        blank=True,
        help_text="Z-coordinate of camera center in meters. Positive above sea level, negative below.",
    )

    coordinate_uncertainty_meters = models.FloatField(
        null=True,
        blank=True,
        help_text="The average/static uncertainty of coordinates in this image set, in meters.",
    )

    entropy = models.FloatField(
        null=True,
        blank=True,
        help_text="Information content of an image / frame according to Shannon entropy.",
    )

    particle_count = models.IntegerField(
        null=True,
        blank=True,
        help_text="Counts of single particles/objects in an image / frame",
    )

    average_color = ArrayField(
        base_field=models.FloatField(),
        null=True,
        blank=True,
        help_text=(
            "The average colour for each image / frame and the n channels of an image (e.g. 3 for RGB). "
            "The values are in the range 0-255."
        ),
    )

    mpeg7_color_layout = ArrayField(
        models.FloatField(),
        null=True,
        blank=True,
        help_text="An nD feature vector per image / frame...",
    )
    mpeg7_color_statistic = ArrayField(
        models.FloatField(),
        null=True,
        blank=True,
        help_text="An nD feature vector per image / frame...",
    )
    mpeg7_color_structure = ArrayField(
        models.FloatField(),
        null=True,
        blank=True,
        help_text="An nD feature vector per image / frame...",
    )
    mpeg7_dominant_color = ArrayField(
        models.FloatField(),
        null=True,
        blank=True,
        help_text="An nD feature vector per image / frame...",
    )
    mpeg7_edge_histogram = ArrayField(
        models.FloatField(),
        null=True,
        blank=True,
        help_text="An nD feature vector per image / frame...",
    )
    mpeg7_homogeneous_texture = ArrayField(
        models.FloatField(),
        null=True,
        blank=True,
        help_text="An nD feature vector per image / frame...",
    )
    mpeg7_scalable_color = ArrayField(
        models.FloatField(),
        null=True,
        blank=True,
        help_text="An nD feature vector per image / frame...",
    )

    acquisition = models.CharField(
        max_length=50,
        choices=enum_choices(AcquisitionEnum),
        null=True,
        blank=True,
    )
    quality = models.CharField(
        max_length=50,
        choices=enum_choices(QualityEnum),
        null=True,
        blank=True,
    )
    deployment = models.CharField(
        max_length=50,
        choices=enum_choices(DeploymentEnum),
        null=True,
        blank=True,
    )
    navigation = models.CharField(
        max_length=50,
        choices=enum_choices(NavigationEnum),
        null=True,
        blank=True,
    )
    scale_reference = models.CharField(
        max_length=50,
        choices=enum_choices(ScaleReferenceEnum),
        null=True,
        blank=True,
    )
    illumination = models.CharField(
        max_length=50,
        choices=enum_choices(IlluminationEnum),
        null=True,
        blank=True,
    )
    pixel_magnitude = models.CharField(
        max_length=50,
        choices=enum_choices(PixelMagnitudeEnum),
        null=True,
        blank=True,
    )
    marine_zone = models.CharField(
        max_length=50,
        choices=enum_choices(MarineZoneEnum),
        null=True,
        blank=True,
    )
    spectral_resolution = models.CharField(
        max_length=50,
        choices=enum_choices(SpectralResEnum),
        null=True,
        blank=True,
    )
    capture_mode = models.CharField(
        max_length=50,
        choices=enum_choices(CaptureModeEnum),
        null=True,
        blank=True,
    )
    fauna_attraction = models.CharField(
        max_length=50,
        choices=enum_choices(FaunaAttractionEnum),
        null=True,
        blank=True,
    )

    area_square_meters = models.FloatField(null=True, blank=True)
    meters_above_ground = models.FloatField(null=True, blank=True)

    acquisition_settings = models.JSONField(null=True, blank=True)

    camera_yaw_degrees = models.FloatField(null=True, blank=True)
    camera_pitch_degrees = models.FloatField(null=True, blank=True)
    camera_roll_degrees = models.FloatField(null=True, blank=True)

    overlap_fraction = models.FloatField(null=True, blank=True)

    spatial_constraints = models.TextField(null=True, blank=True)
    temporal_constraints = models.TextField(null=True, blank=True)
    time_synchronisation = models.TextField(null=True, blank=True)
    item_identification_scheme = models.TextField(null=True, blank=True)
    visual_constraints = models.TextField(null=True, blank=True)

    class Meta:
        """Meta class for CommonFieldsImagesImageSets."""

        abstract = True
