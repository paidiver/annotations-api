# api/views/ingest_ifdo.py
from __future__ import annotations

from typing import Any

from django.db import transaction
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.ingest.data_subs_mapping import (
    IFDOAdaptError,
    adapt_ifdo_image_set_to_serializer_payload,
    adapt_ifdo_item_to_image_serializer_payload,
)
from api.serializers import ImageSerializer, ImageSetSerializer

IngestIFDOSerializer = inline_serializer(
    name="IngestIFDORequest",
    fields={
        "submission_id": serializers.CharField(required=False),
        "image_set_uuid": serializers.CharField(required=False),
        "ifdo": serializers.DictField(),  # contains image-set-header + image-set-items
    },
)

IngestIFDOResponseSerializer = inline_serializer(
    name="IngestIFDOResponse",
    fields={
        "message": serializers.CharField(),
        "image_set_id": serializers.IntegerField(),
        "image_count": serializers.IntegerField(),
    },
)


@extend_schema(
    tags=["Ingest"],
    request=IngestIFDOSerializer,
    responses={201: IngestIFDOResponseSerializer, 400: serializers.DictField(), 502: serializers.DictField()},
)
@api_view(["POST"])
def ingest_ifdo_image_set(request) -> Response:
    body: dict[str, Any] = request.data if isinstance(request.data, dict) else {}

    ifdo = body.get("ifdo")
    if not isinstance(ifdo, dict):
        return Response({"detail": "Missing or invalid 'ifdo' object"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        image_set_payload = adapt_ifdo_image_set_to_serializer_payload(ifdo)
    except IFDOAdaptError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    items = ifdo.get("image-set-items") or []
    if not isinstance(items, list):
        return Response({"detail": "ifdo.image-set-items must be a list"}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        # 1) create ImageSet first (now we have an id)
        image_set_ser = ImageSetSerializer(data=image_set_payload)
        if not image_set_ser.is_valid():
            return Response({"image_set": image_set_ser.errors}, status=status.HTTP_400_BAD_REQUEST)

        image_set = image_set_ser.save()

        # 2) create Images
        created_image_ids: list[int] = []
        item_errors: dict[str, Any] = {}

        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                item_errors[str(idx)] = {"detail": "Item must be an object"}
                continue

            try:
                # don't pass image_set_id at all; we force FK at save time
                img_payload = adapt_ifdo_item_to_image_serializer_payload(item, image_set_id=image_set.id)
            except IFDOAdaptError as exc:
                item_errors[str(idx)] = {"detail": str(exc)}
                continue

            # If your serializer expects image_set_id, keep it in payload.
            # If not, it’s still safe because we inject image_set on save().
            img_ser = ImageSerializer(data=img_payload)
            if not img_ser.is_valid():
                item_errors[str(idx)] = img_ser.errors
                continue

            img = img_ser.save(image_set=image_set)  # ✅ guarantees FK
            created_image_ids.append(img.id)

        if item_errors:
            transaction.set_rollback(True)
            return Response(
                {
                    "detail": "One or more image items failed validation",
                    "image_set": {"name": image_set_payload.get("name")},
                    "items": item_errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    return Response(
        {
            "message": "Ingested iFDO payload successfully",
            "image_set_id": image_set.id,
            "image_count": len(created_image_ids),
        },
        status=status.HTTP_201_CREATED,
    )
