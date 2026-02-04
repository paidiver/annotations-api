"""Models for images."""

from django.contrib.gis.db import models as gis_models
from django.contrib.gis.db.models import indexes as gis_indexes
from django.contrib.gis.geos import Point

from .base import DefaultColumns
from .common_fields import CommonFieldsAll, CommonFieldsImagesImageSets


class ImageCreator(gis_models.Model):
    """Through table for Image <-> Creator.

    Mirrors SQLAlchemy: image_creators association table.
    """

    image = gis_models.ForeignKey(
        "Image",
        on_delete=gis_models.CASCADE,
        db_column="image_id",
    )
    creator = gis_models.ForeignKey(
        "Creator",
        on_delete=gis_models.CASCADE,
        db_column="creator_id",
    )

    class Meta:
        db_table = "image_creators"
        constraints = [
            gis_models.UniqueConstraint(
                fields=["image", "creator"],
                name="image_creators_pkey",
            )
        ]


class Image(DefaultColumns, CommonFieldsAll, CommonFieldsImagesImageSets):
    """Represents an image in the database."""

    # SET NULL FKs (ondelete="SET NULL")
    context = gis_models.ForeignKey(
        "Context",
        null=True,
        blank=True,
        on_delete=gis_models.SET_NULL,
        db_column="context_id",
        help_text="The overarching project context within which the image set was created",
    )
    project = gis_models.ForeignKey(
        "Project",
        null=True,
        blank=True,
        on_delete=gis_models.SET_NULL,
        db_column="project_id",
        help_text="The more specific project or expedition or cruise or experiment or ... within which the image set was created.",
    )
    event = gis_models.ForeignKey(
        "Event",
        null=True,
        blank=True,
        on_delete=gis_models.SET_NULL,
        db_column="event_id",
        help_text="One event of a project or expedition or cruise or experiment or ... that led to the creation of this image set.",
    )
    platform = gis_models.ForeignKey(
        "Platform",
        null=True,
        blank=True,
        on_delete=gis_models.SET_NULL,
        db_column="platform_id",
        help_text="A URI pointing to a description of the camera platform used to create this image set",
    )
    sensor = gis_models.ForeignKey(
        "Sensor",
        null=True,
        blank=True,
        on_delete=gis_models.SET_NULL,
        db_column="sensor_id",
        help_text="A URI pointing to a description of the sensor used to create this image set.",
    )
    pi = gis_models.ForeignKey(
        "PI",
        null=True,
        blank=True,
        on_delete=gis_models.SET_NULL,
        db_column="pi_id",
        help_text="A URI pointing to a description of the principal investigator of the image set",
    )
    license = gis_models.ForeignKey(
        "License",
        null=True,
        blank=True,
        on_delete=gis_models.SET_NULL,
        db_column="license_id",
        help_text="A URI pointing to the license to use the data (should be FAIR, e.g. CC-BY or CC-0)",
    )

    # Many-to-many creators
    creators = gis_models.ManyToManyField(
        "Creator",
        through=ImageCreator,
        related_name="images",
        help_text="Information to identify the creators of the image set",
    )

    # Camera-related FKs (NO ACTION / RESTRICT-ish in SQL => PROTECT matches)
    camera_pose = gis_models.ForeignKey(
        "ImageCameraPose",
        null=True,
        blank=True,
        on_delete=gis_models.PROTECT,
        db_column="camera_pose_id",
    )
    camera_housing_viewport = gis_models.ForeignKey(
        "ImageCameraHousingViewport",
        null=True,
        blank=True,
        on_delete=gis_models.PROTECT,
        db_column="camera_housing_viewport_id",
    )
    flatport_parameter = gis_models.ForeignKey(
        "ImageFlatportParameter",
        null=True,
        blank=True,
        on_delete=gis_models.PROTECT,
        db_column="flatport_parameter_id",
    )
    domeport_parameter = gis_models.ForeignKey(
        "ImageDomeportParameter",
        null=True,
        blank=True,
        on_delete=gis_models.PROTECT,
        db_column="domeport_parameter_id",
    )
    photometric_calibration = gis_models.ForeignKey(
        "ImagePhotometricCalibration",
        null=True,
        blank=True,
        on_delete=gis_models.PROTECT,
        db_column="photometric_calibration_id",
    )
    camera_calibration_model = gis_models.ForeignKey(
        "ImageCameraCalibrationModel",
        null=True,
        blank=True,
        on_delete=gis_models.PROTECT,
        db_column="camera_calibration_model_id",
    )

    # Required FK to ImageSet (CASCADE)
    image_set = gis_models.ForeignKey(
        "ImageSet",
        on_delete=gis_models.CASCADE,
        db_column="image_set_id",
        related_name="images",
        help_text="The image_set this image belongs to. A image_set can have multiple images.",
    )

    class Meta:
        db_table = "images"
        indexes = [
            gis_indexes.GistIndex(fields=["geom"], name="idx_images_geom"),
        ]

    def save(self, *args, **kwargs):
        # Mirror SQLAlchemy _update_geom()
        if self.latitude is not None and self.longitude is not None:
            self.geom = Point(self.longitude, self.latitude, srid=4326)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    # --- Optional: Django versions of the SQLAlchemy helper methods ---

    def get_merged_field(self, field_name: str):
        """Return self.field or fallback to image_set.field if self.field is empty/None."""
        value = getattr(self, field_name, None)
        if value is not None and value not in ([], {}, ""):
            return value
        if self.image_set and hasattr(self.image_set, field_name):
            return getattr(self.image_set, field_name)
        return value

    def to_merged_dict(self) -> dict:
        """Return a dict of common fields with fallback to image_set values."""
        common_fields = [
            "handle",
            "context_id",
            "project_id",
            "event_id",
            "platform_id",
            "sensor_id",
            "pi_id",
            "license_id",
            "creators",
            "camera_pose_id",
            "camera_housing_viewport_id",
            "flatport_parameter_id",
            "domeport_parameter_id",
            "camera_calibration_model_id",
            "photometric_calibration_id",
            "sha256_hash",
            "date_time",
            "geom",
            "latitude",
            "longitude",
            "altitude_meters",
            "coordinate_uncertainty_meters",
            "copyright",
            "abstract",
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
            "objective",
            "target_environment",
            "target_timescale",
            "spatial_constraints",
            "temporal_constraints",
            "time_synchronisation",
            "item_identification_scheme",
            "curation_protocol",
            "visual_constraints",
        ]

        data = {field: self.get_merged_field(field) for field in common_fields}
        data["id"] = self.id
        data["name"] = self.name
        data["image_set_id"] = self.image_set_id
        return data
