"""Parser functions related to annotation data."""

import json

import pandas as pd

from api.utils.constants import (
    ANNOTATION_DATA_END_COL,
    ANNOTATION_DATA_START_COL,
    ANNOTATION_DATA_START_ROW,
    ANNOTATION_METADATA_KEYS,
    ANNOTATION_SET_COL_SIZE,
    LABEL_SET_COL_SIZE,
)


def parse_annotation_set_metadata(annotation_df: pd.DataFrame) -> dict:
    """Parse annotation set metadata.

    Args:
        annotation_df(pd.DataFrame): annotation_set metadata

    Returns:
        dict: parsed data.
    """
    df = annotation_df.iloc[:, :ANNOTATION_SET_COL_SIZE]
    df.iloc[:, 2] = df.iloc[:, 2].fillna("")

    annotation_data = {}
    current_main_key = None

    for main_key, sub_key, value in df.itertuples(index=False, name=None):
        # Update main key if valid
        if pd.notna(main_key) and str(main_key).strip():
            current_main_key = str(main_key).strip()

        # Skip if no main key yet
        if not current_main_key:
            continue

        sub_key_clean = str(sub_key).strip() if pd.notna(sub_key) else ""

        final_key = f"{current_main_key}-{sub_key_clean}" if sub_key_clean else current_main_key

        # Store only if value exists
        if pd.notna(value) and str(value).strip() != "" and final_key in ANNOTATION_METADATA_KEYS:
            annotation_data[final_key] = str(value).strip()

    required_keys = {
        "annotation-image-set-name": "Image Set Name",
        "annotation-image-set-uuid": "Image Set UUID",
        "annotation-set-name": "Annotation Set Name",
        "annotation-license-name": "License Name",
    }

    missing = [label for key, label in required_keys.items() if not annotation_data.get(key)]
    if missing:
        # Raising a ValidationError for missing required keys.
        raise ValueError(f"Missing required metadata: {', '.join(missing)}")

    return annotation_data


def _empty_to_none(value):
    """Helper to convert blank strings to None."""
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None


def parse_label_set(label_df: pd.DataFrame) -> list[dict]:
    """Parse Label set data from Dataframe.

    Args:
        label_df(pd.DataFrame): label data.

    Returns:
        list[dict]: list of label dictionaries.
    """
    start_idx = None
    for i, val in enumerate(label_df.iloc[:, 0]):
        if str(val).strip().lower() == "value":
            start_idx = i  # data starts AFTER this row
            break

    if start_idx is None:
        raise ValueError("Could not find values in Label Set.")

    label_df = label_df.iloc[start_idx:, :LABEL_SET_COL_SIZE]

    label_df.columns = [
        "field",
        "label_name",
        "parent_label_name",
        "lowest_taxonomic_name",
        "lowest_aphia_id",
        "label_name_is_lowest",
        "identification_qualifier",
    ]

    # Clean data
    label_df = label_df.fillna("")

    label_data = []

    for row in label_df.to_dict(orient="records"):
        if not str(row["label_name"]).strip():
            continue

        label_data.append(
            {
                "name": row["label_name"].strip(),
                "parent_label_name": row["parent_label_name"].strip(),
                "lowest_taxonomic_name": _empty_to_none(row["lowest_taxonomic_name"]),
                "lowest_aphia_id": _empty_to_none(row["lowest_aphia_id"]),
                "name_is_lowest": str(row["label_name_is_lowest"]).strip().lower() == "yes",
                "identification_qualifier": _empty_to_none(row["identification_qualifier"]),
            }
        )

    return label_data


def _parse_coordinates(coord_val: str) -> list:
    """Convert coordinate string into list format."""
    if not coord_val or pd.isna(coord_val):
        return []

    coord_val = str(coord_val).strip()

    try:
        if coord_val.startswith("["):
            return json.loads(coord_val)

        parts = [float(x.strip()) for x in coord_val.split(",")]
        return [parts]

    except Exception:
        return []


def parse_annotation_data(annotation_df: pd.DataFrame) -> list[dict]:
    """Parse Annotation data from dataframe.

    Args:
        annotation_df(pd.DataFrame): annotation data.

    Returns:
        list[dict]: list of annotation dictionaries.
    """
    annotation_df = annotation_df.iloc[ANNOTATION_DATA_START_ROW:, ANNOTATION_DATA_START_COL:ANNOTATION_DATA_END_COL]

    annotation_df.columns = [
        "image_uuid",
        "annotation_platform",
        "image_filename",
        "annotation_human_creator",
        "annotation_creation_datetime",
        "annotation_label_name",
        "annotation_shape_name",
        "annotation_coordinates",
        "annotation_dimension_pixels",
    ]

    annotation_df = annotation_df.fillna("")

    annotation_data = []

    for index, row in enumerate(annotation_df.to_dict(orient="records")):
        uuid_val = str(row["image_uuid"]).strip()
        filename_val = str(row["image_filename"]).strip()
        # Skip empty rows
        if not str(row["image_filename"]).strip():
            continue
        if not uuid_val and not filename_val:
            excel_row = index + 1 + ANNOTATION_DATA_START_ROW
            raise ValueError(
                f"Validation Error at Row {excel_row}: " f"Record must provide either 'image-uuid' or 'image-filename'."
            )

        parsed_row = {
            "image_id": uuid_val,
            "image_filename": filename_val,
            "annotation_platform": row["annotation_platform"].strip(),
            "shape": row["annotation_shape_name"].strip(),
            "coordinates": _parse_coordinates(row["annotation_coordinates"]),
            "dimension_pixels": (
                float(row["annotation_dimension_pixels"]) if str(row["annotation_dimension_pixels"]).strip() else None
            ),
            "label_name": row["annotation_label_name"].strip(),
            "annotator_name": row["annotation_human_creator"].strip(),
            "creation_datetime": row["annotation_creation_datetime"],
        }

        annotation_data.append(parsed_row)

    return annotation_data
