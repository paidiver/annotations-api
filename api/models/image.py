"""Models for images."""

from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point

from .base import DefaultColumns
from .common_fields import CommonFieldsAll, CommonFieldsImagesImageSets


class ImageCreator(gis_models.Model):
    """Through table for Image Creator."""

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

    class Meta:  # noqa: D106
        db_table = "image_creators"
        constraints = [
            gis_models.UniqueConstraint(
                fields=["image", "creator"],
                name="uq_image_creators",
            )
        ]


class Image(DefaultColumns, CommonFieldsAll, CommonFieldsImagesImageSets):
    """Represents an image in the database."""

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
        help_text=(
            "The more specific project or expedition or cruise or experiment or "
            "... within which the image set was created."
        ),
    )
    event = gis_models.ForeignKey(
        "Event",
        null=True,
        blank=True,
        on_delete=gis_models.SET_NULL,
        db_column="event_id",
        help_text=(
            "One event of a project or expedition or cruise or experiment or ... "
            "that led to the creation of this image set."
        ),
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
        related_name="images",
    )
    camera_housing_viewport = gis_models.ForeignKey(
        "ImageCameraHousingViewport",
        null=True,
        blank=True,
        on_delete=gis_models.PROTECT,
        db_column="camera_housing_viewport_id",
        related_name="images",
    )
    flatport_parameter = gis_models.ForeignKey(
        "ImageFlatportParameter",
        null=True,
        blank=True,
        on_delete=gis_models.PROTECT,
        db_column="flatport_parameter_id",
        related_name="images",
    )
    domeport_parameter = gis_models.ForeignKey(
        "ImageDomeportParameter",
        null=True,
        blank=True,
        on_delete=gis_models.PROTECT,
        db_column="domeport_parameter_id",
        related_name="images",
    )
    photometric_calibration = gis_models.ForeignKey(
        "ImagePhotometricCalibration",
        null=True,
        blank=True,
        on_delete=gis_models.PROTECT,
        db_column="photometric_calibration_id",
        related_name="images",
    )
    camera_calibration_model = gis_models.ForeignKey(
        "ImageCameraCalibrationModel",
        null=True,
        blank=True,
        on_delete=gis_models.PROTECT,
        db_column="camera_calibration_model_id",
        related_name="images",
    )

    # Required FK to ImageSet (CASCADE)
    image_set = gis_models.ForeignKey(
        "ImageSet",
        on_delete=gis_models.CASCADE,
        db_column="image_set_id",
        related_name="images",
        help_text="The image_set this image belongs to. A image_set can have multiple images.",
    )

    class Meta:  # noqa: D106
        db_table = "images"

    def save(self, *args, **kwargs):  # noqa: D102
        if self.latitude is not None and self.longitude is not None:
            self.geom = Point(self.longitude, self.latitude, srid=4326)
        super().save(*args, **kwargs)

    def __str__(self) -> str:  # noqa: D105
        return self.name
