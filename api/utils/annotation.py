"""Service functions related to annotation data."""

from itertools import zip_longest

import pandas as pd
from django.db import transaction

from api.models.fields import Creator
from api.models.image_set import ImageSet
from api.serializers import AnnotationSetSerializer
from api.utils.constants import ANNOTATION_KEYS


def insert_annotations_into_tables(data: pd.DataFrame):
    """Insert annotations related into respective tables.

    Args:
        data(pd.DataFrame): annotation dataframe.

    Returns:
        newly created annotation_set object
    """
    with transaction.atomic():
        # Prepare data for AnnotationSet
        annotation_set_data = {
            "name": data.get("annotation-set-name", ""),
            "abstract": data.get("annotation-abstract", ""),
            "objective": data.get("annotation-objective", ""),
            "target_environment": data.get("annotation-target-environment", ""),
            "target_timescale": data.get("annotation-target-timescale", ""),
            "curation_protocol": data.get("annotation-curation-protocol", ""),
            "handle": data.get("annotation-set-handle", ""),
            "copyright": data.get("annotation-set-copyright", ""),
            "version": str(data.get("annotation-set-version", "1")),
            "context": {"name": data.get("annotation-context-name", ""), "uri": data.get("annotation-context-uri", "")},
            "project": {"name": data.get("annotation-project-name", ""), "uri": data.get("annotation-project-uri", "")},
            "pi": {"name": data.get("annotation-pi-name", ""), "uri": data.get("annotation-pi-uri", "")},
            "license": {"name": data.get("annotation-license-name", ""), "uri": data.get("annotation-license-uri", "")},
        }

        serializer = AnnotationSetSerializer(data=annotation_set_data)
        if serializer.is_valid(raise_exception=True):
            annotation_set = serializer.save()

            # Handle Many-to-Many Creators
            if data.get("annotation-creators-names"):
                names_list = [n.strip() for n in data.get("annotation-creators-names", "").split(",") if n.strip()]
                uris_list = [u.strip() for u in data.get("annotation-creators-uris", "").split(",") if u.strip()]

                for name, uri in zip_longest(names_list, uris_list, fillvalue=None):
                    creator, _ = Creator.objects.get_or_create(name=name, uri=uri)
                    annotation_set.creators.add(creator)

            # Handle Many-to-Many image-sets
            if data.get("annotation-image-set-name"):
                image_set, _ = ImageSet.objects.get_or_create(
                    name=data.get("annotation-image-set-name"),
                    id=data.get("annotation-image-set-uuid"),
                    handle=data.get("annotation-image-set-handle"),
                )
                annotation_set.image_sets.add(image_set)

        return annotation_set


def parse_annodation_set_metadata(annotation_df: pd.DataFrame) -> dict:
    """Parse annotation metadata from dataframe and insert into db."""
    df = annotation_df.iloc[:, :3]
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
        if pd.notna(value) and final_key in ANNOTATION_KEYS:
            annotation_data[final_key] = value

    insert_annotations_into_tables(data=annotation_data)


def parse_label_set(label_df: pd.DataFrame) -> list[dict]:
    """Parse Label set data from Dataframe."""
    start_idx = None
    for i, val in enumerate(label_df.iloc[:, 0]):
        if str(val).strip().lower() == "value":
            start_idx = i   # data starts AFTER this row
            print(f'original start index: {start_idx}')
            break

    # if start_idx is None:
    #     return Response(
    #         {"error": "Invalid Label Set format (missing 'Value' row)."},
    #         status=HTTP_400_BAD_REQUEST,
    #     )

    label_df = label_df.iloc[start_idx:, :7]

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

        label_data.append({
            "label_name": row["label_name"].strip(),
            "parent_label_name": row["parent_label_name"].strip(),
            "lowest_taxonomic_name": row["lowest_taxonomic_name"].strip(),
            "lowest_aphia_id": row["lowest_aphia_id"],
            "is_lowest": str(row["label_name_is_lowest"]).strip().lower(),
            "identification_qualifier": row["identification_qualifier"].strip(),
        })

    return label_data
