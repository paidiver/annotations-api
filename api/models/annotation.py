"""Models for annotations, annotators, and annotation labels."""

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError

from api.models.base import (
    AliasedShapesEnumField,
    DefaultColumns,
    HumanOrMachineEnum,
    MachineTrainingValidationEnum,
    ShapeEnum,
    enum_choices,
)
from api.models.validators import validate_coco_rle_mask


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

    shape = AliasedShapesEnumField(
        max_length=32,
        choices=enum_choices(ShapeEnum),
        help_text="The annotation shape is specified by a keyword.",
    )

    coordinates = models.JSONField(
        null=True,
        blank=True,
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

    label = models.ForeignKey(
        "Label",
        on_delete=models.CASCADE,
        related_name="annotation_labels",
        help_text="A unique identifier to a semantic label",
    )

    creators = models.ManyToManyField(
        "Annotator",
        blank=True,
        related_name="created_annotations",
        help_text="The human annotators involved in creating this annotation.",
    )

    creation_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="UTC date and time when the annotation was created.",
    )

    human_or_machine = models.CharField(
        max_length=32,
        choices=enum_choices(HumanOrMachineEnum),
        help_text="Whether the annotation was created by a human, algorithm, or combination of both.",
    )

    human_reviewer = models.ForeignKey(
        "Annotator",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_annotations",
        help_text="The human reviewer of this annotation, when applicable.",
    )
    machine_training_validation = models.CharField(
        max_length=16,
        choices=enum_choices(MachineTrainingValidationEnum),
        null=True,
        blank=True,
        help_text="Whether this annotation was used for training, validation, or both.",
    )
    additional_info = models.TextField(null=True, blank=True, help_text="Additional comments or observations.")
    detection_model = models.ForeignKey(
        "AnnotationSetModel", null=True, blank=True, on_delete=models.PROTECT,
        related_name="detected_annotations",
        help_text="The registered model that produced the annotation shape.",
    )
    classification_model = models.ForeignKey(
        "AnnotationSetModel", null=True, blank=True, on_delete=models.PROTECT,
        related_name="classified_annotations",
        help_text="The registered model that produced the annotation label.",
    )
    detection_confidence = models.FloatField(
        null=True, blank=True, help_text="Detection model score for the annotation shape."
    )
    classification_confidence = models.FloatField(
        null=True, blank=True, help_text="Classification model score for the assigned label."
    )

    mask = models.JSONField(
        null=True,
        blank=True,
        validators=[validate_coco_rle_mask],
        help_text="Per-pixel mask encoded as COCO RLE with encoding, width, height, and counts.",
    )

    annotation_set = models.ForeignKey(
        "AnnotationSet",
        on_delete=models.CASCADE,
        related_name="annotations",
        help_text="The annotation set this annotation belongs to",
    )

    class Meta:
        """Meta class for Annotation."""

        db_table = "annotations"
        constraints = [
            models.CheckConstraint(
                check=models.Q(detection_confidence__isnull=True)
                | models.Q(detection_confidence__gte=0, detection_confidence__lte=1),
                name="annotation_detection_confidence_0_1",
            ),
            models.CheckConstraint(
                check=models.Q(classification_confidence__isnull=True)
                | models.Q(classification_confidence__gte=0, classification_confidence__lte=1),
                name="annotation_classification_confidence_0_1",
            ),
        ]

    def __str__(self):
        """String representation of the Annotation instance."""
        return f"Annotation({self.pk})"

    def clean(self) -> None:
        """Validate confidence scores against their registered models."""
        super().clean()
        errors = {}
        if self.detection_confidence is not None:
            if self.detection_model is None:
                errors["detection_model"] = "A detection model is required when detection confidence is provided."
            elif not self.detection_model.score_type:
                errors["detection_model"] = "The detection model must define score_type when confidence is provided."
        if self.classification_confidence is not None:
            if self.classification_model is None:
                errors["classification_model"] = (
                    "A classification model is required when classification confidence is provided."
                )
            elif not self.classification_model.score_type:
                errors["classification_model"] = (
                    "The classification model must define score_type when confidence is provided."
                )
        if errors:
            raise ValidationError(errors)
