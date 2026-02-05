"""Docstring for api.models.image_set."""

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, Polygon

from .base import DefaultColumns
from .common_fields import CommonFieldsAll, CommonFieldsImagesImageSets


class ImageSetCreator(models.Model):
    """Through table for ImageSet Creator."""

    image_set = models.ForeignKey(
        "ImageSet",
        on_delete=models.CASCADE,
        db_column="image_set_id",
    )
    creator = models.ForeignKey(
        "Creator",
        on_delete=models.CASCADE,
        db_column="creator_id",
    )

    class Meta:  # noqa: D106
        db_table = "image_set_creators"
        constraints = [
            models.UniqueConstraint(
                fields=["image_set", "creator"],
                name="uq_image_set_creators",
            )
        ]


class ImageSetRelatedMaterial(models.Model):
    """Through table for ImageSet RelatedMaterial."""

    image_set = models.ForeignKey(
        "ImageSet",
        on_delete=models.CASCADE,
        db_column="image_set_id",
    )
    material = models.ForeignKey(
        "RelatedMaterial",
        on_delete=models.CASCADE,
        db_column="material_id",
    )

    class Meta:  # noqa: D106
        db_table = "image_set_related_materials"
        constraints = [
            models.UniqueConstraint(
                fields=["image_set", "material"],
                name="uq_image_set_related_materials",
            )
        ]


class ImageSet(CommonFieldsAll, CommonFieldsImagesImageSets, DefaultColumns):
    """A collection of images, videos, or other media files related to a specific project, event, or context."""

    # SET NULL FKs (ondelete="SET NULL")
    context = models.ForeignKey(
        "Context",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="context_id",
        related_name="image_sets",
        help_text="The overarching project context within which the image set was created",
    )
    project = models.ForeignKey(
        "Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="project_id",
        related_name="image_sets",
        help_text=(
            "The more specific project or expedition or cruise or experiment or ... "
            "within which the image set was created."
        ),
    )
    event = models.ForeignKey(
        "Event",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="event_id",
        related_name="image_sets",
        help_text=(
            "One event of a project or expedition or cruise or experiment or ... "
            "that led to the creation of this image set."
        ),
    )
    platform = models.ForeignKey(
        "Platform",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="platform_id",
        related_name="image_sets",
        help_text="A URI pointing to a description of the camera platform used to create this image set",
    )
    sensor = models.ForeignKey(
        "Sensor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="sensor_id",
        related_name="image_sets",
        help_text="A URI pointing to a description of the sensor used to create this image set.",
    )
    pi = models.ForeignKey(
        "PI",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="pi_id",
        related_name="image_sets",
        help_text="A URI pointing to a description of the principal investigator of the image set",
    )
    license = models.ForeignKey(
        "License",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="license_id",
        related_name="image_sets",
        help_text="A URI pointing to the license to use the data (should be FAIR, e.g. CC-BY or CC-0)",
    )

    # Many-to-many creators and related materials
    creators = models.ManyToManyField(
        "Creator",
        through=ImageSetCreator,
        related_name="image_sets",
        help_text="Information to identify the creators of the image set",
    )

    related_materials = models.ManyToManyField(
        "RelatedMaterial",
        through=ImageSetRelatedMaterial,
        related_name="image_sets",
    )

    camera_pose = models.ForeignKey(
        "ImageCameraPose",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="camera_pose_id",
        related_name="image_sets",
    )
    camera_housing_viewport = models.ForeignKey(
        "ImageCameraHousingViewport",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="camera_housing_viewport_id",
        related_name="image_sets",
    )
    flatport_parameter = models.ForeignKey(
        "ImageFlatportParameter",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="flatport_parameter_id",
        related_name="image_sets",
    )
    domeport_parameter = models.ForeignKey(
        "ImageDomeportParameter",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="domeport_parameter_id",
        related_name="image_sets",
    )
    photometric_calibration = models.ForeignKey(
        "ImagePhotometricCalibration",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="photometric_calibration_id",
        related_name="image_sets",
    )
    camera_calibration_model = models.ForeignKey(
        "ImageCameraCalibrationModel",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        db_column="camera_calibration_model_id",
        related_name="image_sets",
    )

    # ImageSet-specific fields
    local_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        default="../raw",
        help_text=(
            "Local relative or absolute path to a directory in which (also its sub-directories), the referenced "
            "image files are located. Absolute paths must start with and relative paths without path separator "
            "(ignoring drive letters on windows). The default is the relative path `../raw`."
        ),
    )

    min_latitude_degrees = models.FloatField(
        null=True,
        blank=True,
        help_text="The lower bounding box latitude...",
    )
    max_latitude_degrees = models.FloatField(
        null=True,
        blank=True,
        help_text="The upper bounding box latitude...",
    )
    min_longitude_degrees = models.FloatField(
        null=True,
        blank=True,
        help_text="The lower bounding box longitude...",
    )
    max_longitude_degrees = models.FloatField(
        null=True,
        blank=True,
        help_text="The upper bounding box longitude...",
    )

    limits = models.PolygonField(
        srid=4326,
        null=True,
        blank=True,
        help_text="Geographic bounding box of the image_set in WGS84 coordinates.",
    )

    class Meta:  # noqa: D106
        db_table = "image_sets"

    def save(self, *args, **kwargs):
        """Save method to update geom and limits fields."""
        if self.latitude is not None and self.longitude is not None:
            self.geom = Point(self.longitude, self.latitude, srid=4326)

        # Mirror _update_limits() using a bbox polygon
        if (
            self.min_latitude_degrees is not None
            and self.max_latitude_degrees is not None
            and self.min_longitude_degrees is not None
            and self.max_longitude_degrees is not None
        ):
            # Polygon.from_bbox expects (xmin, ymin, xmax, ymax)
            self.limits = Polygon.from_bbox(
                (
                    self.min_longitude_degrees,
                    self.min_latitude_degrees,
                    self.max_longitude_degrees,
                    self.max_latitude_degrees,
                )
            )
            self.limits.srid = 4326

        super().save(*args, **kwargs)

    def __str__(self) -> str:  # noqa: D105
        return self.name
