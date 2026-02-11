"""Utility functions for test factories."""

import random

from api.models.base import enum_choices


def rand_lat() -> float:
    """Generates a random latitude between -80 and 80 degrees (avoiding poles)."""
    return random.uniform(-80.0, 80.0)


def rand_lon() -> float:
    """Generates a random longitude between -180 and 180 degrees."""
    return random.uniform(-180.0, 180.0)


def bbox_around(lat: float, lon: float) -> tuple[float, float, float, float]:
    """Generates a random bounding box around a given latitude and longitude.

    Args:
        lat: The central latitude for the bounding box.
        lon: The central longitude for the bounding box.

    Returns:
        A tuple of (min_lat, max_lat, min_lon, max_lon) representing the bounding box.
    """
    dlat = random.uniform(0.001, 0.5)
    dlon = random.uniform(0.001, 0.5)
    min_lat = max(-90.0, lat - dlat)
    max_lat = min(90.0, lat + dlat)
    min_lon = max(-180.0, lon - dlon)
    max_lon = min(180.0, lon + dlon)
    return (min_lat, max_lat, min_lon, max_lon)


def vec3(min_v: float = -1.0, max_v: float = 1.0) -> list[float]:
    """Generates a list of 3 random floats between min_v and max_v.

    Args:
        min_v: Minimum value for each component (inclusive).
        max_v: Maximum value for each component (inclusive).

    Returns:
        A list of 3 random floats in the specified range.
    """
    return [random.uniform(min_v, max_v) for _ in range(3)]


def enum_choice(enum_cls) -> str | None:
    """Return a random .value from a Django-style Enum, or None.

    Args:
        enum_cls: An Enum class (e.g. AcquisitionEnum) with .value attributes.

    Returns:
        A random value from the enum, or None if the enum has no values.
    """
    values = enum_choices(enum_cls)
    return random.choice(values) if values else None


def coords_for_shape(shape: str) -> list[list[float]]:  # noqa: C901
    """Generate coordinates in your required format: [[x1,y1,x2,y2,...], ...].

    Shapes and minimum coords described in your docstring:
      - whole-image: 0
      - single-pixel: 2
      - circle: 3 (x,y,r)
      - ellipse/rectangle: 8
      - polyline: 4+
      - polygon: 8+ and first==last (closed)

    Args:
        shape: The shape type as a string (e.g. "circle", "polygon",
               "rectangle", "ellipse", "polyline", "single-pixel", "whole-image").

    Returns:
        A list of lists of floats representing coordinates. The outer list allows for multiple shapes.
    """
    width, height = 4000.0, 3000.0

    def xy() -> tuple[float, float]:
        return (random.uniform(0.0, width), random.uniform(0.0, height))

    if shape == "whole-image":
        output = [[]]
    elif shape == "single-pixel":
        x, y = xy()
        output = [[x, y]]
    elif shape == "circle":
        x, y = xy()
        r = random.uniform(1.0, min(width, height) / 10.0)
        output = [[x, y, r]]
    elif shape == "rectangle":
        x1, y1 = xy()
        x2, y2 = xy()
        output = [[x1, y1, x2, y1, x2, y2, x1, y2]]
    elif shape == "ellipse":
        x1, y1 = xy()
        x2, y2 = xy()
        x3, y3 = xy()
        x4, y4 = xy()
        output = [[x1, y1, x2, y2, x3, y3, x4, y4]]
    elif shape == "polyline":
        n_points = random.randint(2, 8)
        flat = []
        for _ in range(n_points):
            x, y = xy()
            flat.extend([x, y])
        output = [flat]
    elif shape == "polygon":
        n_points = random.randint(4, 10)
        points = [xy() for _ in range(n_points)]
        points.append(points[0])
        flat = []
        for x, y in points:
            flat.extend([x, y])
        output = [flat]
    else:
        raise ValueError(f"Unknown shape: {shape}")
    return output
