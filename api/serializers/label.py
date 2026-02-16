"""Serializers for the Labels API endpoints."""

import requests
from django.conf import settings
from rest_framework import serializers

from api.models import Label
from api.models.annotation_set import AnnotationSet
from api.serializers.base import ReadOnlyFieldsMixin


class LabelSerializer(ReadOnlyFieldsMixin, serializers.ModelSerializer):
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

    def _validate_aphia_id(self, attrs: dict, errors: dict) -> dict:
        """Custom validation to ensure lowest_aphid_id matches to an existing aphia_id in WoRMS API.

        Args:
            attrs (dict): The attributes to validate.
            errors (dict): The dictionary to which any validation errors will be added.

        Returns:
            dict: The updated errors dictionary with any new errors added.
        """
        aphia_id = attrs.get("lowest_aphia_id")
        if aphia_id is None:
            return errors
        response = _test_cached_and_live_worms_api(aphia_id)
        if response.status_code != 200:  # noqa: PLR2004
            errors["lowest_aphia_id"] = f"Invalid lowest_aphia_id: {aphia_id} does not exist in WoRMS API."
        return errors

    def validate(self, attrs: dict) -> dict:
        """Custom validation to ensure no duplicate AnnotationLabel for the same annotation, label, and annotator.

        Args:
            attrs (dict): The attributes to validate.

        Returns:
            dict: The validated attributes.
        """
        errors = {}

        errors = self._validate_aphia_id(attrs, errors)

        if errors:
            raise serializers.ValidationError(errors)
        return attrs


def _test_cached_and_live_worms_api(aphia_id: str) -> requests.Response:
    """Test the provided aphia_id against the cached WoRMS API first, then the live WoRMS API if not found in cache.

    Args:
        aphia_id (str): The AphiaID to test.

    Returns:
        requests.Response: The response from the WoRMS API containing the AphiaRecord for the provided AphiaID,
    or an error if not found.
    """
    cached_response = requests.get(f"{settings.CACHED_WORMS_API_BASE_URL}/AphiaRecordByAphiaID/{aphia_id}", timeout=20)
    if cached_response.status_code == 200:  # noqa: PLR2004
        return cached_response
    response = requests.get(f"{settings.WORMS_API_BASE_URL}/AphiaRecordByAphiaID/{aphia_id}", timeout=20)
    if response.status_code == 200:  # noqa: PLR2004
        # TODO - consider caching this result in our DB for future requests to avoid hitting the live WoRMS API
        # repeatedly for the same AphiaIDs
        pass
    return response
