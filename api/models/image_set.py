"""Docstring for api.models.image_set."""

from django.contrib.gis.db import models as gis_models
from django.contrib.gis.db.models import indexes as gis_indexes
from django.contrib.gis.geos import Point, Polygon

from .base import DefaultColumns
from .common_fields import CommonFieldsAll, CommonFieldsImagesImageSets


class ImageSetCreator(gis_models.Model):
    """Through table for ImageSet <-> Creator.

    Mirrors SQLAlchemy: image_set_creators association table.
    """

    image_set = gis_models.ForeignKey(
        "ImageSet",
        on_delete=gis_models.CASCADE,
        db_column="image_set_id",
    )
    creator = gis_models.ForeignKey(
        "Creator",
        on_delete=gis_models.CASCADE,
        db_column="creator_id",
    )

    class Meta:
        """Docstring for Meta."""
        db_table = "image_set_creators"
        constraints = [
            gis_models.UniqueConstraint(
                fields=["image_set", "creator"],
                name="image_set_creators_pkey",
            )
        ]


class ImageSetRelatedMaterial(gis_models.Model):
    """Through table for ImageSet <-> RelatedMaterial.

    Mirrors SQLAlchemy: image_set_related_materials association table.
    """

    image_set = gis_models.ForeignKey(
        "ImageSet",
        on_delete=gis_models.CASCADE,
        db_column="image_set_id",
    )
    material = gis_models.ForeignKey(
        "RelatedMaterial",
        on_delete=gis_models.CASCADE,
        db_column="material_id",
    )

    class Meta:
        db_table = "image_set_related_materials"
        constraints = [
            gis_models.UniqueConstraint(
                fields=["image_set", "material"],
                name="image_set_related_materials_pkey",
            )
        ]


class ImageSet(CommonFieldsAll, CommonFieldsImagesImageSets, DefaultColumns):
    """A collection of images, videos, or other media files related to a specific project, event, or context."""

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

    # Many-to-many creators and related materials
    creators = gis_models.ManyToManyField(
        "Creator",
        through=ImageSetCreator,
        related_name="image_sets",
        help_text="Information to identify the creators of the image set",
    )

    related_materials = gis_models.ManyToManyField(
        "RelatedMaterial",
        through=ImageSetRelatedMaterial,
        related_name="image_sets",
    )

    # Camera-related FKs (SQLAlchemy had no ondelete => default NO ACTION; PROTECT matches)
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

    # ImageSet-specific fields
    local_path = gis_models.CharField(
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

    min_latitude_degrees = gis_models.FloatField(null=True, blank=True, help_text="The lower bounding box latitude...")
    max_latitude_degrees = gis_models.FloatField(null=True, blank=True, help_text="The upper bounding box latitude...")
    min_longitude_degrees = gis_models.FloatField(null=True, blank=True, help_text="The lower bounding box longitude...")
    max_longitude_degrees = gis_models.FloatField(null=True, blank=True, help_text="The upper bounding box longitude...")

    limits = gis_models.PolygonField(
        srid=4326,
        null=True,
        blank=True,
        help_text="Geographic bounding box of the image_set in WGS84 coordinates.",
    )

    # Relationship to AnnotationSet (join table exists elsewhere)
    annotation_sets = gis_models.ManyToManyField(
        "AnnotationSet",
        through="AnnotationSetImageSet",  # name your through model to match the join table
        related_name="image_sets",
        help_text="Relationship to annotation sets that include this image_set.",
    )

    class Meta:
        db_table = "image_sets"
        indexes = [
            gis_indexes.GistIndex(fields=["geom"], name="idx_image_sets_geom"),
            gis_indexes.GistIndex(fields=["limits"], name="idx_image_sets_limits"),
        ]

    def save(self, *args, **kwargs):
        # Mirror _update_geom() from SQLAlchemy
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
                (self.min_longitude_degrees, self.min_latitude_degrees, self.max_longitude_degrees, self.max_latitude_degrees)
            )
            self.limits.srid = 4326

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
