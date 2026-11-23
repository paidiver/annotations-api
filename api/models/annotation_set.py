"""AnnotationSet model module."""

from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import RegexValidator

from api.models.base import (
    AnnotationModelEnum,
    DefaultColumns,
    QualitativeOrQuantitativeEnum,
    QuantificationTypeEnum,
    enum_choices,
)
from api.models.common_fields import CommonFieldsAll
from api.models.validators import validate_uuid_or_uri


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

    label_sets = models.ManyToManyField(
        "LabelSet",
        related_name="annotation_sets",
        blank=True,
        help_text="Label sets containing the labels used by this annotation set.",
    )

    connected_sets = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="connected_from_sets",
        help_text="Directed links to connected annotation sets, including previous versions.",
    )

    machine_scope = models.TextField(
        null=True,
        blank=True,
        help_text="Scope of machine use, including training, validation, and its role in the study.",
    )
    related_materials = models.ManyToManyField(
        "RelatedMaterial",
        related_name="annotation_sets",
        blank=True,
        help_text="Papers, websites, software, or documentation associated with the annotation set.",
    )
    quantitative_or_qualitative = models.CharField(
        max_length=32,
        choices=enum_choices(QualitativeOrQuantitativeEnum),
        null=True,
        blank=True,
        help_text="Whether observations are qualitative, semi-quantitative, or quantitative.",
    )
    quantification_type = models.CharField(
        max_length=255,
        choices=enum_choices(QuantificationTypeEnum),
        null=True,
        blank=True,
        help_text="The planned type of quantification, such as count, measurement, or rate.",
    )
    biological_metrics = models.TextField(null=True, blank=True, help_text="Planned derived biological metrics.")
    biological_stats = models.TextField(
        null=True, blank=True, help_text="Planned statistical comparisons and sampling design."
    )
    obis_handles = ArrayField(
        base_field=models.CharField(max_length=2048),
        null=True,
        blank=True,
        help_text="DOIs or UUIDs of archived OBIS datasets derived from these annotations.",
    )
    funding = models.TextField(null=True, blank=True, help_text="Funding attribution for the annotation set.")

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
        return f"AnnotationSet(id={self.pk})"


class AnnotationSetModel(DefaultColumns):
    """A machine-learning model used to produce annotations in an annotation set."""

    annotation_set = models.ForeignKey(
        "AnnotationSet",
        on_delete=models.CASCADE,
        related_name="annotation_models",
        help_text="The annotation set in which this model identifier is registered.",
    )
    model_id = models.CharField(max_length=255, help_text="Identifier unique within the annotation set.")
    name = models.CharField(max_length=255, help_text="Name of the model or architecture.")
    version = models.CharField(max_length=255, help_text="Version of the trained model weights.")
    task = models.CharField(
        max_length=32,
        choices=enum_choices(AnnotationModelEnum),
        null=True,
        blank=True,
        help_text="The task performed by the model.",
    )
    handle = models.CharField(
        max_length=2048,
        null=True,
        blank=True,
        help_text="Persistent URI or DOI for the model weights or model card.",
    )
    weights_sha256 = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^[0-9a-f]{64}$",
                message="Enter exactly 64 lowercase hexadecimal characters.",
            )
        ],
        help_text="SHA-256 hash of the exact model weights file, as 64 lowercase hexadecimal characters.",
    )
    description = models.TextField(
        null=True, blank=True, help_text="Inference settings and details of how the model was applied."
    )
    score_type = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Meaning of confidence scores produced by this model.",
    )
    confidence_threshold = models.FloatField(
        null=True,
        blank=True,
        help_text="Minimum model score retained, between zero and one.",
    )
    label_set = models.ForeignKey(
        "LabelSet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="annotation_models",
        help_text="Label set containing the model output classes, when different from the annotation set default.",
    )
    training_image_set = models.CharField(
        max_length=2048,
        null=True,
        blank=True,
        validators=[validate_uuid_or_uri],
        help_text="UUID or URI of the training image set.",
    )
    training_annotation_set = models.CharField(
        max_length=2048,
        null=True,
        blank=True,
        validators=[validate_uuid_or_uri],
        help_text="UUID or URI of the training annotation set.",
    )
    validation_image_set = models.CharField(
        max_length=2048,
        null=True,
        blank=True,
        validators=[validate_uuid_or_uri],
        help_text="UUID or URI of the validation image set.",
    )
    validation_annotation_set = models.CharField(
        max_length=2048,
        null=True,
        blank=True,
        validators=[validate_uuid_or_uri],
        help_text="UUID or URI of the validation annotation set.",
    )

    class Meta:
        """Database metadata for an annotation set model."""

        db_table = "annotation_set_models"
        constraints = [
            models.UniqueConstraint(fields=["annotation_set", "model_id"], name="uq_annotation_set_model_id"),
            models.CheckConstraint(
                check=models.Q(confidence_threshold__isnull=True)
                | models.Q(confidence_threshold__gte=0, confidence_threshold__lte=1),
                name="annotation_model_confidence_threshold_0_1",
            ),
        ]

    def __str__(self):
        return f"{self.model_id}: {self.name} {self.version}"
