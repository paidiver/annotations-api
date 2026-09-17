"""Response serializers for annotation search and exports."""

from drf_spectacular.utils import extend_schema_serializer, inline_serializer
from rest_framework import serializers


class SearchResultItem(serializers.Serializer):
    """A matching annotation-label row."""

    uuid = serializers.UUIDField()
    creation_datetime = serializers.DateTimeField()
    annotation_creation_datetime = serializers.DateTimeField()
    annotation_set_uuid = serializers.UUIDField()
    annotation_set_name = serializers.CharField()
    image_set_uuid = serializers.UUIDField()
    image_set_name = serializers.CharField()
    image_filename = serializers.CharField()
    image_handle = serializers.CharField(allow_null=True)
    image_uuid = serializers.UUIDField()
    image_latitude = serializers.FloatField(allow_null=True)
    image_longitude = serializers.FloatField(allow_null=True)
    label_name = serializers.CharField()
    label_aphia_id = serializers.IntegerField(allow_null=True)
    annotation_platform = serializers.CharField(allow_null=True)
    annotation_shape = serializers.CharField()
    annotation_coordinates = serializers.ListField()
    annotation_dimension_pixels = serializers.FloatField(allow_null=True)
    annotator_name = serializers.CharField(allow_null=True)


class SearchMetadata(serializers.Serializer):
    """Optional full-search aggregates and filter information."""

    summary = serializers.DictField(required=False)
    info = serializers.DictField(required=False)


@extend_schema_serializer(many=False)
class PaginatedSearchResult(serializers.Serializer):
    """Stable collection envelope for paginated and complete searches."""

    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = SearchResultItem(many=True)
    meta = SearchMetadata()


class AnnotationSetGroup(serializers.Serializer):
    """All matching rows belonging to an annotation set."""

    annotation_set_uuid = serializers.UUIDField()
    annotations = SearchResultItem(many=True)


@extend_schema_serializer(many=False)
class GroupedSearchResultRow(PaginatedSearchResult):
    """Pages of complete groups; count is the number of annotation sets."""

    results = AnnotationSetGroup(many=True)


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
