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
                "34705832-8ad5-403f-8bbc-5b6f463309cc": AnnotationSetGroup,
                "3535f7a4-e285-4017-a96b-18de8e592d8f": AnnotationSetGroup,
            },
        ),
    },
)
