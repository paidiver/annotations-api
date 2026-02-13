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

    # --- 1) Validate ImageSet (no save yet)
    image_set_ser = ImageSetSerializer(data=image_set_payload)
    if not image_set_ser.is_valid():
        return Response({"image_set": image_set_ser.errors}, status=status.HTTP_400_BAD_REQUEST)

    # --- 2) Validate all items (no save yet)
    item_errors: dict[str, Any] = {}
    validated_item_payloads: list[dict[str, Any]] = []

    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            item_errors[str(idx)] = {"detail": "Item must be an object"}
            continue

        try:
            img_payload = adapt_ifdo_item_to_image_serializer_payload(item, image_set_id=None)
        except IFDOAdaptError as exc:
            item_errors[str(idx)] = {"detail": str(exc)}
            continue

        img_ser = ImageSerializer(data=img_payload)
        if not img_ser.is_valid():
            item_errors[str(idx)] = img_ser.errors
            continue

        # keep validated serializer data (or just keep payload and revalidate later)
        validated_item_payloads.append(img_payload)

    if item_errors:
        return Response(
            {
                "detail": "One or more image items failed validation",
                "image_set": {"name": image_set_payload.get("name")},
                "items": item_errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # --- 3) Save everything atomically now we know it all validates
    with transaction.atomic():
        image_set = image_set_ser.save()

        created_image_ids: list[int] = []
        for img_payload in validated_item_payloads:
            # inject the created FK now
            img_payload["image_set_id"] = image_set.id
            img_ser = ImageSerializer(data=img_payload)
            img_ser.is_valid(raise_exception=True)
            img = img_ser.save()
            created_image_ids.append(img.id)

    return Response(
        {
            "message": "Ingested iFDO payload successfully",
            "image_set_id": image_set.id,
            "image_count": len(created_image_ids),
        },
        status=status.HTTP_201_CREATED,
    )