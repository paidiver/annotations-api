"""Model for semantic labels assigned to annotations."""

from django.contrib.gis.db import models

from api.models.base import DefaultColumns


class Label(DefaultColumns):
    """A semantic label that can be assigned to an annotation."""

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Name in BIIGLE label tree output; name of label as annotated",
    )

    parent_label_name = models.CharField(
        max_length=255,
        help_text="Name of parent to label_name",
    )

    lowest_taxonomic_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Most detailed taxonomic identification possible; scientificName field in DarwinCore",
    )

    lowest_aphia_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="The AphiaID corresponding to the lowest_taxonomic_name, if applicable",
    )

    name_is_lowest = models.BooleanField(
        default=False,
        help_text="Indicates whether the name field represents the lowest taxonomic identification",
    )

    identification_qualifier = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Open nomenclature signs (see Horton et al 2021); same field name in DarwinCore",
    )

    annotation_set = models.ForeignKey(
        "AnnotationSet",
        on_delete=models.CASCADE,
        related_name="labels",
        help_text="The annotation_set this label belongs to. An annotation_set can have multiple labels.",
    )

    class Meta:
        """Meta class for Label."""

        db_table = "labels"

    def __str__(self):
        """String representation of the Label instance."""
        return self.name
