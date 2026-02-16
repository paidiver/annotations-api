"""Serializers for the Labels API endpoints."""

import requests
from django.conf import settings
from requests import RequestException
from rest_framework import serializers

from api.models import Label
from api.models.annotation_set import AnnotationSet
from api.serializers.base import ReadOnlyFieldsMixin

OK_STATUS_CODE = 200
NO_CONTENT_STATUS_CODE = 204
ERROR_STATUS_CODE = 400
API_ERROR_STATUS_CODES = range(500, 600)


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

        try:
            response = _test_cached_and_live_worms_api(aphia_id)
        except RequestException:
            errors["lowest_aphia_id"] = "WoRMS API is currently unavailable. Please try again later."
            return errors

        if response.status_code == OK_STATUS_CODE:
            # TODO - consider caching this result in our DB for future requests to avoid hitting the live WoRMS API
            # repeatedly for the same AphiaIDs
            return errors

        if response.status_code in [NO_CONTENT_STATUS_CODE, ERROR_STATUS_CODE]:
            errors["lowest_aphia_id"] = f"Invalid lowest_aphia_id: {aphia_id} does not exist in WoRMS API."
            return errors

        if response.status_code in API_ERROR_STATUS_CODES:
            errors["lowest_aphia_id"] = (
                f"Unable to validate lowest_aphia_id right now (status {response.status_code}). Please try again later."
            )
            return errors

        errors["lowest_aphia_id"] = (
            f"Unable to validate lowest_aphia_id right now (status {response.status_code}). Please try again later."
        )
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
    """Helper function to test both the cached and live WoRMS API for a given aphia_id.

    Args:
        aphia_id (str): The aphia_id to test.

    Returns:
        requests.Response: The response from the WoRMS API.
    """
    cached_response = requests.get(
        f"{settings.CACHED_WORMS_API_BASE_URL}/AphiaRecordByAphiaID/{aphia_id}",
        timeout=20,
    )
    if cached_response.status_code == OK_STATUS_CODE:
        return cached_response

    return requests.get(
        f"{settings.WORMS_API_BASE_URL}/AphiaRecordByAphiaID/{aphia_id}",
        timeout=20,
    )
