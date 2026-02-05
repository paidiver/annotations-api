"""Base models and enumerations for the API."""

import enum
import uuid

from django.contrib.gis.db import models


class DefaultColumns(models.Model):
    """Abstract base model with default columns."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class for DefaultColumns."""

        abstract = True


class DefaultColumnsGis(models.Model):
    """Abstract base model with default columns."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class for DefaultColumns."""

        abstract = True


def enum_choices(py_enum: type[enum.Enum]):
    """Convert a Python Enum into Django choices.

    Args:
        py_enum: The Python Enum class to convert.

    Returns:
        A list of tuples suitable for Django model field 'choices' parameter.
    """
    return [(e.value, e.name) for e in py_enum]


class CaseInsensitiveEnum(str, enum.Enum):
    """Base Enum that allows case-insensitive matching."""

    @classmethod
    def _missing_(cls, value: str) -> "CaseInsensitiveEnum | None":
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class ShapeEnum(str, enum.Enum):
    """Enumeration of possible annotation shapes."""

    single_pixel = "single-pixel"
    polyline = "polyline"
    polygon = "polygon"
    circle = "circle"
    rectangle = "rectangle"
    ellipse = "ellipse"
    whole_image = "whole-image"


class AcquisitionEnum(CaseInsensitiveEnum):
    """Enumeration for acquisition types in the system."""

    photo = "photo"
    video = "video"
    slide = "slide"


class NavigationEnum(CaseInsensitiveEnum):
    """Enumeration for navigation types in the system."""

    satellite = "satellite"
    beacon = "beacon"
    transponder = "transponder"
    reconstructed = "reconstructed"


class ScaleReferenceEnum(CaseInsensitiveEnum):
    """Enumeration for scale references in the system."""

    camera_3d = "3D camera"
    camera_calibrated = "calibrated camera"
    laser_marker = "laser marker"
    optical_flow = "optical flow"


class IlluminationEnum(CaseInsensitiveEnum):
    """Enumeration for illumination types in the system."""

    sunlight = "sunlight"
    artificial_light = "artificial light"
    mixed_light = "mixed light"


class PixelMagnitudeEnum(CaseInsensitiveEnum):
    """Enumeration for pixel magnitude types in the system."""

    km = "km"
    hm = "hm"
    dam = "dam"
    m = "m"
    cm = "cm"
    mm = "mm"
    um = "µm"  # keep the same value as upstream


class MarineZoneEnum(CaseInsensitiveEnum):
    """Enumeration for marine zones in the system."""

    seafloor = "seafloor"
    water_column = "water column"
    sea_surface = "sea surface"
    atmosphere = "atmosphere"
    laboratory = "laboratory"


class SpectralResEnum(CaseInsensitiveEnum):
    """Enumeration for spectral resolution types in the system."""

    grayscale = "grayscale"
    rgb = "rgb"
    multi_spectral = "multi-spectral"
    hyper_spectral = "hyper-spectral"


class CaptureModeEnum(CaseInsensitiveEnum):
    """Enumeration for capture modes in the system."""

    timer = "timer"
    manual = "manual"
    mixed = "mixed"


class FaunaAttractionEnum(CaseInsensitiveEnum):
    """Enumeration for fauna attraction methods in the system."""

    none = "none"
    baited = "baited"
    light = "light"


class DeploymentEnum(CaseInsensitiveEnum):
    """Enumeration for deployment types in the system."""

    mapping = "mapping"
    stationary = "stationary"
    survey = "survey"
    exploration = "exploration"
    experiment = "experiment"
    sampling = "sampling"


class QualityEnum(CaseInsensitiveEnum):
    """Enumeration for quality types in the system."""

    raw = "raw"
    processed = "processed"
    product = "product"
