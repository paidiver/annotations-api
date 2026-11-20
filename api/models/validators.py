"""Reusable validators for model fields."""

import uuid
from urllib.parse import urlparse

from django.core.exceptions import ValidationError


def validate_uuid_or_uri(value: str) -> None:
    """Validate that a value is either a UUID or an absolute URI."""
    try:
        uuid.UUID(str(value))
        return
    except (ValueError, TypeError, AttributeError):
        parsed = urlparse(str(value))
        if parsed.scheme and (parsed.netloc or parsed.path):
            return
    raise ValidationError("Enter a valid UUID or absolute URI.", code="invalid_uuid_or_uri")


def validate_coco_rle_mask(value: dict | None) -> None:
    """Validate the expected structure of a COCO run-length encoded mask."""
    if value is None:
        return
    if not isinstance(value, dict):
        raise ValidationError("Mask must be a JSON object.", code="invalid_mask")

    required_keys = {"encoding", "width", "height", "counts"}
    missing_keys = required_keys - value.keys()
    if missing_keys:
        raise ValidationError(
            f"Mask is missing required keys: {', '.join(sorted(missing_keys))}.",
            code="invalid_mask",
        )
    if not isinstance(value["encoding"], str) or not value["encoding"]:
        raise ValidationError("Mask encoding must be a non-empty string.", code="invalid_mask")
    for dimension in ("width", "height"):
        if isinstance(value[dimension], bool) or not isinstance(value[dimension], int) or value[dimension] <= 0:
            raise ValidationError(f"Mask {dimension} must be a positive integer.", code="invalid_mask")
    if not isinstance(value["counts"], str | list):
        raise ValidationError("Mask counts must be a string or list.", code="invalid_mask")
