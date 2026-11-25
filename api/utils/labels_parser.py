"""Parser functions for label-set submission workbooks."""

from uuid import UUID

import pandas as pd

LABEL_DATA_START_ROW = 4
LABEL_DATA_START_COL = 1
LABEL_DATA_END_COL = 8


LABEL_SET_PAIRED_FIELDS = {
    "label-set-project",
    "label-set-context",
    "label-set-creators",
    "label-set-pi",
    "label-set-license",
}

REQUIRED_LABEL_SET_FIELDS = {
    "label-set-name",
    "label-set-abstract",
    "label-set-objective",
    "label-set-creators",
    "label-set-pi",
    "label-set-license",
    "label-set-funding",
}

SpreadsheetValue = str | int | float | bool | None


def _optional_string(value: SpreadsheetValue) -> str | None:
    """Return a stripped string, or None for an empty spreadsheet value."""
    if value is None or pd.isna(value):
        return None

    cleaned = str(value).strip()
    return cleaned or None


def _parse_optional_integer(value: SpreadsheetValue, row_number: int, field_name: str) -> int | None:
    """Parse an optional integer spreadsheet value."""
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None

    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Validation error at row {row_number}: {field_name} must be an integer.") from exc

    if not numeric_value.is_integer():
        raise ValueError(f"Validation error at row {row_number}: {field_name} must be an integer.")

    return int(numeric_value)


def _parse_optional_boolean(value: SpreadsheetValue, row_number: int, field_name: str) -> bool | None:
    """Parse an optional boolean spreadsheet value."""
    cleaned = _optional_string(value)
    if cleaned is None:
        return None

    normalised = cleaned.lower()
    if normalised in {"yes", "true"}:
        return True
    if normalised in {"no", "false"}:
        return False

    raise ValueError(f"Validation error at row {row_number}: " f"{field_name} must be Yes, No, True or False.")


def _parse_optional_uuid(value: SpreadsheetValue, row_number: int, field_name: str) -> UUID | None:
    """Parse an optional UUID spreadsheet value."""
    cleaned = _optional_string(value)
    if cleaned is None:
        return None

    try:
        return UUID(cleaned)
    except ValueError as exc:
        raise ValueError(f"Validation error at row {row_number}: {field_name} must be a valid UUID.") from exc


def _split_comma_separated(value: SpreadsheetValue) -> list[str]:
    """Split a comma-separated spreadsheet value into cleaned strings."""
    cleaned = _optional_string(value)
    if cleaned is None:
        return []

    return [item.strip() for item in cleaned.split(",") if item.strip()]


def _extract_label_set_values(
    label_set_df: pd.DataFrame,
) -> tuple[dict[str, str | None], dict[str, str | None], dict[str, int]]:
    """Extract primary and paired values from the label-set worksheet."""
    primary_values = {}
    paired_values = {}
    row_numbers = {}
    current_key = None

    for excel_row, (_, row) in enumerate(
        label_set_df.iloc[:, :2].iterrows(),
        start=1,
    ):
        key = _optional_string(row.iloc[0])
        value = _optional_string(row.iloc[1])

        if key == "Attribute name":
            current_key = None
            continue

        if key is not None:
            current_key = key
            primary_values[key] = value
            row_numbers[key] = excel_row
            continue

        if current_key in LABEL_SET_PAIRED_FIELDS:
            paired_values[current_key] = value
            current_key = None

    return primary_values, paired_values, row_numbers


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

    return {
        "name": name,
        "uri": uri,
    }


def parse_label_set_metadata(
    label_set_df: pd.DataFrame,
) -> tuple[UUID | None, dict]:
    """Parse label-set metadata into a LabelSetSerializer payload."""
    values, paired_values, row_numbers = _extract_label_set_values(label_set_df)

    missing_fields = [field_name for field_name in REQUIRED_LABEL_SET_FIELDS if values.get(field_name) is None]
    if missing_fields:
        raise ValueError("Missing required label-set metadata: " + ", ".join(sorted(missing_fields)))

    label_set_id = _parse_optional_uuid(
        values["label-set-uuid"],
        row_numbers["label-set-uuid"],
        "label-set-uuid",
    )

    creator_names = _split_comma_separated(values["label-set-creators"])
    creator_uris = _split_comma_separated(paired_values.get("label-set-creators"))

    if creator_uris and len(creator_names) != len(creator_uris):
        raise ValueError("The number of label-set creator URIs must match " "the number of creator names.")

    creators = [
        {
            "name": name,
            "uri": creator_uris[index] if creator_uris else None,
        }
        for index, name in enumerate(creator_names)
    ]

    pi_uris = _split_comma_separated(paired_values.get("label-set-pi"))
    if len(pi_uris) > 1:
        raise ValueError("label-set-pi must have no more than one URI.")

    project = _named_uri(
        values.get("label-set-project"),
        paired_values.get("label-set-project"),
        "label-set-project",
    )
    context = _named_uri(
        values.get("label-set-context"),
        paired_values.get("label-set-context"),
        "label-set-context",
    )
    pi = _named_uri(
        values.get("label-set-pi"),
        pi_uris[0] if pi_uris else None,
        "label-set-pi",
    )
    license_data = _named_uri(
        values.get("label-set-license"),
        paired_values.get("label-set-license"),
        "label-set-license",
    )

    related_materials = [{"uri": uri} for uri in _split_comma_separated(values.get("label-set-related-material"))]

    payload = {
        "name": values["label-set-name"],
        "abstract": values["label-set-abstract"],
        "objective": values["label-set-objective"],
        "creators": creators,
        "pi": pi,
        "license": license_data,
        "funding": values["label-set-funding"],
    }

    optional_fields = {
        "handle": values.get("label-set-handle"),
        "copyright": values.get("label-set-copyright"),
        "catalogue": values.get("label-set-catalogue"),
        "project": project,
        "context": context,
        "related_materials": related_materials or None,
    }

    payload.update({field_name: value for field_name, value in optional_fields.items() if value is not None})

    return label_set_id, payload


def parse_labels(label_df: pd.DataFrame) -> list[dict]:
    """Parse label records from the label-attributes worksheet."""
    data = label_df.iloc[
        LABEL_DATA_START_ROW:,
        LABEL_DATA_START_COL:LABEL_DATA_END_COL,
    ].copy()

    data.columns = [
        "name",
        "parent_label_name",
        "lowest_taxonomic_name",
        "lowest_aphia_id",
        "name_is_lowest",
        "identification_qualifier",
        "id",
    ]

    labels = []
    seen_names = set()

    for excel_row, (_, row) in enumerate(
        data.iterrows(),
        start=LABEL_DATA_START_ROW + 1,
    ):
        name = _optional_string(row["name"])

        row_has_data = any(_optional_string(value) is not None for value in row)
        if not row_has_data:
            continue

        if name is None:
            raise ValueError(f"Validation error at row {excel_row}: label-name is required.")

        if name in seen_names:
            raise ValueError(f"Validation error at row {excel_row}: " f"duplicate label-name '{name}'.")
        seen_names.add(name)

        labels.append(
            {
                "id": _parse_optional_uuid(row["id"], excel_row, "label-name-uuid"),
                "name": name,
                "parent_label_name": _optional_string(row["parent_label_name"]),
                "lowest_taxonomic_name": _optional_string(row["lowest_taxonomic_name"]),
                "lowest_aphia_id": _parse_optional_integer(
                    row["lowest_aphia_id"],
                    excel_row,
                    "label-lowest-AphiaID",
                ),
                "name_is_lowest": _parse_optional_boolean(
                    row["name_is_lowest"],
                    excel_row,
                    "label-name-is-lowest-taxon",
                ),
                "identification_qualifier": _optional_string(row["identification_qualifier"]),
            }
        )

    if not labels:
        raise ValueError("No labels were found in the label-attributes worksheet.")

    return labels
