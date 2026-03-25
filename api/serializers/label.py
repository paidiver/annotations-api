"""Serializers for the Labels API endpoints."""

import requests
from requests import RequestException
from rest_framework import serializers, status

from api.models import Label
from api.models.annotation_set import AnnotationSet
from api.serializers.base import ReadOnlyFieldsMixin
from api.services.cached_worms_client import CachedWoRMSClient


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
        """Custom validation to ensure lowest_aphid_id (if given) matches to an existing aphia_id in WoRMS API.

        Args:
            attrs (dict): The attributes to validate.
            errors (dict): The dictionary to which any validation errors will be added.

        Returns:
            dict: The updated errors dictionary with any new errors added.
        """
        aphia_id = attrs.get("lowest_aphia_id")
        if aphia_id is None:
            return errors

        aphia_cache = self.context.setdefault("aphia_validation_error_cache", {})

        if aphia_id in aphia_cache:
            cached_error = aphia_cache[aphia_id]
            if cached_error:
                errors["lowest_aphia_id"] = cached_error
            return errors

        try:
            response = _ingest_get_aphia_id_cached_worms(aphia_id)
        except RequestException:
            error_message = "WoRMS API is currently unavailable. Please try again later."
            aphia_cache[aphia_id] = error_message
            errors["lowest_aphia_id"] = error_message
            return errors

        if response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_202_ACCEPTED,
        ]:
            aphia_cache[aphia_id] = None
            return errors

        if response.status_code == status.HTTP_400_BAD_REQUEST:
            error_message = f"Invalid lowest_aphia_id: {aphia_id} does not exist in WoRMS API."
            aphia_cache[aphia_id] = error_message
            errors["lowest_aphia_id"] = error_message
            return errors

        error_message = (
            f"Unable to validate lowest_aphia_id right now " f"(status {response.status_code}). Please try again later."
        )
        aphia_cache[aphia_id] = error_message
        errors["lowest_aphia_id"] = error_message
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


def _ingest_get_aphia_id_cached_worms(aphia_id: str) -> requests.Response:
    """Helper function to call the cached WoRMS API to validate an aphia_id.

    This is a POST request to trigger the ingest endpoint, which will return 200 if the aphia_id exists in WoRMS
    (either in cache or after fetching from live WoRMS), 204 if it does not exist in WoRMS, and 4xx/5xx if there was
    an error.

    Args:
        aphia_id (str): The aphia_id to test.

    Returns:
        requests.Response: The response from the WoRMS API.
    """
    client = CachedWoRMSClient()
    return client.ingest(aphia_id)
