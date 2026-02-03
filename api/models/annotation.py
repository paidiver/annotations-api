"""Models for annotations, annotators, and annotation labels."""

from django.db import models

from api.models.base import DefaultColumns, ShapeEnum, enum_choices


class Image(DefaultColumns):
    """Placeholder Image model for ForeignKey reference."""


    class Meta:
        """Meta class for Image."""

        db_table = "images"



class Annotator(DefaultColumns):
    """An annotator is a person or machine that creates annotations."""

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="A human-readable name for the annotator (identifying the specific human or machine)",
    )

    class Meta:
        """Meta class for Annotator."""

        db_table = "annotators"

    def __str__(self):
        """String representation of the Annotator instance."""
        return self.name


class Annotation(DefaultColumns):
    """An annotation is a description of a specific part of an image or video."""

    image = models.ForeignKey(
        "Image",
        on_delete=models.CASCADE,
        related_name="annotations",
        help_text="A unique identifier to the image this annotation belongs to",
    )

    annotation_platform = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="The platform used to create the annotation, e.g., 'BIIGLE', 'VARS', 'SQUIDLE+', none",
    )

    shape = models.CharField(
        max_length=32,
        choices=enum_choices(ShapeEnum),
        help_text="The annotation shape is specified by a keyword.",
    )

    coordinates = models.JSONField(
        help_text=(
            "The pixel coordinates of one annotation. The top-left corner of an image is the (0,0) coordinate. "
            "The x-axis is the horizontal axis. Pixel coordinates may be fractional. Coordinates are to be "
            "given as a list of lists (only one element for photos, optionally multiple elements for videos). "
            "The required number of pixel coordinates is defined by the shape (0 for whole-image, 2 for single-pixel, "
            "3 for circle, 8 for ellipse/rectangle, 4 or more for polyline, 8 or more for polygon). The third "
            "coordinate value of a circle defines the radius. The first and last coordinates of a polygon must "
            "be equal. Format: [[p1.x,p1.y,p2x,p2.y,...]..]"
        )
    )

    dimension_pixels = models.FloatField(
        null=True,
        blank=True,
        help_text=(
            "The real-world dimension (e.g., length, diameter) in pixels corresponding to the annotation, if applicable"
        ),
    )

    annotation_set = models.ForeignKey(
        "AnnotationSet",
        on_delete=models.CASCADE,
        related_name="annotations",
        help_text="The annotation set this annotation belongs to",
    )

    labels = models.ManyToManyField(
        "Label",
        through="AnnotationLabel",
        related_name="annotations",
        blank=True,
    )

    class Meta:
        """Meta class for Annotation."""

        db_table = "annotations"

    def __str__(self):
        """String representation of the Annotation instance."""
        return f"Annotation({self.pk})"


class AnnotationLabel(DefaultColumns):
    """A label assigned to an annotation by an annotator."""

    label = models.ForeignKey(
        "Label",
        on_delete=models.CASCADE,
        related_name="annotation_labels",
        help_text="A unique identifier to a semantic label",
    )

    annotation = models.ForeignKey(
        "Annotation",
        on_delete=models.CASCADE,
        related_name="annotation_labels",
        help_text="A unique identifier to the annotation this label is assigned to",
    )

    annotator = models.ForeignKey(
        "Annotator",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="annotation_labels",
        help_text="A unique identifier to an annotation creator, e.g. orcid URL or handle to ML model",
    )

    creation_datetime = models.CharField(
        max_length=255,
        help_text="The date-time stamp of label creation",
    )

    class Meta:
        """Meta class for AnnotationLabel."""

        db_table = "annotation_labels"
        constraints = [
            models.UniqueConstraint(
                fields=["label", "annotation", "annotator"],
                name="uq_annotation_label_annotation_annotator",
            )
        ]

    def __str__(self):
        """String representation of the AnnotationLabel instance."""
        return f"AnnotationLabel(annotation={self.annotation_id}, label={self.label_id})"
