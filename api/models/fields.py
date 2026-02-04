"""Models for common named URI fields used across multiple models."""

from django.contrib.postgres.fields import ArrayField
from django.db import models

from .base import DefaultColumns


class NamedURI(DefaultColumns):
    """Mixin for models that have a name and a URI."""

    name = models.CharField(max_length=255, unique=True)
    uri = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        """Meta class for NamedURI."""

        abstract = True

    def __str__(self):
        """String representation of the instance."""
        return self.name


class Creator(NamedURI):
    """The creator of the images, image_sets or annotation_sets."""

    class Meta:
        """Meta class for Creator."""

        db_table = "creators"


class Context(NamedURI):
    """The context in which images were captured."""

    class Meta:
        """Meta class for Context."""

        db_table = "contexts"


class Project(NamedURI):
    """The project under which images were captured."""

    class Meta:
        """Meta class for Project."""

        db_table = "projects"


class PI(NamedURI):
    """The principal investigator associated with the images."""

    class Meta:
        """Meta class for PI."""

        db_table = "pis"


class License(NamedURI):
    """The license under which images are made available."""

    class Meta:  # noqa: D106

        db_table = "licenses"

class Event(NamedURI):
    """Represents an event related to image."""
    class Meta:  # noqa: D106
        db_table = "events"


class Platform(NamedURI):
    """Represents a platform on which an image was captured."""
    class Meta:  # noqa: D106
        db_table = "platforms"


class Sensor(NamedURI):
    """Represents a sensor used to capture an image."""
    class Meta:  # noqa: D106
        db_table = "sensors"


class RelatedMaterial(DefaultColumns):
    """Represents a related material for an image set."""

    uri = models.CharField(max_length=255, help_text="The URI pointing to a related resource")
    title = models.CharField(max_length=255, help_text="A name characterising the resource that is pointed to")
    relation = models.TextField(help_text="A textual explanation how this material is related to this image set")

    class Meta:  # noqa: D106
        db_table = "related_materials"

    def __str__(self) -> str:  # noqa: D105
        return self.title


class ImageCameraPose(DefaultColumns):
    """Camera pose information."""

    utm_zone = models.CharField(max_length=10, null=True, blank=True, help_text="The UTM zone number")
    utm_epsg = models.CharField(max_length=10, null=True, blank=True, help_text="The EPSG code of the UTM zone")

    utm_east_north_up_meters = ArrayField(
        base_field=models.FloatField(),
        null=True,
        blank=True,
        help_text="The position of the camera center in UTM coordinates.",
    )

    absolute_orientation_utm_matrix = ArrayField(
        base_field=models.FloatField(),
        null=True,
        blank=True,
        help_text=(
            "3x3 row-major float rotation matrix that transforms a direction in camera coordinates "
            "(x,y,z = right,down,line of sight) into a direction in UTM coordinates (x,y,z = easting,northing,up)"
        ),
    )

    class Meta:  # noqa: D106
        db_table = "image_camera_poses"


class ImageCameraHousingViewport(DefaultColumns):
    """Camera housing viewport parameters."""

    viewport_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="e.g.: flat port, dome port, other",
    )
    optical_density = models.FloatField(
        null=True,
        blank=True,
        help_text="Unit-less optical density (1.0=vacuum)",
    )
    thickness_millimeters = models.FloatField(
        null=True,
        blank=True,
        help_text="Thickness of viewport in millimeters",
    )
    extra_description = models.TextField(
        null=True,
        blank=True,
        help_text="A textual description of the viewport used",
    )

    class Meta:  # noqa: D106
        db_table = "image_camera_housing_viewports"


class ImageFlatportParameter(DefaultColumns):
    """Parameters of a flat port used in an image."""

    lens_port_distance_millimeters = models.FloatField(
        null=True,
        blank=True,
        help_text=(
            "Distance between the front of the camera lens and the inner side "
            "of the housing viewport in millimeters."
        ),
    )

    interface_normal_direction = ArrayField(
        base_field=models.FloatField(),
        null=True,
        blank=True,
        help_text=(
            "3D direction vector to specify how the view direction of the lens "
            "intersects with the viewport (unit-less, (0,0,1) is aligned)"
        ),
    )

    extra_description = models.TextField(null=True, blank=True, help_text="A textual description of the flat port used")

    class Meta:  # noqa: D106
        db_table = "image_flatport_parameters"


class ImageDomeportParameter(DefaultColumns):
    """Parameters of a dome port used in an image."""

    outer_radius_millimeters = models.FloatField(
        null=True,
        blank=True,
        help_text="Outer radius of the dome port - the part that has contact with the water.",
    )

    decentering_offset_xyz_millimeters = ArrayField(
        base_field=models.FloatField(),
        null=True,
        blank=True,
        help_text="3D offset vector of the camera center from the dome port center in millimeters",
    )

    extra_description = models.TextField(null=True, blank=True, help_text="A textual description of the dome port used")

    class Meta:  # noqa: D106
        db_table = "image_domeport_parameters"


class ImageCameraCalibrationModel(DefaultColumns):
    """Camera calibration model parameters."""

    calibration_model_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="e.g.: rectilinear air, rectilinear water, fisheye air, fisheye water, other",
    )

    focal_length_xy_pixel = ArrayField(
        base_field=models.FloatField(),
        null=True,
        blank=True,
        help_text="2D focal length in pixels",
    )

    principal_point_xy_pixel = ArrayField(
        base_field=models.FloatField(),
        null=True,
        blank=True,
        help_text="2D principal point in pixels (top left pixel center is 0,0, x right, y down)",
    )

    distortion_coefficients = ArrayField(
        base_field=models.FloatField(),
        null=True,
        blank=True,
        help_text="rectilinear: k1,k2,p1,p2,k3,k4,k5,k6; fisheye: k1,k2,k3,k4",
    )

    approximate_field_of_view_water_xy_degree = ArrayField(
        base_field=models.FloatField(),
        null=True,
        blank=True,
        help_text="Proxy for pixel to meter conversion, and as backup",
    )

    extra_description = models.TextField(
        null=True,
        blank=True,
        help_text="Explain model, or if lens parameters are in mm rather than in pixel",
    )

    class Meta:  # noqa: D106
        db_table = "image_camera_calibration_models"


class ImagePhotometricCalibration(DefaultColumns):
    """Photometric calibration parameters."""

    sequence_white_balancing = models.TextField(null=True, blank=True, help_text="How white-balancing was done.")

    exposure_factor_rgb = ArrayField(
        base_field=models.FloatField(),
        null=True,
        blank=True,
        help_text="RGB factors applied to this image (product of ISO, exposure time, relative white balance)",
    )

    sequence_illumination_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text=(
            "e.g. constant artificial, globally adapted artificial, "
            "individually varying light sources, sunlight, mixed"
        ),
    )

    sequence_illumination_description = models.TextField(
        null=True,
        blank=True,
        help_text="How the image sequence was illuminated",
    )

    illumination_factor_rgb = ArrayField(
        base_field=models.FloatField(),
        null=True,
        blank=True,
        help_text="RGB factors applied to artificial lights for this image",
    )

    water_properties_description = models.TextField(
        null=True,
        blank=True,
        help_text="Photometric properties of the water within which the images were captured",
    )

    class Meta:  # noqa: D106
        db_table = "image_photometric_calibrations"
