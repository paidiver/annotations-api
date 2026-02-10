"""Utility functions for test factories."""

import random


def rand_lat() -> float:
    """Generates a random latitude between -80 and 80 degrees (avoiding poles)."""
    return random.uniform(-80.0, 80.0)


def rand_lon() -> float:
    """Generates a random longitude between -180 and 180 degrees."""
    return random.uniform(-180.0, 180.0)


def bbox_around(lat: float, lon: float) -> tuple[float, float, float, float]:
    """Returns (min_lat, max_lat, min_lon, max_lon)."""
    dlat = random.uniform(0.001, 0.5)
    dlon = random.uniform(0.001, 0.5)
    min_lat = max(-90.0, lat - dlat)
    max_lat = min(90.0, lat + dlat)
    min_lon = max(-180.0, lon - dlon)
    max_lon = min(180.0, lon + dlon)
    return (min_lat, max_lat, min_lon, max_lon)


def vec3(min_v: float = -1.0, max_v: float = 1.0) -> list[float]:
    """Generates a list of 3 random floats between min_v and max_v."""
    return [random.uniform(min_v, max_v) for _ in range(3)]


def vec2(min_v: float = 0.0, max_v: float = 1.0) -> list[float]:
    """Generates a list of 2 random floats between min_v and max_v."""
    return [random.uniform(min_v, max_v) for _ in range(2)]


def pick_choice(model, field_name: str) -> str:
    """Pick a random value from a Django choices field."""
    choices = [c[0] for c in model._meta.get_field(field_name).choices]
    if not choices:
        raise ValueError(f"No choices defined for {model.__name__}.{field_name}")
    return random.choice(choices)


def coords_for_shape(shape: str) -> list[list[float]]:  # noqa: C901, PLR0911
    """Generate coordinates in your required format: [[x1,y1,x2,y2,...], ...].

    Shapes and minimum coords described in your docstring:
      - whole-image: 0
      - single-pixel: 2
      - circle: 3 (x,y,r)
      - ellipse/rectangle: 8
      - polyline: 4+
      - polygon: 8+ and first==last (closed)
    """
    # Use a simple pixel coordinate space
    W, H = 4000.0, 3000.0

    def xy() -> tuple[float, float]:
        return (random.uniform(0.0, W), random.uniform(0.0, H))

    if shape.lower() in {"whole-image", "whole_image", "wholeimage"}:
        return [[]]

    if shape.lower() in {"point", "single-pixel", "single_pixel", "pixel"}:
        x, y = xy()
        return [[x, y]]

    if shape.lower() == "circle":
        x, y = xy()
        r = random.uniform(1.0, min(W, H) / 10.0)
        return [[x, y, r]]

    if shape.lower() in {"rectangle", "bbox", "box"}:
        x1, y1 = xy()
        x2, y2 = xy()
        return [[x1, y1, x2, y1, x2, y2, x1, y2]]

    if shape.lower() in {"ellipse"}:
        # Use 8 values; you might interpret differently, but format is valid.
        x1, y1 = xy()
        x2, y2 = xy()
        x3, y3 = xy()
        x4, y4 = xy()
        return [[x1, y1, x2, y2, x3, y3, x4, y4]]

    if shape.lower() in {"polyline", "line"}:
        n_points = random.randint(2, 8)
        flat = []
        for _ in range(n_points):
            x, y = xy()
            flat.extend([x, y])
        return [flat]

    if shape.lower() in {"polygon"}:
        n_points = random.randint(4, 10)  # 4 points => 8 numbers, then closed
        points = [xy() for _ in range(n_points)]
        # Close polygon: append first point at end
        points.append(points[0])
        flat = []
        for x, y in points:
            flat.extend([x, y])
        return [flat]

    # Fallback: valid "polyline-like" coords
    n_points = random.randint(2, 6)
    flat = []
    for _ in range(n_points):
        x, y = xy()
        flat.extend([x, y])
    return [flat]
