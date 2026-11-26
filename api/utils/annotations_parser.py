"""Parser functions for annotation-set submission workbooks."""

import json
from uuid import UUID, uuid4

import pandas as pd

ANNOTATION_SET_PAIRED_FIELDS = {
    "annotation-set-project",
    "annotation-set-context",
    "annotation-set-creators",
    "annotation-set-pi",
    "annotation-set-license",
}

REQUIRED_ANNOTATION_SET_FIELDS = {
    "annotation-set-name",
    "annotation-set-abstract",
    "annotation-set-objective",
    "annotation-set-creators",
    "annotation-set-pi",
    "annotation-set-license",
    "annotation-set-funding",
    "annotation-set-label-set-names",
    "annotation-set-label-set-uuids",
}

ANNOTATION_MODEL_DATA_START_ROW = 4
ANNOTATION_MODEL_DATA_START_COL = 1
ANNOTATION_MODEL_DATA_END_COL = 15

ANNOTATION_DATA_START_ROW = 4
ANNOTATION_DATA_START_COL = 1
ANNOTATION_DATA_END_COL = 21

SpreadsheetValue = str | int | float | bool | None


def _optional_string(value: SpreadsheetValue) -> str | None:
    """Return a stripped string, or None for an empty spreadsheet value."""
    if value is None or pd.isna(value):
        return None

    cleaned = str(value).strip()
    return cleaned or None


def _normalise_metadata_key(value: SpreadsheetValue) -> str | None:
    """Return a normalised annotation-set metadata key."""
    cleaned = _optional_string(value)
    return cleaned.lower() if cleaned is not None else None


def _normalise_enum_value(value: str | None) -> str | None:
    """Normalise an optional case-insensitive enum value."""
    return value.lower() if value is not None else None


def _normalise_enum_values(value: SpreadsheetValue) -> list[str] | None:
    """Normalise a comma-separated list of optional enum values."""
    values = _split_comma_separated(value)
    return [item.lower() for item in values] or None


def _split_comma_separated(value: SpreadsheetValue) -> list[str]:
    """Split a comma-separated spreadsheet value into cleaned strings."""
    cleaned = _optional_string(value)
    if cleaned is None:
        return []

    return [item.strip() for item in cleaned.split(",") if item.strip()]


def _parse_optional_uuid(
    value: SpreadsheetValue,
    row_number: int,
    field_name: str,
) -> UUID | None:
    """Parse an optional UUID spreadsheet value."""
    cleaned = _optional_string(value)
    if cleaned is None:
        return None

    try:
        return UUID(cleaned)
    except ValueError as exc:
        raise ValueError(f"Validation error at row {row_number}: " f"{field_name} must be a valid UUID.") from exc


def _parse_optional_probability(
    value: SpreadsheetValue,
    row_number: int,
    field_name: str,
) -> float | None:
    """Parse an optional numeric value constrained to zero through one."""
    cleaned = _optional_string(value)
    if cleaned is None:
        return None

    try:
        parsed_value = float(cleaned)
    except ValueError as exc:
        raise ValueError(f"Validation error at row {row_number}: " f"{field_name} must be a number.") from exc

    if not 0 <= parsed_value <= 1:
        raise ValueError(f"Validation error at row {row_number}: " f"{field_name} must be between 0 and 1.")

    return parsed_value


def _parse_uuid_list(
    value: SpreadsheetValue,
    row_number: int,
    field_name: str,
) -> list[UUID]:
    """Parse a comma-separated list of UUID values."""
    parsed_values = []

    for item in _split_comma_separated(value):
        parsed_value = _parse_optional_uuid(item, row_number, field_name)
        if parsed_value is not None:
            parsed_values.append(parsed_value)

    return parsed_values


def _named_uri(
    name: str | None,
    uri: str | None,
    field_name: str,
) -> dict | None:
    """Build a nested named-URI serializer value."""
    if name is None:
        if uri is not None:
            raise ValueError(f"{field_name} has a URI but no corresponding name.")
        return None

    if uri is None:
        return {"name": name}

    return {"name": name, "uri": uri}


def _extract_annotation_set_values(
    annotation_set_df: pd.DataFrame,
) -> tuple[dict[str, str | None], dict[str, str | None], dict[str, int]]:
    """Extract primary and paired values from the metadata worksheet."""
    primary_values = {}
    paired_values = {}
    row_numbers = {}
    current_key = None

    for excel_row, (_, row) in enumerate(
        annotation_set_df.iloc[:, :2].iterrows(),
        start=1,
    ):
        key = _normalise_metadata_key(row.iloc[0])
        value = _optional_string(row.iloc[1])

        if key == "attribute name":
            current_key = None
            continue

        if key is not None:
            current_key = key
            primary_values[key] = value
            row_numbers[key] = excel_row
            continue

        if current_key in ANNOTATION_SET_PAIRED_FIELDS:
            paired_values[current_key] = value
            current_key = None

    return primary_values, paired_values, row_numbers


def _validate_matching_references(
    names: list[str],
    identifiers: list[UUID],
    field_name: str,
    *,
    identifiers_required: bool,
) -> None:
    """Validate paired names and UUIDs from annotation-set metadata."""
    if identifiers_required and not identifiers:
        raise ValueError(f"{field_name} UUIDs are required.")

    if identifiers and (identifiers_required or names) and len(names) != len(identifiers):
        raise ValueError(f"The number of {field_name} UUIDs must match " f"the number of names.")


def parse_annotation_set_metadata(
    annotation_set_df: pd.DataFrame,
) -> tuple[UUID, dict, dict]:
    """Parse annotation-set metadata and its external references."""
    values, paired_values, row_numbers = _extract_annotation_set_values(annotation_set_df)

    missing_fields = [field_name for field_name in REQUIRED_ANNOTATION_SET_FIELDS if values.get(field_name) is None]
    if missing_fields:
        raise ValueError("Missing required annotation-set metadata: " + ", ".join(sorted(missing_fields)))

    annotation_set_id = (
        _parse_optional_uuid(
            values.get("annotation-set-uuid"),
            row_numbers.get("annotation-set-uuid", 1),
            "annotation-set-uuid",
        )
        or uuid4()
    )

    creator_names = _split_comma_separated(values["annotation-set-creators"])
    creator_uris = _split_comma_separated(paired_values.get("annotation-set-creators"))

    if creator_uris and len(creator_names) != len(creator_uris):
        raise ValueError("The number of annotation-set creator URIs must match " "the number of creator names.")

    creators = [
        _named_uri(
            name,
            creator_uris[index] if creator_uris else None,
            "annotation-set-creators",
        )
        for index, name in enumerate(creator_names)
    ]

    pi_uris = _split_comma_separated(paired_values.get("annotation-set-pi"))
    if len(pi_uris) > 1:
        raise ValueError("annotation-set-pi must have no more than one URI.")

    project = _named_uri(
        values.get("annotation-set-project"),
        paired_values.get("annotation-set-project"),
        "annotation-set-project",
    )
    context = _named_uri(
        values.get("annotation-set-context"),
        paired_values.get("annotation-set-context"),
        "annotation-set-context",
    )
    pi = _named_uri(
        values.get("annotation-set-pi"),
        pi_uris[0] if pi_uris else None,
        "annotation-set-pi",
    )
    license_data = _named_uri(
        values.get("annotation-set-license"),
        paired_values.get("annotation-set-license"),
        "annotation-set-license",
    )

    image_set_names = _split_comma_separated(values.get("annotation-set-image-set-name"))
    image_set_ids = _parse_uuid_list(
        values.get("annotation-set-image-set-uuids"),
        row_numbers.get("annotation-set-image-set-uuids", 1),
        "annotation-set-image-set-UUIDs",
    )
    image_set_handles = _split_comma_separated(values.get("annotation-set-image-set-handles"))

    _validate_matching_references(
        image_set_names,
        image_set_ids,
        "annotation-set image-set",
        identifiers_required=False,
    )

    image_set_reference_count = len(image_set_names) or len(image_set_ids)
    if image_set_handles and image_set_reference_count and image_set_reference_count != len(image_set_handles):
        raise ValueError("The number of annotation-set image-set handles must match " "the number of names or UUIDs.")

    label_set_names = _split_comma_separated(values.get("annotation-set-label-set-names"))
    label_set_ids = _parse_uuid_list(
        values.get("annotation-set-label-set-uuids"),
        row_numbers["annotation-set-label-set-uuids"],
        "annotation-set-label-set-UUIDs",
    )

    _validate_matching_references(
        label_set_names,
        label_set_ids,
        "annotation-set label-set",
        identifiers_required=True,
    )

    connected_set_ids = _parse_uuid_list(
        values.get("annotation-set-connected-set-uuids"),
        row_numbers.get("annotation-set-connected-set-uuids", 1),
        "annotation-set-connected-set-UUIDs",
    )

    related_materials = [{"uri": uri} for uri in _split_comma_separated(values.get("annotation-set-related-material"))]

    obis_handles = _split_comma_separated(values.get("annotation-set-obis-handles"))

    payload = {
        "name": values["annotation-set-name"],
        "abstract": values["annotation-set-abstract"],
        "objective": values["annotation-set-objective"],
        "creators": creators,
        "pi": pi,
        "license": license_data,
        "funding": values["annotation-set-funding"],
    }

    optional_fields = {
        "handle": values.get("annotation-set-handle"),
        "copyright": values.get("annotation-set-copyright"),
        "project": project,
        "context": context,
        "connected_set_ids": connected_set_ids or None,
        "machine_scope": values.get("annotation-set-machine-scope"),
        "related_materials": related_materials or None,
        "quantitative_or_qualitative": _normalise_enum_values(values.get("annotation-set-quantitative-or-qualitative")),
        "quantification_type": _normalise_enum_values(values.get("annotation-set-quantification-type")),
        "biological_metrics": values.get("annotation-set-biological-metrics"),
        "biological_stats": values.get("annotation-set-biological-stats"),
        "obis_handles": obis_handles or None,
    }

    payload.update({field_name: value for field_name, value in optional_fields.items() if value is not None})

    references = {
        "image_set_names": image_set_names,
        "image_set_ids": image_set_ids,
        "image_set_handles": image_set_handles,
        "label_set_names": label_set_names,
        "label_set_ids": label_set_ids,
    }

    return annotation_set_id, payload, references


def parse_annotation_models(
    annotation_models_df: pd.DataFrame,
) -> list[dict]:
    """Parse models registered for an annotation set."""
    data = annotation_models_df.iloc[
        ANNOTATION_MODEL_DATA_START_ROW:,
        ANNOTATION_MODEL_DATA_START_COL:ANNOTATION_MODEL_DATA_END_COL,
    ].copy()

    data.columns = [
        "model_id",
        "name",
        "version",
        "task",
        "handle",
        "weights_sha256",
        "description",
        "score_type",
        "confidence_threshold",
        "label_set_id",
        "training_image_set",
        "training_annotation_set",
        "validation_image_set",
        "validation_annotation_set",
    ]

    models = []
    seen_model_ids = set()

    for excel_row, (_, row) in enumerate(
        data.iterrows(),
        start=ANNOTATION_MODEL_DATA_START_ROW + 1,
    ):
        row_has_data = any(_optional_string(value) is not None for value in row)
        if not row_has_data:
            continue

        model_id = _optional_string(row["model_id"])
        name = _optional_string(row["name"])
        version = _optional_string(row["version"])
        task = _normalise_enum_value(_optional_string(row["task"]))

        missing_fields = [
            field_name
            for field_name, value in {
                "annotation-model-id": model_id,
                "annotation-model-name": name,
                "annotation-model-version": version,
                "annotation-model-task": task,
            }.items()
            if value is None
        ]
        if missing_fields:
            raise ValueError(
                f"Validation error at row {excel_row}: missing required " f"model fields: {', '.join(missing_fields)}."
            )

        if model_id in seen_model_ids:
            raise ValueError(f"Validation error at row {excel_row}: " f"duplicate annotation-model-id '{model_id}'.")
        seen_model_ids.add(model_id)

        models.append(
            {
                "model_id": model_id,
                "name": name,
                "version": version,
                "task": task,
                "handle": _optional_string(row["handle"]),
                "weights_sha256": _optional_string(row["weights_sha256"]),
                "description": _optional_string(row["description"]),
                "score_type": _optional_string(row["score_type"]),
                "confidence_threshold": _parse_optional_probability(
                    row["confidence_threshold"],
                    excel_row,
                    "annotation-model-confidence-threshold",
                ),
                "label_set_id": _parse_optional_uuid(
                    row["label_set_id"],
                    excel_row,
                    "annotation-model-label-set-uuid",
                ),
                "training_image_set": _optional_string(row["training_image_set"]),
                "training_annotation_set": _optional_string(row["training_annotation_set"]),
                "validation_image_set": _optional_string(row["validation_image_set"]),
                "validation_annotation_set": _optional_string(row["validation_annotation_set"]),
            }
        )

    return models


def _optional_nullable_string(
    value: SpreadsheetValue,
) -> str | None:
    """Return None for common spreadsheet null markers."""
    cleaned = _optional_string(value)
    if cleaned is None:
        return None

    if cleaned.lower() in {"na", "n/a", "none", "null"}:
        return None

    return cleaned


def _parse_optional_number(
    value: SpreadsheetValue,
    row_number: int,
    field_name: str,
) -> float | None:
    """Parse an optional numeric spreadsheet value."""
    cleaned = _optional_nullable_string(value)
    if cleaned is None:
        return None

    try:
        return float(cleaned)
    except ValueError as exc:
        raise ValueError(f"Validation error at row {row_number}: " f"{field_name} must be a number.") from exc


def _coordinates_are_numeric(value: object) -> bool:
    """Return whether a coordinate structure contains only numbers."""
    if not isinstance(value, list):
        return False

    if all(isinstance(item, int | float) for item in value):
        return True

    return all(
        isinstance(item, list) and all(isinstance(coordinate, int | float) for coordinate in item) for item in value
    )


def _parse_coordinates(
    value: SpreadsheetValue,
    row_number: int,
) -> list | None:
    """Parse optional JSON or comma-separated annotation coordinates."""
    cleaned = _optional_nullable_string(value)
    if cleaned is None:
        return None

    try:
        if cleaned.startswith("["):
            coordinates = json.loads(cleaned)
        else:
            coordinates = [float(coordinate.strip()) for coordinate in cleaned.split(",")]
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Validation error at row {row_number}: " "annotation-coordinates must contain valid numeric coordinates."
        ) from exc

    if not _coordinates_are_numeric(coordinates):
        raise ValueError(f"Validation error at row {row_number}: " "annotation-coordinates must be a numeric array.")

    return coordinates


def _parse_mask(
    value: SpreadsheetValue,
    row_number: int,
) -> dict | None:
    """Parse an optional COCO RLE mask JSON object."""
    cleaned = _optional_nullable_string(value)
    if cleaned is None:
        return None

    try:
        mask = json.loads(cleaned)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"Validation error at row {row_number}: " "annotation-mask must be valid JSON.") from exc

    if not isinstance(mask, dict):
        raise ValueError(f"Validation error at row {row_number}: " "annotation-mask must be a JSON object.")

    return mask


def parse_annotation_data(  # noqa: C901
    annotation_df: pd.DataFrame,
) -> list[dict]:
    """Parse annotation records from the v3 annotation worksheet."""
    data = annotation_df.iloc[
        ANNOTATION_DATA_START_ROW:,
        ANNOTATION_DATA_START_COL:ANNOTATION_DATA_END_COL,
    ].copy()

    data.columns = [
        "id",
        "image_filename",
        "image_id",
        "human_or_machine",
        "creator_name",
        "creator_uri",
        "creation_datetime",
        "label_name",
        "shape",
        "coordinates",
        "dimension_pixels",
        "human_reviewer_name",
        "human_reviewer_uri",
        "machine_training_validation",
        "additional_info",
        "detection_model_ref",
        "classification_model_ref",
        "detection_confidence",
        "classification_confidence",
        "mask",
    ]

    annotations = []
    seen_annotation_ids = set()

    for excel_row, (_, row) in enumerate(
        data.iterrows(),
        start=ANNOTATION_DATA_START_ROW + 1,
    ):
        row_has_data = any(_optional_string(value) is not None for value in row)
        if not row_has_data:
            continue

        annotation_id = _parse_optional_uuid(
            row["id"],
            excel_row,
            "annotation-uuid",
        )
        image_filename = _optional_string(row["image_filename"])
        image_id = _parse_optional_uuid(
            row["image_id"],
            excel_row,
            "image-UUID",
        )
        human_or_machine = _normalise_enum_value(_optional_string(row["human_or_machine"]))
        label_name = _optional_string(row["label_name"])
        shape = _normalise_enum_value(_optional_string(row["shape"]))

        missing_fields = [
            field_name
            for field_name, value in {
                "annotation-uuid": annotation_id,
                "annotation-human-or-machine": human_or_machine,
                "annotation-label-name": label_name,
                "annotation-shape-name": shape,
            }.items()
            if value is None
        ]
        if missing_fields:
            raise ValueError(
                f"Validation error at row {excel_row}: missing required "
                f"annotation fields: {', '.join(missing_fields)}."
            )

        if image_id is None and image_filename is None:
            raise ValueError(
                f"Validation error at row {excel_row}: " "either image-UUID or image-filename is required."
            )

        if annotation_id in seen_annotation_ids:
            raise ValueError(f"Validation error at row {excel_row}: " f"duplicate annotation-uuid '{annotation_id}'.")
        seen_annotation_ids.add(annotation_id)

        valid_creator_types = {
            "human",
            "algorithm",
            "combination",
        }
        if human_or_machine not in valid_creator_types:
            raise ValueError(
                f"Validation error at row {excel_row}: "
                "annotation-human-or-machine must be human, "
                "algorithm or combination."
            )

        creator_name = _optional_nullable_string(row["creator_name"])
        creator_uri = _optional_nullable_string(row["creator_uri"])

        if human_or_machine != "algorithm" and creator_name is None:
            raise ValueError(
                f"Validation error at row {excel_row}: "
                "annotation-creator is required for human and "
                "combination annotations."
            )

        creator = _named_uri(
            creator_name,
            creator_uri,
            "annotation-creator",
        )

        human_reviewer = _named_uri(
            _optional_nullable_string(row["human_reviewer_name"]),
            _optional_nullable_string(row["human_reviewer_uri"]),
            "annotation-human-reviewer",
        )

        detection_model_ref = _optional_nullable_string(row["detection_model_ref"])
        classification_model_ref = _optional_nullable_string(row["classification_model_ref"])

        if (
            human_or_machine in {"algorithm", "combination"}
            and detection_model_ref is None
            and classification_model_ref is None
        ):
            raise ValueError(
                f"Validation error at row {excel_row}: an algorithm or "
                "combination annotation requires a detection or "
                "classification model."
            )

        mask = _parse_mask(row["mask"], excel_row)
        if shape == "mask" and mask is None:
            raise ValueError(
                f"Validation error at row {excel_row}: " "annotation-mask is required when the shape is mask."
            )

        annotations.append(
            {
                "id": annotation_id,
                "image_id": image_id,
                "image_filename": image_filename,
                "human_or_machine": human_or_machine,
                "creator": creator,
                "creation_datetime": _optional_nullable_string(row["creation_datetime"]),
                "label_name": label_name,
                "shape": shape,
                "coordinates": _parse_coordinates(
                    row["coordinates"],
                    excel_row,
                ),
                "dimension_pixels": _parse_optional_number(
                    row["dimension_pixels"],
                    excel_row,
                    "annotation-measurement",
                ),
                "human_reviewer": human_reviewer,
                "machine_training_validation": _normalise_enum_value(
                    _optional_nullable_string(row["machine_training_validation"])
                ),
                "additional_info": _optional_nullable_string(row["additional_info"]),
                "detection_model_ref": detection_model_ref,
                "classification_model_ref": classification_model_ref,
                "detection_confidence": _parse_optional_probability(
                    row["detection_confidence"],
                    excel_row,
                    "annotation-detection-confidence",
                ),
                "classification_confidence": _parse_optional_probability(
                    row["classification_confidence"],
                    excel_row,
                    "annotation-classification-confidence",
                ),
                "mask": mask,
            }
        )

    if not annotations:
        raise ValueError("No annotations were found in the annotation-attributes worksheet.")

    return annotations
