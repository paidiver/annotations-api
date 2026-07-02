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

CreatorExportItem = inline_serializer(
    name="CreatorExportItem",
    many=True,
    fields={
        "name": serializers.CharField(allow_null=True),
        "uri": serializers.CharField(allow_blank=True, allow_null=True),
    },
)


AnnotationExportAnnotation = inline_serializer(
    name="AnnotationExportAnnotation",
    many=True,
    fields={
        "image_handle": serializers.CharField(allow_null=True),
        "image_uuid": serializers.UUIDField(),
        "annotation_platform": serializers.CharField(allow_null=True),
        "image_filename": serializers.CharField(),
        "annotation_human_creator": serializers.CharField(allow_null=True),
        "annotation_creation_datetime": serializers.DateTimeField(),
        "annotation_label_name": serializers.CharField(),
        "annotation_shape_name": serializers.CharField(),
        "annotation_coordinates": serializers.ListField(),
        "annotation_set_name": serializers.CharField(),
    },
)


AnnotationExportImage = inline_serializer(
    name="AnnotationExportImage",
    many=True,
    fields={
        "image_filename": serializers.CharField(),
        "image_datetime": serializers.DateTimeField(allow_null=True),
        "image_longitude": serializers.FloatField(allow_null=True),
        "image_latitude": serializers.FloatField(allow_null=True),
        "image_depth": serializers.FloatField(allow_null=True),
        "image_uuid": serializers.UUIDField(),
        "image_hash_sha256": serializers.CharField(allow_null=True),
        "image_area_square_meter": serializers.FloatField(allow_null=True),
        "image_meters_above_ground": serializers.FloatField(allow_null=True),
        "image_acquisition_settings": serializers.JSONField(allow_null=True),
        "image_set_name": serializers.CharField(),
    },
)


AnnotationExportAnnotationSet = inline_serializer(
    name="AnnotationExportAnnotationSet",
    many=True,
    fields={
        "annotation_set_name": serializers.CharField(),
        "annotation_project_name": serializers.CharField(allow_null=True),
        "annotation_project_uri": serializers.CharField(allow_blank=True, allow_null=True),
        "annotation_context_name": serializers.CharField(allow_null=True),
        "annotation_context_uri": serializers.CharField(allow_blank=True, allow_null=True),
        "annotation_abstract": serializers.CharField(allow_blank=True, allow_null=True),
        "annotation_objective": serializers.CharField(allow_blank=True, allow_null=True),
        "annotation_target_environment": serializers.CharField(allow_blank=True, allow_null=True),
        "annotation_target_timescale": serializers.CharField(allow_blank=True, allow_null=True),
        "annotation_curation_protocol": serializers.CharField(allow_blank=True, allow_null=True),
        "annotation_pi_name": serializers.CharField(allow_null=True),
        "annotation_pi_uri": serializers.CharField(allow_blank=True, allow_null=True),
        "annotation_license_name": serializers.CharField(allow_null=True),
        "annotation_license_uri": serializers.CharField(allow_blank=True, allow_null=True),
        "annotation_copyright": serializers.CharField(allow_blank=True, allow_null=True),
        "annotation_set_uuid": serializers.UUIDField(),
        "annotation_set_handle": serializers.CharField(allow_blank=True, allow_null=True),
        "annotation_set_version": serializers.CharField(allow_blank=True, allow_null=True),
        "annotation_image_set_name": serializers.CharField(),
        "annotation_image_set_uuid": serializers.UUIDField(),
        "annotation_image_set_handle": serializers.CharField(allow_blank=True, allow_null=True),
        "annotation_creators": CreatorExportItem,
    },
)


AnnotationExportImageSet = inline_serializer(
    name="AnnotationExportImageSet",
    many=True,
    fields={
        "image_set_name": serializers.CharField(),
        "image_project_name": serializers.CharField(allow_null=True),
        "image_project_uri": serializers.CharField(allow_blank=True, allow_null=True),
        "image_context_name": serializers.CharField(allow_null=True),
        "image_context_uri": serializers.CharField(allow_blank=True, allow_null=True),
        "image_abstract": serializers.CharField(allow_blank=True, allow_null=True),
        "image_event_name": serializers.CharField(allow_null=True),
        "image_event_uri": serializers.CharField(allow_blank=True, allow_null=True),
        "image_platform_name": serializers.CharField(allow_null=True),
        "image_platform_uri": serializers.CharField(allow_blank=True, allow_null=True),
        "image_sensor_name": serializers.CharField(allow_null=True),
        "image_sensor_uri": serializers.CharField(allow_blank=True, allow_null=True),
        "image_set_uuid": serializers.UUIDField(),
        "image_set_handle": serializers.CharField(allow_blank=True, allow_null=True),
        "image_pi_name": serializers.CharField(allow_null=True),
        "image_pi_uri": serializers.CharField(allow_blank=True, allow_null=True),
        "image_license_name": serializers.CharField(allow_null=True),
        "image_license_uri": serializers.CharField(allow_blank=True, allow_null=True),
        "image_copyright": serializers.CharField(allow_blank=True, allow_null=True),
        "image_acquisition": serializers.CharField(allow_blank=True, allow_null=True),
        "image_quality": serializers.CharField(allow_blank=True, allow_null=True),
        "image_deployment": serializers.CharField(allow_blank=True, allow_null=True),
        "image_navigation": serializers.CharField(allow_blank=True, allow_null=True),
        "image_scale_reference": serializers.CharField(allow_blank=True, allow_null=True),
        "image_illumination": serializers.CharField(allow_blank=True, allow_null=True),
        "image_resolution": serializers.CharField(allow_blank=True, allow_null=True),
        "image_marine_zone": serializers.CharField(allow_blank=True, allow_null=True),
        "image_spectral_resolution": serializers.CharField(allow_blank=True, allow_null=True),
        "image_capture_mode": serializers.CharField(allow_blank=True, allow_null=True),
        "image_spatial_constraints": serializers.CharField(allow_blank=True, allow_null=True),
        "image_temporal_constraints": serializers.CharField(allow_blank=True, allow_null=True),
        "image_target_environment": serializers.CharField(allow_blank=True, allow_null=True),
        "image_objective": serializers.CharField(allow_blank=True, allow_null=True),
        "image_time_synchronisation": serializers.CharField(allow_blank=True, allow_null=True),
        "image_item_identification_scheme": serializers.CharField(allow_blank=True, allow_null=True),
        "image_curation_protocol": serializers.CharField(allow_blank=True, allow_null=True),
        "image_acquisition_settings": serializers.JSONField(allow_null=True),
        "image_set_start_datetime": serializers.DateTimeField(allow_null=True),
        "image_set_lat_min": serializers.FloatField(allow_null=True),
        "image_set_lat_max": serializers.FloatField(allow_null=True),
        "image_set_long_min": serializers.FloatField(allow_null=True),
        "image_set_long_max": serializers.FloatField(allow_null=True),
        "image_creators": CreatorExportItem,
    },
)


AnnotationExportData = inline_serializer(
    name="AnnotationExportData",
    fields={
        "annotations": AnnotationExportAnnotation,
        "images": AnnotationExportImage,
        "annotation_sets": AnnotationExportAnnotationSet,
        "image_sets": AnnotationExportImageSet,
    },
)
