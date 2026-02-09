"""Serializers for the Labels API endpoints."""

from rest_framework import serializers

from api.models import Label
from api.models.annotation_set import AnnotationSet


class LabelSerializer(serializers.ModelSerializer):
    """Serializer for Label model."""

    annotation_set_id = serializers.PrimaryKeyRelatedField(
        source="annotation_set",
        queryset=AnnotationSet.objects.all(),
    )

    class Meta:
        """Meta class for LabelSerializer."""

        model = Label
        fields = [
            "id",
            "name",
            "parent_label_name",
            "lowest_taxonomic_name",
            "lowest_aphia_id",
            "name_is_lowest",
            "identification_qualifier",
            "annotation_set_id",
        ]

        read_only_fields = ["id", "created_at", "updated_at"]
