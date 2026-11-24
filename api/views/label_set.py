"""ViewSet for the LabelSet model."""

from django.db.models import CharField, QuerySet
from django.db.models.functions import Cast
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from api.models import LabelSet
from api.serializers import LabelSetSerializer
from api.views.set_filters import filter_by_any_text_field, filter_set_queryset

LABEL_SET_FILTERS = {
    "name": "name",
    "project": "project__name",
    "context": "context__name",
    "abstract": "abstract",
    "objective": "objective",
    "handle": "handle",
}

LABEL_FILTERS = {
    "label-name": "labels__name",
    "label-parent-name": "labels__parent_label_name",
    "label-lowest-taxonomic-name": "labels__lowest_taxonomic_name",
}

LABEL_SET_METADATA_SEARCH_FIELDS = [
    "name",
    "project__name",
    "context__name",
    "abstract",
    "objective",
]

LABEL_METADATA_SEARCH_FIELDS = [
    "labels__name",
    "labels__parent_label_name",
    "labels__lowest_taxonomic_name",
]

LABEL_SET_FILTER_PARAMETERS = [
    OpenApiParameter(name=name, type=str, description=f"Filter label sets by {name} (case-insensitive partial match).")
    for name in LABEL_SET_FILTERS
] + [
    OpenApiParameter(name="uuid", type=str, description="Filter by part of the label-set UUID."),
    OpenApiParameter(
        name="metadata_search",
        type=str,
        description="Search name, project, context, abstract, or objective (partial match).",
    ),
    OpenApiParameter(
        name="label_search",
        type=str,
        description="Search labels by name, parent name, lowest taxonomic name, or AphiaID (partial match).",
    ),
    *[
        OpenApiParameter(
            name=name,
            type=str,
            description=f"Filter label sets by matching labels' {name.removeprefix('label-')}.",
        )
        for name in LABEL_FILTERS
    ],
    OpenApiParameter(
        name="label-lowest-AphiaID",
        type=str,
        description="Filter label sets by part of the labels' AphiaID.",
    ),
]


@extend_schema(tags=["Labels API"])
class LabelSetViewSet(viewsets.ModelViewSet):
    """ViewSet for the LabelSet model."""

    queryset = (
        LabelSet.objects.select_related("context", "project", "pi", "license")
        .prefetch_related("creators", "related_materials")
        .order_by("id")
    )
    serializer_class = LabelSetSerializer

    @extend_schema(parameters=LABEL_SET_FILTER_PARAMETERS)
    def list(self, request: Request, *args, **kwargs) -> Response:
        """List label sets, optionally filtered by their searchable metadata."""
        return super().list(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[LabelSet]:
        """Return label sets matching all supplied query parameters."""
        queryset = super().get_queryset()
        if self.action != "list":
            return queryset
        queryset = filter_set_queryset(
            queryset,
            self.request,
            LABEL_SET_FILTERS,
            LABEL_SET_METADATA_SEARCH_FIELDS,
        )

        label_filters: dict[str, str] = {}
        for parameter, model_field in LABEL_FILTERS.items():
            value = self.request.query_params.get(parameter, "").strip()
            if value:
                label_filters[f"{model_field}__icontains"] = value

        aphia_id = self.request.query_params.get("label-lowest-AphiaID", "").strip()
        label_search = self.request.query_params.get("label_search", "").strip()
        if aphia_id or label_search:
            queryset = queryset.alias(lowest_aphia_id_as_text=Cast("labels__lowest_aphia_id", output_field=CharField()))

        if aphia_id:
            label_filters["lowest_aphia_id_as_text__icontains"] = aphia_id

        if label_search:
            queryset = filter_by_any_text_field(
                queryset,
                label_search,
                [*LABEL_METADATA_SEARCH_FIELDS, "lowest_aphia_id_as_text"],
            )

        if label_filters:
            queryset = queryset.filter(**label_filters).distinct()
        elif label_search:
            queryset = queryset.distinct()

        return queryset
