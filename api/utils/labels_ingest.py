"""Ingestion functions for label-set submission workbooks."""

from collections import Counter
from uuid import UUID

from django.db import transaction
from rest_framework import serializers

from api.models import Label, LabelSet
from api.serializers.label import LabelSerializer
from api.serializers.label_set import LabelSetSerializer


def _validate_uuid_collisions(
    label_set_id: UUID | None,
    labels_data: list[dict],
) -> None:
    """Reject supplied UUIDs that already belong to existing records."""
    if label_set_id is not None and LabelSet.objects.filter(pk=label_set_id).exists():
        raise serializers.ValidationError({"label-set-uuid": (f"A label set with UUID {label_set_id} already exists.")})

    supplied_label_ids = [label["id"] for label in labels_data if label.get("id") is not None]

    duplicate_label_ids = sorted(str(label_id) for label_id, count in Counter(supplied_label_ids).items() if count > 1)

    if duplicate_label_ids:
        raise serializers.ValidationError(
            {
                "label-name-uuid": [
                    f"Label UUID {label_id} is used more than once in the workbook." for label_id in duplicate_label_ids
                ]
            }
        )

    existing_label_ids = Label.objects.filter(pk__in=supplied_label_ids).values_list("pk", flat=True)

    existing_label_ids = sorted(str(value) for value in existing_label_ids)

    if existing_label_ids:
        raise serializers.ValidationError(
            {"label-name-uuid": [f"A label with UUID {label_id} already exists." for label_id in existing_label_ids]}
        )


@transaction.atomic
def ingest_label_data(
    label_set_id: UUID | None,
    label_set_data: dict,
    labels_data: list[dict],
) -> dict:
    """Create a label set and its labels atomically."""
    _validate_uuid_collisions(label_set_id, labels_data)

    label_set_serializer = LabelSetSerializer(data=label_set_data)
    label_set_serializer.is_valid(raise_exception=True)
    label_set = (
        label_set_serializer.save(id=label_set_id)
        if label_set_id is not None
        else label_set_serializer.save()
    )

    created_labels = []

    # Share the WoRMS validation cache between every label serializer.
    serializer_context = {}

    for parsed_label in labels_data:
        label_data = parsed_label.copy()
        label_id = label_data.pop("id", None)
        label_data["label_set_id"] = label_set.id

        label_serializer = LabelSerializer(
            data=label_data,
            context=serializer_context,
        )
        label_serializer.is_valid(raise_exception=True)

        label = label_serializer.save(id=label_id) if label_id is not None else label_serializer.save()

        created_labels.append(label)

    return {
        "label_set": LabelSetSerializer(label_set).data,
        "labels": LabelSerializer(created_labels, many=True).data,
    }
