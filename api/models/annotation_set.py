"""AnnotationSet model module."""

from django.contrib.gis.db import models

from api.models.base import DefaultColumns
from api.models.common_fields import CommonFieldsAll


class AnnotationSetCreator(models.Model):
    """Association table between AnnotationSet and Creator."""

    annotation_set = models.ForeignKey(
        "AnnotationSet",
        on_delete=models.CASCADE,
        db_column="annotation_set_id",
        related_name="annotation_set_creator_links",
    )
    creator = models.ForeignKey(
        "Creator",
        on_delete=models.CASCADE,
        db_column="creator_id",
        related_name="annotation_set_creator_links",
    )

    class Meta:
        """Meta class for AnnotationSetCreator."""

        db_table = "annotation_set_creators"
        constraints = [
            models.UniqueConstraint(
                fields=["annotation_set", "creator"],
                name="uq_annotation_set_creator",
            )
        ]


class AnnotationSetImageSet(models.Model):
    """Association table between AnnotationSet and ImageSet."""

    annotation_set = models.ForeignKey(
        "AnnotationSet",
        on_delete=models.CASCADE,
        db_column="annotation_set_id",
        related_name="annotation_set_image_set_links",
    )
    image_set = models.ForeignKey(
        "ImageSet",
        on_delete=models.CASCADE,
        db_column="image_set_id",
        related_name="annotation_set_image_set_links",
    )

    class Meta:
        """Meta class for AnnotationSetImageSet."""

        db_table = "annotation_set_image_sets"
        constraints = [
            models.UniqueConstraint(
                fields=["annotation_set", "image_set"],
                name="uq_annotation_set_image_set",
            )
        ]


class AnnotationSet(CommonFieldsAll, DefaultColumns):
    """A collection of annotations that are related to a specific project, event, or context."""

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text=("A unique name for the annotation set."),
    )

    context = models.ForeignKey(
        "Context",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="annotation_sets",
        help_text="The overarching project context within which the annotation set was created",
    )
    project = models.ForeignKey(
        "Project",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="annotation_sets",
        help_text=(
            "The more specific project or expedition or cruise or experiment or ... within which "
            "the annotation set was created."
        ),
    )
    pi = models.ForeignKey(
        "PI",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="annotation_sets",
        help_text="A URI pointing to a description of the principal investigator of the annotation set",
    )
    license = models.ForeignKey(
        "License",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="annotation_sets",
        help_text="A URI pointing to the license to use the data (should be FAIR, e.g. CC-BY or CC-0)",
    )

    creators = models.ManyToManyField(
        "Creator",
        through=AnnotationSetCreator,
        related_name="annotation_sets",
        help_text="Information to identify the creators of the annotation set",
        blank=True,
    )

    version = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="The version of the annotation set.",
    )

    image_sets = models.ManyToManyField(
        "ImageSet",
        through=AnnotationSetImageSet,
        related_name="annotation_sets",
        help_text="Relationship to image_sets included in this annotation set.",
        blank=True,
    )

    class Meta:
        """Meta class for AnnotationSet."""

        db_table = "annotation_sets"

    def __str__(self):
        """String representation of the AnnotationSet instance.

        Returns:
            A string representing the AnnotationSet instance.
        """
        return f"AnnotationSet(id={self.pk}, version={self.version})"
