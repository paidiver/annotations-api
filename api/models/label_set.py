"""Models for collections of semantic labels."""

from django.contrib.gis.db import models

from api.models.base import DefaultColumns
from api.models.common_fields import CommonFieldsAll


class LabelSetCreator(models.Model):
    """Association table between a label set and its creators."""

    label_set = models.ForeignKey("LabelSet", on_delete=models.CASCADE, related_name="label_set_creator_links")
    creator = models.ForeignKey("Creator", on_delete=models.CASCADE, related_name="label_set_creator_links")

    class Meta:
        """Database metadata for the label-set creator association."""

        db_table = "label_set_creators"
        constraints = [models.UniqueConstraint(fields=["label_set", "creator"], name="uq_label_set_creator")]


class LabelSet(CommonFieldsAll, DefaultColumns):
    """A versioned, reusable collection of semantic labels."""

    name = models.CharField(max_length=255, unique=True, help_text="A unique name for the label set.")
    project = models.ForeignKey(
        "Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="label_sets",
        help_text="The project within which the label set was created.",
    )
    context = models.ForeignKey(
        "Context",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="label_sets",
        help_text="The expedition, cruise, experiment, or other context for the label set.",
    )
    pi = models.ForeignKey(
        "PI",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="label_sets",
        help_text="Principal investigator associated with the label set.",
    )
    license = models.ForeignKey(
        "License",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="label_sets",
        help_text="License under which the label set may be used.",
    )
    creators = models.ManyToManyField(
        "Creator",
        through=LabelSetCreator,
        related_name="label_sets",
        blank=True,
        help_text="People or organisations that created the label set.",
    )
    related_materials = models.ManyToManyField(
        "RelatedMaterial",
        related_name="label_sets",
        blank=True,
        help_text="Papers, websites, software, or documentation associated with the label set.",
    )
    catalogue = models.CharField(
        max_length=2048,
        null=True,
        blank=True,
        help_text="URL or DOI of a catalogue or vocabulary used by the label set.",
    )
    funding = models.TextField(null=True, blank=True, help_text="Funding attribution for the label set.")

    class Meta:
        """Database metadata for label sets."""

        db_table = "label_sets"

    def __str__(self):
        return self.name
