"""Serializers for the Annotations API endpoints."""

from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

AnnotationSetGroup = inline_serializer(
    name="AnnotationSetGroup",
    many=True,
    fields={
        "uuid": serializers.UUIDField(),
        "creation_datetime": serializers.DateTimeField(),
        "annotation_set_name": serializers.CharField(),
        "image_set_name": serializers.CharField(allow_null=True),
        "image_set_uuid": serializers.UUIDField(),
        "image_filename": serializers.CharField(),
        "image_uuid": serializers.UUIDField(),
        "label_name": serializers.CharField(),
        "label_aphia_id": serializers.IntegerField(allow_null=True),
        "annotation_platform": serializers.CharField(allow_null=True),
        "annotation_shape": serializers.CharField(),
        "annotation_coordinates": serializers.ListField(),
        "annotation_dimension_pixels": serializers.FloatField(allow_null=True),
        "annotator_name": serializers.CharField(allow_null=True),
    },
)


SearchResultItem = inline_serializer(
    many=True,
    name="SearchResultItem",
    fields={
        "uuid": serializers.UUIDField(),
        "image_filename": serializers.CharField(),
        "image_uuid": serializers.UUIDField(),
        "label_name": serializers.CharField(),
        "label_aphia_id": serializers.IntegerField(),
        "annotation_platform": serializers.CharField(allow_null=True),
        "annotation_shape": serializers.CharField(),
        "annotation_coordinates": serializers.ListField(),
        "annotation_dimension_pixels": serializers.FloatField(allow_null=True),
        "annotator_name": serializers.CharField(allow_null=True),
        "annotation_set_uuid": serializers.UUIDField(),
        "image_set_uuid": serializers.UUIDField(),
    },
)


PaginatedSearchResult = inline_serializer(
    name="PaginatedSearchResult",
    fields={
        "count": serializers.IntegerField(),
        "next": serializers.URLField(allow_null=True),
        "previous": serializers.URLField(allow_null=True),
        "results": inline_serializer(
            name="SearchResultPayload",
            fields={
                "info": serializers.DictField(required=False),
                "summary": serializers.DictField(required=False),
                "annotations": SearchResultItem,
            },
        ),
    },
)

GroupedSearchResultRow = inline_serializer(
    name="GroupedSearchResultRow",
    fields={
        "summary": inline_serializer(
            name="GroupedSearchResultSummary",
            fields={
                "n_annotations": serializers.IntegerField(),
                "n_images": serializers.IntegerField(),
                "n_annotation_sets": serializers.IntegerField(),
                "n_image_sets": serializers.IntegerField(),
            },
        ),
        "annotations": inline_serializer(
            name="GroupedSearchResultAnnotations",
            fields={
                "<annotation_set_uuid1>": AnnotationSetGroup,
                "<annotation_set_uuid2>": AnnotationSetGroup,
            },
        ),
    },
)
