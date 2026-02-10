"""Management command to seed demo data for testing and development."""

import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from api.models import AnnotationLabel
from api.tests.factories.annotation_set import AnnotationSetFactory
from api.tests.factories.image import ImageFactory
from api.tests.factories.image_set import ImageSetFactory
from api.tests.factories.label import LabelFactory

from ...tests.factories.annotation import (
    AnnotationFactory,
    AnnotatorFactory,
)


class Command(BaseCommand):
    """Django management command to seed demo data for testing and development."""

    help = (
        "Seed demo data with configurable counts.\n\n"
        "Defaults replicate:\n"
        "- 2 image_sets\n"
        "- 2 annotation_sets (1 per image_set)\n"
        "- 20 images (10 per image_set)\n"
        "- 40 labels (20 per annotation_set)\n"
        "- 10 annotators\n"
        "- 40 annotations (2 per image)\n"
        "- 100 annotation_labels (random)\n"
    )

    def add_arguments(self, parser) -> None:
        """Add command-line arguments for configurable seeding.

        Args:
            parser: The argument parser to which we can add custom arguments.
        """
        parser.add_argument(
            "--image-annotation-sets", type=int, default=2, help="Number of ImageSets and AnnotationSets to create"
        )
        parser.add_argument(
            "--images-per-image-set",
            type=int,
            default=10,
            help="Number of Images to create per ImageSet (and thus per linked AnnotationSet)",
        )
        parser.add_argument(
            "--labels-per-annotation-set",
            type=int,
            default=20,
            help="Number of Labels to create per AnnotationSet",
        )
        parser.add_argument("--annotators", type=int, default=10, help="Total number of Annotators to create")
        parser.add_argument(
            "--annotations-per-image",
            type=int,
            default=2,
            help="Number of Annotations to create per Image",
        )
        parser.add_argument(
            "--annotation-labels",
            type=int,
            default=100,
            help="Total number of AnnotationLabel rows to create (random across annotations/labels/annotators)",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        """Seed demo data based on provided options.

        Args:
            *args: Positional arguments (not used here).
            **options: Command-line options for seeding counts.
        """
        n_image_annotation_sets: int = options["image_annotation_sets"]
        images_per_iset: int = options["images_per_image_set"]
        labels_per_aset: int = options["labels_per_annotation_set"]
        n_annotators: int = options["annotators"]
        annotations_per_image: int = options["annotations_per_image"]
        annotation_labels_per_set: int = options["annotation_labels"]

        if n_image_annotation_sets <= 0:
            raise ValueError("--image-annotation-sets must be > 0")
        if images_per_iset < 0 or labels_per_aset < 0 or n_annotators < 0 or annotations_per_image < 0:
            raise ValueError("Counts must be >= 0")

        annotators = [AnnotatorFactory() for _ in range(n_annotators)]

        image_sets = []
        annotation_sets = []
        total_created_annotation_labels = 0
        for _ in range(n_image_annotation_sets):
            image_set = ImageSetFactory(
                with_relations=True,
                with_camera_models=True,
                with_related_materials=3,
                with_creators=2,
                with_limits=True,
            )
            image_sets.append(image_set)
            annotation_set = AnnotationSetFactory(with_relations=True, image_set_ids=[image_set.id])
            annotation_sets.append(annotation_set)

            labels = [LabelFactory(annotation_set_id=annotation_set.id) for _ in range(labels_per_aset)]
            images = [
                ImageFactory(
                    image_set_id=image_set.id,
                    with_relations=False,
                )
                for _ in range(images_per_iset)
            ]
            annotations = []
            for img in images:
                for _ in range(annotations_per_image):
                    ann = AnnotationFactory(image=img, annotation_set=annotation_set)
                    annotations.append(ann)

            #    Ensure label.annotation_set matches annotation.annotation_set to keep data consistent.
            #    Respect unique constraint (label, annotation, annotator).
            possible = len(annotations) * len(labels) * len(annotators)
            target = min(annotation_labels_per_set, possible)
            created = 0
            attempts = 0
            max_attempts = annotation_labels_per_set * 50  # give it a bit more room

            while created < target and attempts < max_attempts:
                attempts += 1
                ann = random.choice(annotations)
                label = random.choice(labels)
                annotator = random.choice(annotators)

                _, was_created = AnnotationLabel.objects.get_or_create(
                    annotation=ann,
                    label=label,
                    annotator=annotator,
                    defaults={"creation_datetime": timezone.now()},
                )
                if was_created:
                    created += 1
                    total_created_annotation_labels += 1
            if created < target:
                self.stdout.write(
                    self.style.WARNING(
                        f"WARNING: Only created {created}/{target} AnnotationLabels due to uniqueness collisions."
                    )
                )
        self.stdout.write(self.style.SUCCESS("Seed complete!"))
        self.stdout.write(f"ImageSets: {n_image_annotation_sets}")
        self.stdout.write(f"AnnotationSets: {n_image_annotation_sets} (each linked to one ImageSet)")
        self.stdout.write(f"Images: {images_per_iset} per ImageSet)")
        self.stdout.write(f"Labels: {labels_per_aset} per AnnotationSet)")
        self.stdout.write(f"Annotators: {n_annotators}")
        self.stdout.write(f"Annotations: {annotations_per_image} per Image)")
        self.stdout.write(f"AnnotationLabels created: {total_created_annotation_labels}")
