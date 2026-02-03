"""Common fields module for models."""

from django.db import models


class CommonFieldsAll(models.Model):
    """Common fields used across multiple tables."""

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text=(
            "A unique name for the image set, image or annotation set."
        ),
    )

    handle = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="A Handle URL to point to the landing page of the image set, image or annotation set.",
    )

    copyright = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Copyright statement or contact person or office for the image set, image or annotation set.",
    )

    abstract = models.TextField(
        null=True,
        blank=True,
        help_text=(
            "500 - 2000 characters describing what, when, where, why and how the data was collected/annotated. "
            "Includes general information on the event (aka station, experiment), e.g. overlap between "
            "images/frames, parameters on platform movement, aims, purpose of image capture etc."
        ),
    )

    objective = models.TextField(
        null=True,
        blank=True,
        help_text="A general description of the aims and objectives...",
    )

    target_environment = models.TextField(
        null=True,
        blank=True,
        help_text="A description of the habitat or environment...",
    )

    target_timescale = models.TextField(
        null=True,
        blank=True,
        help_text="A description of the period or temporal environment...",
    )

    curation_protocol = models.TextField(
        null=True,
        blank=True,
        help_text="A description of the image/annotation and metadata curation...",
    )

    class Meta:
        """Meta class for CommonFieldsAll."""

        abstract = True
