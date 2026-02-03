"""Base models and enumerations for the API."""

import enum
import uuid

from django.db import models


class DefaultColumns(models.Model):
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
