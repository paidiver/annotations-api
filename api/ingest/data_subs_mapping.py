"""Functions to adapt incoming iFDO payloads into the shape expected by our DB models and serializers."""

from datetime import datetime
from typing import Any

import pandas as pd


class IFDOAdaptError(ValueError):
    """Raised when the incoming iFDO payload cannot be adapted safely."""


def _is_blank(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str):
        return v.strip() in {"", "null"}
    return False


def _require_str(v: Any, path: str) -> str:
    if not isinstance(v, str):
        raise IFDOAdaptError(f"{path} must be a string")
    s = v.strip()
    if not s:
        raise IFDOAdaptError(f"{path} is required")
    return s


def _maybe_str(v: Any) -> str | None:
    if _is_blank(v):
        return None
    if isinstance(v, str):
        s = v.strip()
        return s if s else None
    # if someone gives us a number etc, coerce to str (MVP-friendly)
    return str(v)


def _maybe_float(v: Any) -> float | None:
    if _is_blank(v):
        return None
    try:
        return float(v)
    except Exception:
        raise IFDOAdaptError(f"Expected a float-like value, got {v!r}") from None


def _maybe_int(v: Any) -> int | None:
    if _is_blank(v):
        return None
    try:
        return int(v)
    except Exception:
        raise IFDOAdaptError(f"Expected an int-like value, got {v!r}") from None


def _maybe_list(v: Any) -> list | None:
    if _is_blank(v):
        return None
    if isinstance(v, list):
        return v
    raise IFDOAdaptError(f"Expected a list, got {type(v).__name__}")


def _maybe_dict(v: Any) -> dict | None:
    if _is_blank(v):
        return None
    if isinstance(v, dict):
        return v
    raise IFDOAdaptError(f"Expected an object/dict, got {type(v).__name__}")

def _maybe_datetime(v: Any) -> datetime | None:
    if _is_blank(v):
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, str):
        # try pandas
        try:
            return pd.to_datetime(v, utc=True).to_pydatetime()
        except Exception:
            pass
        # try EXIF
        try:
            return datetime.strptime(v, "%Y:%m:%d %H:%M:%S%z")
        except Exception:
            raise IFDOAdaptError(f"Invalid datetime: {v!r}") from None
    raise IFDOAdaptError(f"Expected datetime-like value, got {type(v).__name__}")



def _named_uri_obj(v: Any, path: str) -> dict[str, Any] | None:
    """Convert iFDO object-ish fields into a nested serializer payload with name/uri.

    - If v is blank -> None
    - If v is dict -> require name, keep uri if present
    - If v is str -> treat as name (uri unknown)
    """
    if _is_blank(v):
        return None

    if isinstance(v, str):
        name = v.strip()
        if not name:
            return None
        return {"name": name}

    if isinstance(v, dict):
        name = _require_str(v.get("name"), f"{path}.name")
        out: dict[str, Any] = {"name": name}
        uri = _maybe_str(v.get("uri"))
        if uri:
            out["uri"] = uri
        return out

    raise IFDOAdaptError(f"{path} must be a string or object")


def _creator_list(v: Any, path: str) -> list[dict[str, Any]] | None:
    """image-creators should become nested creators list."""
    if _is_blank(v):
        return None
    if not isinstance(v, list):
        raise IFDOAdaptError(f"{path} must be a list")

    out: list[dict[str, Any]] = []
    for idx, item in enumerate(v):
        p = f"{path}[{idx}]"
        obj = _named_uri_obj(item, p)
        if obj is None:
            raise IFDOAdaptError(f"{p}.name is required")
        # creators are name-only in your mixin examples; if uri is present it's fine too
        out.append(obj)

    return out


def _related_materials(v: Any, path: str) -> list[dict[str, Any]] | None:
    """
    iFDO image-set-related-material is likely list-ish.
    Your serializer expects related_materials list of objects.
    We’ll pass through as-is if already list[dict], otherwise coerce list[str] -> [{name: str}].
    """
    if _is_blank(v):
        return None
    if not isinstance(v, list):
        raise IFDOAdaptError(f"{path} must be a list")

    out: list[dict[str, Any]] = []
    for idx, item in enumerate(v):
        p = f"{path}[{idx}]"
        if isinstance(item, dict):
            # best-effort: require at least name if present, else reject
            name = item.get("name")
            if name is None:
                raise IFDOAdaptError(f"{p}.name is required")
            out.append({"name": _require_str(name, f"{p}.name"), **{k: v for k, v in item.items() if k != "name"}})
        elif isinstance(item, str):
            out.append({"name": _require_str(item, f"{p}")})
        else:
            raise IFDOAdaptError(f"{p} must be an object or string")

    return out


def adapt_ifdo_image_set_to_serializer_payload(ifdo: dict[str, Any]) -> dict[str, Any]:
    """
    Convert incoming iFDO (image-set-header) into ImageSetSerializer input.

    This intentionally only maps what we know and what ImageSet model supports.
    Anything unknown is ignored (MVP).
    """
    header = _maybe_dict(ifdo.get("image-set-header")) or {}
    if not header:
        raise IFDOAdaptError("ifdo.image-set-header is required")

    # ImageSet.name is required and unique.
    # In iFDO, this comes from image-set-name.
    name = _require_str(header.get("image-set-name"), "ifdo.image-set-header.image-set-name")

    payload: dict[str, Any] = {
        "name": name,
        "handle": _maybe_str(header.get("image-set-handle")),
        "copyright": _maybe_str(header.get("image-copyright")),
        "abstract": _maybe_str(header.get("image-abstract")),
        "target_environment": _maybe_str(header.get("image-target-environment")),
        "time_synchronisation": _maybe_str(header.get("image-time-synchronisation")),
        "item_identification_scheme": _maybe_str(header.get("image-item-identification-scheme")),
        "visual_constraints": _maybe_str(header.get("image-visual-constraints")),
        "spatial_constraints": _maybe_str(header.get("image-spatial-constraints")) if "image-spatial-constraints" in header else None,
        "temporal_constraints": _maybe_str(header.get("image-temporal-constraints")) if "image-temporal-constraints" in header else None,
        "local_path": _maybe_str(header.get("image-set-local-path")) if "image-set-local-path" in header else None,  # optional if you ever add it
        "min_latitude_degrees": _maybe_float(header.get("image-set-min-latitude-degrees")),
        "max_latitude_degrees": _maybe_float(header.get("image-set-max-latitude-degrees")),
        "min_longitude_degrees": _maybe_float(header.get("image-set-min-longitude-degrees")),
        "max_longitude_degrees": _maybe_float(header.get("image-set-max-longitude-degrees")),
        "date_time": _maybe_datetime(header.get("image-set-start-datetime")),  # DRF DateTimeField can parse ISO strings
        "latitude": _maybe_float(header.get("image-latitude")),
        "longitude": _maybe_float(header.get("image-longitude")),
        "altitude_meters": _maybe_float(header.get("image-altitude-meters")),
        "coordinate_uncertainty_meters": _maybe_float(header.get("image-coordinate-uncertainty-meters")),
        "entropy": _maybe_float(header.get("image-entropy")),
        "particle_count": _maybe_int(header.get("image-particle-count")),
        "acquisition": _maybe_str(header.get("image-acquisition")),
        "quality": _maybe_str(header.get("image-quality")),
        "deployment": _maybe_str(header.get("image-deployment")),
        "navigation": _maybe_str(header.get("image-navigation")),
        "scale_reference": _maybe_str(header.get("image-scale-reference")),
        "illumination": _maybe_str(header.get("image-illumination")),
        "pixel_magnitude": _maybe_str(header.get("image-pixel-magnitude")),
        "marine_zone": _maybe_str(header.get("image-marine-zone")),
        "spectral_resolution": _maybe_str(header.get("image-spectral-resolution")),
        "capture_mode": _maybe_str(header.get("image-capture-mode")),
        "fauna_attraction": _maybe_str(header.get("image-fauna-attraction")),
        "area_square_meters": _maybe_float(header.get("image-area-square-meter")),
        "meters_above_ground": _maybe_float(header.get("image-meters-above-ground")),
        "acquisition_settings": _maybe_dict(header.get("image-acquisition-settings")),
        "camera_yaw_degrees": _maybe_float(header.get("image-camera-yaw-degrees")),
        "camera_pitch_degrees": _maybe_float(header.get("image-camera-pitch-degrees")),
        "camera_roll_degrees": _maybe_float(header.get("image-camera-roll-degrees")),
        "overlap_fraction": _maybe_float(header.get("image-overlap-fraction")),
    }

    # nested FK-ish objects
    payload["context"] = _named_uri_obj(header.get("image-context"), "ifdo.image-set-header.image-context")
    payload["project"] = _named_uri_obj(header.get("image-project"), "ifdo.image-set-header.image-project")
    payload["event"] = _named_uri_obj(header.get("image-event"), "ifdo.image-set-header.image-event")
    payload["platform"] = _named_uri_obj(header.get("image-platform"), "ifdo.image-set-header.image-platform")
    payload["sensor"] = _named_uri_obj(header.get("image-sensor"), "ifdo.image-set-header.image-sensor")
    payload["pi"] = _named_uri_obj(header.get("image-pi"), "ifdo.image-set-header.image-pi")
    payload["license"] = _named_uri_obj(header.get("image-license"), "ifdo.image-set-header.image-license")

    creators = _creator_list(header.get("image-creators"), "ifdo.image-set-header.image-creators")
    if creators is not None:
        payload["creators"] = creators

    related = _related_materials(header.get("image-set-related-material"), "ifdo.image-set-header.image-set-related-material")
    if related is not None:
        payload["related_materials"] = related

    # Drop keys where value is None so DRF doesn't complain about explicit nulls in some places
    return {k: v for k, v in payload.items() if v is not None}


def adapt_ifdo_item_to_image_serializer_payload(
    item: dict[str, Any],
    *,
    image_set_id: int,
) -> dict[str, Any]:
    """
    Convert one iFDO image-set-item dict into ImageSerializer input.

    We are intentionally MVP:
    - filename required
    - map shared fields where keys match our existing iFDO naming
    - attach image_set_id
    """
    filename = _require_str(item.get("image-filename"), "ifdo.image-set-items[].image-filename")

    payload: dict[str, Any] = {
        "filename": filename,
        "image_set_id": image_set_id,
        "handle": _maybe_str(item.get("image-handle")),
        "copyright": _maybe_str(item.get("image-copyright")),
        "sha256_hash": _maybe_str(item.get("image-hash-sha256")),
        "date_time": _maybe_datetime(item.get("image-datetime")),
        "latitude": _maybe_float(item.get("image-latitude")),
        "longitude": _maybe_float(item.get("image-longitude")),
        "altitude_meters": _maybe_float(item.get("image-altitude-meters")),
        "coordinate_uncertainty_meters": _maybe_float(item.get("image-coordinate-uncertainty-meters")),
        "entropy": _maybe_float(item.get("image-entropy")),
        "particle_count": _maybe_int(item.get("image-particle-count")),
        "average_color": _maybe_list(item.get("image-average-color")),
        "mpeg7_color_layout": _maybe_list(item.get("image-mpeg7-colorlayout")),
        "mpeg7_color_statistic": _maybe_list(item.get("image-mpeg7-colorstatistic")),
        "mpeg7_color_structure": _maybe_list(item.get("image-mpeg7-colorstructure")),
        "mpeg7_dominant_color": _maybe_list(item.get("image-mpeg7-dominantcolor")),
        "mpeg7_edge_histogram": _maybe_list(item.get("image-mpeg7-edgehistogram")),
        "mpeg7_homogeneous_texture": _maybe_list(item.get("image-mpeg7-homogeneoustexture")),
        "mpeg7_scalable_color": _maybe_list(item.get("image-mpeg7-scalablecolor")),
        "acquisition": _maybe_str(item.get("image-acquisition")),
        "quality": _maybe_str(item.get("image-quality")),
        "deployment": _maybe_str(item.get("image-deployment")),
        "navigation": _maybe_str(item.get("image-navigation")),
        "scale_reference": _maybe_str(item.get("image-scale-reference")),
        "illumination": _maybe_str(item.get("image-illumination")),
        "pixel_magnitude": _maybe_str(item.get("image-pixel-magnitude")),
        "marine_zone": _maybe_str(item.get("image-marine-zone")),
        "spectral_resolution": _maybe_str(item.get("image-spectral-resolution")),
        "capture_mode": _maybe_str(item.get("image-capture-mode")),
        "fauna_attraction": _maybe_str(item.get("image-fauna-attraction")),
        "area_square_meters": _maybe_float(item.get("image-area-square-meter")),
        "meters_above_ground": _maybe_float(item.get("image-meters-above-ground")),
        "acquisition_settings": _maybe_dict(item.get("image-acquisition-settings")),
        "camera_yaw_degrees": _maybe_float(item.get("image-camera-yaw-degrees")),
        "camera_pitch_degrees": _maybe_float(item.get("image-camera-pitch-degrees")),
        "camera_roll_degrees": _maybe_float(item.get("image-camera-roll-degrees")),
        "overlap_fraction": _maybe_float(item.get("image-overlap-fraction")),
        "camera_pose": _named_uri_obj(item.get("image-camera-pose"), "ifdo.image-set-items[].image-camera-pose"),
        "camera_housing_viewport": _named_uri_obj(
            item.get("image-camera-housing-viewport"), "ifdo.image-set-items[].image-camera-housing-viewport"
        ),
        "flatport_parameter": _named_uri_obj(item.get("image-flatport-parameters"), "ifdo.image-set-items[].image-flatport-parameters"),
        "domeport_parameter": _named_uri_obj(item.get("image-domeport-parameters"), "ifdo.image-set-items[].image-domeport-parameters"),
        "photometric_calibration": _named_uri_obj(
            item.get("image-photometric-calibration"), "ifdo.image-set-items[].image-photometric-calibration"
        ),
        "camera_calibration_model": _named_uri_obj(
            item.get("image-camera-calibration-model"), "ifdo.image-set-items[].image-camera-calibration-model"
        ),
    }

    # Optional nested objects if you ever include them per-image (most likely you won't, but allowed)
    payload["context"] = _named_uri_obj(item.get("image-context"), "ifdo.image-set-items[].image-context")
    payload["project"] = _named_uri_obj(item.get("image-project"), "ifdo.image-set-items[].image-project")
    payload["event"] = _named_uri_obj(item.get("image-event"), "ifdo.image-set-items[].image-event")
    payload["platform"] = _named_uri_obj(item.get("image-platform"), "ifdo.image-set-items[].image-platform")
    payload["sensor"] = _named_uri_obj(item.get("image-sensor"), "ifdo.image-set-items[].image-sensor")
    payload["pi"] = _named_uri_obj(item.get("image-pi"), "ifdo.image-set-items[].image-pi")
    payload["license"] = _named_uri_obj(item.get("image-license"), "ifdo.image-set-items[].image-license")

    creators = _creator_list(item.get("image-annotation-creators") or item.get("image-creators"), "ifdo.image-set-items[].image-creators")
    if creators is not None:
        payload["creators"] = creators

    return {k: v for k, v in payload.items() if v is not None}
