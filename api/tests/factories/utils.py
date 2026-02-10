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
