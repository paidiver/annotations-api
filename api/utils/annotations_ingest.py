"""Functions for ingesting annotation data."""

import uuid
from datetime import datetime
from itertools import zip_longest

import pandas as pd
from django.db import transaction

from api.models.annotation import Annotator
from api.models.fields import Creator
from api.models.image import Image
from api.models.image_set import ImageSet
from api.models.label import Label
from api.serializers import AnnotationSetSerializer, LabelSerializer
from api.serializers.annotation import AnnotationLabelSerializer, AnnotationSerializer, AnnotatorSerializer


def insert_annotations_set(data: pd.DataFrame) -> dict:
    """Insert annotations related into respective tables.

    Args:
        data(pd.DataFrame): annotation dataframe.

    Returns:
        newly created annotation_set object
    """
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

    return serializer.data


def insert_label_data(label_list, annotation_set_id: uuid.UUID) -> list[dict]:
    """Inserts a list of label dictionaries into the Label table.

    Args:
        label_list(list[dict]): list of label dictionaries.
        annotation_set_id(uuid.UUID): associated annotation set ID.

    Returns:
        list[dict]: list of inserted label data.
    """
    processed_data = []

    for label_dict in label_list:
        label_name = label_dict.get("name")
        # Ensure this matches the key from parse_label_set
        parent_name = label_dict.get("parent_label_name")

        existing_label = Label.objects.filter(
            name=label_name, parent_label_name=parent_name, annotation_set_id=annotation_set_id
        ).first()

        if not existing_label:
            label_dict["annotation_set_id"] = annotation_set_id
            serializer = LabelSerializer(data=label_dict)

            if serializer.is_valid(raise_exception=True):
                serializer.save()
                processed_data.append(serializer.data)

    return processed_data


def insert_annotations_data(parsed_data_list: list[dict], annotation_set_inst: uuid.UUID) -> dict:
    """Ingests parsed records into Annotation, Annotator, and AnnotationLabel.

    Args:
        parsed_data_list (list[dict]): List of parsed annotation data.
        annotation_set_inst (uuid.UUID): UUID of the annotation set.

    Returns:
        dict: Dictionary containing the inserted annotation data.
    """
    created_count = 0
    errors = []
    data = []

    for index, entry in enumerate(parsed_data_list):
        try:
            image_inst = None
            image_uuid = entry.get("image_id")
            image_filename = entry.get("image_filename")

            if image_uuid and str(image_uuid).strip() != "":
                image_inst = Image.objects.filter(id=image_uuid).first()

            if not image_inst and image_filename:
                image_inst = Image.objects.filter(filename=image_filename).first()

            if not image_inst:
                errors.append(f"Row {index+1}: Image not found (UUID: {image_uuid}, Name: {image_filename})")
                continue

            # Labels must exist in the context of this Annotation Set (from Tab 3)
            label_inst = Label.objects.filter(name=entry["label_name"], annotation_set=annotation_set_inst).first()

            if not label_inst:
                errors.append(f"Row {index+1}: Label '{entry['label_name']}' not found in this Annotation Set.")
                continue

            # find or create the person/machine
            annotator_name = entry.get("annotator_name")
            annotator_inst, _ = Annotator.objects.get_or_create(name=annotator_name)

            # Create Annotation via Serializer
            annotation_data = {
                "image_id": image_inst.id,
                "annotation_set_id": annotation_set_inst,
                "annotation_platform": entry["annotation_platform"],
                "shape": entry["shape"],
                "coordinates": entry["coordinates"],
                "dimension_pixels": entry["dimension_pixels"],
            }

            anno_serializer = AnnotationSerializer(data=annotation_data)
            anno_serializer.is_valid(raise_exception=True)
            annotation_obj = anno_serializer.save()

            # Create AnnotationLabel via Serializer
            dt_val = entry["creation_datetime"]
            if isinstance(dt_val, str) and dt_val.strip():
                try:
                    dt_val = datetime.strptime(dt_val, "%d%m%Y %H:%M:%S")
                except ValueError:
                    dt_val = datetime.now()

            anno_label_data = {
                "annotation_id": annotation_obj.id,
                "label_id": label_inst.id,
                "annotator_id": annotator_inst.id,
                "creation_datetime": dt_val,
            }

            anno_label_serializer = AnnotationLabelSerializer(data=anno_label_data)
            anno_label_serializer.is_valid(raise_exception=True)
            anno_label_serializer.save()

            annotator_serializer = AnnotatorSerializer(annotator_inst)

            data.append(
                {
                    "annotation": anno_serializer.data,
                    "label": anno_label_serializer.data,
                    "annotator": annotator_serializer.data,
                }
            )
            created_count += 1

        except Exception as e:
            errors.append(f"Row {index+1}: {str(e)}")

    data = {"created": created_count, "data": data, "errors": errors}
    return data


def ingest_annotation_data(annotation_set_df: pd.DataFrame, label_list: list, annotation_data: list[dict]) -> dict:
    """Ingest data."""
    with transaction.atomic():
        annotation_set = insert_annotations_set(annotation_set_df)
        label_set = insert_label_data(label_list, annotation_set["id"])

        annotation_data = insert_annotations_data(annotation_data, annotation_set["id"])

        data = {"annotation_set": annotation_set, "label_set": label_set, "annotation_data": annotation_data}
        return data
