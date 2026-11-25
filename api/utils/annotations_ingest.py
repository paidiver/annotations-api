"""Ingestion functions for annotation-set submission workbooks."""

from collections import Counter
from uuid import UUID

from django.db import transaction
from rest_framework import serializers

from api.models import (
    Annotation,
    AnnotationSet,
    AnnotationSetModel,
    Creator,
    Image,
    ImageSet,
    Label,
    LabelSet,
)
from api.serializers.annotation import AnnotationSerializer
from api.serializers.annotation_set import (
    AnnotationSetModelSerializer,
    AnnotationSetSerializer,
)
from api.serializers.fields import CreatorSerializer


def _validate_uuid_collisions(
    annotation_set_id: UUID,
    annotations_data: list[dict],
) -> None:
    """Reject annotation-set and annotation UUID collisions."""
    if AnnotationSet.objects.filter(pk=annotation_set_id).exists():
        raise serializers.ValidationError(
            {"annotation-set-uuid": [f"An annotation set with UUID " f"{annotation_set_id} already exists."]}
        )

    supplied_annotation_ids = [annotation["id"] for annotation in annotations_data if annotation.get("id") is not None]

    duplicate_ids = sorted(
        str(annotation_id) for annotation_id, count in Counter(supplied_annotation_ids).items() if count > 1
    )
    if duplicate_ids:
        raise serializers.ValidationError(
            {
                "annotation-uuid": [
                    f"Annotation UUID {annotation_id} is used more than " "once in the workbook."
                    for annotation_id in duplicate_ids
                ]
            }
        )

    existing_ids = sorted(
        str(annotation_id)
        for annotation_id in Annotation.objects.filter(pk__in=supplied_annotation_ids).values_list("pk", flat=True)
    )
    if existing_ids:
        raise serializers.ValidationError(
            {
                "annotation-uuid": [
                    f"An annotation with UUID {annotation_id} " "already exists." for annotation_id in existing_ids
                ]
            }
        )


def _resolve_image_sets(references: dict) -> list[ImageSet]:
    """Resolve and validate image sets referenced by workbook metadata."""
    names = references["image_set_names"]
    identifiers = references["image_set_ids"]
    handles = references["image_set_handles"]

    resolved = []

    for index, name in enumerate(names):
        image_set = None

        if identifiers:
            image_set = ImageSet.objects.filter(pk=identifiers[index]).first()
        else:
            matches = list(ImageSet.objects.filter(name=name)[:2])
            if len(matches) > 1:
                raise serializers.ValidationError(
                    {"annotation-set-image-set-name": [f"More than one image set is named {name!r}."]}
                )
            if matches:
                image_set = matches[0]

        if image_set is None:
            raise serializers.ValidationError(
                {"annotation-set-image-set-name": [f"Image set {name!r} could not be found."]}
            )

        if image_set.name != name:
            raise serializers.ValidationError(
                {
                    "annotation-set-image-set-name": [
                        f"Image-set UUID {image_set.id} belongs to " f"{image_set.name!r}, not {name!r}."
                    ]
                }
            )

        if handles and image_set.handle != handles[index]:
            raise serializers.ValidationError(
                {
                    "annotation-set-image-set-handles": [
                        f"The handle supplied for image set {name!r} " "does not match the stored image set."
                    ]
                }
            )

        resolved.append(image_set)

    return resolved


def _resolve_label_sets(references: dict) -> list[LabelSet]:
    """Resolve and validate label sets referenced by workbook metadata."""
    names = references["label_set_names"]
    identifiers = references["label_set_ids"]
    resolved = []

    for name, label_set_id in zip(names, identifiers, strict=True):
        label_set = LabelSet.objects.filter(pk=label_set_id).first()

        if label_set is None:
            raise serializers.ValidationError(
                {"annotation-set-label-set-UUIDs": [f"Label set {label_set_id} could not be found."]}
            )

        if label_set.name != name:
            raise serializers.ValidationError(
                {
                    "annotation-set-label-set-names": [
                        f"Label-set UUID {label_set_id} belongs to " f"{label_set.name!r}, not {name!r}."
                    ]
                }
            )

        resolved.append(label_set)

    return resolved


def _resolve_creator(data: dict | None) -> Creator | None:
    """Resolve or create a creator from workbook name and URI data."""
    if data is None:
        return None

    serializer = CreatorSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.save()


def _resolve_image(
    annotation_data: dict,
    image_sets: list[ImageSet],
) -> Image:
    """Resolve an annotation image within the linked image sets."""
    image_set_ids = [image_set.id for image_set in image_sets]
    image_id = annotation_data.get("image_id")
    filename = annotation_data.get("image_filename")

    queryset = Image.objects.filter(image_set_id__in=image_set_ids)

    if image_id is not None:
        image = queryset.filter(pk=image_id).first()

        if image is None:
            raise serializers.ValidationError(
                {"image-UUID": [f"Image {image_id} was not found in the " "annotation set's linked image sets."]}
            )

        if filename is not None and image.filename != filename:
            raise serializers.ValidationError(
                {"image-filename": [f"Image UUID {image_id} belongs to " f"{image.filename!r}, not {filename!r}."]}
            )

        return image

    matches = list(queryset.filter(filename=filename)[:2])

    if not matches:
        raise serializers.ValidationError(
            {"image-filename": [f"Image {filename!r} was not found in the " "annotation set's linked image sets."]}
        )

    if len(matches) > 1:
        raise serializers.ValidationError(
            {
                "image-filename": [
                    f"Image filename {filename!r} is ambiguous across " "the linked image sets; supply image-UUID."
                ]
            }
        )

    return matches[0]


def _resolve_label(
    label_name: str,
    label_sets: list[LabelSet],
) -> Label:
    """Resolve a label by name across the linked label sets."""
    label_set_ids = [label_set.id for label_set in label_sets]
    matches = list(
        Label.objects.filter(
            label_set_id__in=label_set_ids,
            name=label_name,
        )[:2]
    )

    if not matches:
        raise serializers.ValidationError(
            {"annotation-label-name": [f"Label {label_name!r} was not found in the linked " "label sets."]}
        )

    if len(matches) > 1:
        raise serializers.ValidationError(
            {"annotation-label-name": [f"Label name {label_name!r} is ambiguous across " "the linked label sets."]}
        )

    return matches[0]


def _resolve_model(
    model_reference: str | None,
    models_by_reference: dict[str, AnnotationSetModel],
    field_name: str,
) -> AnnotationSetModel | None:
    """Resolve a workbook model reference."""
    if model_reference is None:
        return None

    model = models_by_reference.get(model_reference)
    if model is None:
        raise serializers.ValidationError(
            {field_name: [f"Annotation model {model_reference!r} was not " "defined in the workbook."]}
        )

    return model


def _create_models(
    annotation_set: AnnotationSet,
    models_data: list[dict],
) -> tuple[list[AnnotationSetModel], dict[str, AnnotationSetModel]]:
    """Create models registered against an annotation set."""
    created_models = []
    models_by_reference = {}

    for parsed_model in models_data:
        model_data = parsed_model.copy()
        model_data["annotation_set_id"] = annotation_set.id

        serializer = AnnotationSetModelSerializer(data=model_data)
        serializer.is_valid(raise_exception=True)
        model = serializer.save()

        created_models.append(model)
        models_by_reference[model.model_id] = model

    return created_models, models_by_reference


def _create_annotations(
    annotation_set: AnnotationSet,
    annotations_data: list[dict],
    image_sets: list[ImageSet],
    label_sets: list[LabelSet],
    models_by_reference: dict[str, AnnotationSetModel],
) -> list[Annotation]:
    """Create annotation records and resolve their workbook references."""
    created_annotations = []

    for parsed_annotation in annotations_data:
        annotation_data = parsed_annotation.copy()
        annotation_id = annotation_data.pop("id")
        label_name = annotation_data.pop("label_name")
        creator_data = annotation_data.pop("creator")
        reviewer_data = annotation_data.pop("human_reviewer")
        detection_reference = annotation_data.pop("detection_model_ref")
        classification_reference = annotation_data.pop("classification_model_ref")

        image = _resolve_image(annotation_data, image_sets)
        label = _resolve_label(label_name, label_sets)
        creator = _resolve_creator(creator_data)
        reviewer = _resolve_creator(reviewer_data)
        detection_model = _resolve_model(
            detection_reference,
            models_by_reference,
            "annotation-detection-model",
        )
        classification_model = _resolve_model(
            classification_reference,
            models_by_reference,
            "annotation-classification-model",
        )

        annotation_data.pop("image_filename", None)
        annotation_data["image_id"] = image.id
        annotation_data["annotation_set_id"] = annotation_set.id
        annotation_data["label_id"] = label.id
        annotation_data["creator_id"] = creator.id if creator is not None else None
        annotation_data["human_reviewer_id"] = reviewer.id if reviewer is not None else None
        annotation_data["detection_model_id"] = detection_model.id if detection_model is not None else None
        annotation_data["classification_model_id"] = (
            classification_model.id if classification_model is not None else None
        )

        serializer = AnnotationSerializer(data=annotation_data)
        serializer.is_valid(raise_exception=True)
        annotation = serializer.save(id=annotation_id)

        created_annotations.append(annotation)

    return created_annotations


@transaction.atomic
def ingest_annotation_data(
    annotation_set_id: UUID,
    annotation_set_data: dict,
    references: dict,
    models_data: list[dict],
    annotations_data: list[dict],
) -> dict:
    """Create an annotation set, models and annotations atomically."""
    _validate_uuid_collisions(
        annotation_set_id,
        annotations_data,
    )

    image_sets = _resolve_image_sets(references)
    label_sets = _resolve_label_sets(references)

    annotation_set_payload = annotation_set_data.copy()
    annotation_set_payload["image_set_ids"] = [image_set.id for image_set in image_sets]
    annotation_set_payload["label_set_ids"] = [label_set.id for label_set in label_sets]

    annotation_set_serializer = AnnotationSetSerializer(data=annotation_set_payload)
    annotation_set_serializer.is_valid(raise_exception=True)
    annotation_set = annotation_set_serializer.save(id=annotation_set_id)

    created_models, models_by_reference = _create_models(
        annotation_set,
        models_data,
    )
    created_annotations = _create_annotations(
        annotation_set,
        annotations_data,
        image_sets,
        label_sets,
        models_by_reference,
    )

    return {
        "annotation_set": AnnotationSetSerializer(annotation_set).data,
        "models": AnnotationSetModelSerializer(
            created_models,
            many=True,
        ).data,
        "annotations": AnnotationSerializer(
            created_annotations,
            many=True,
        ).data,
    }
