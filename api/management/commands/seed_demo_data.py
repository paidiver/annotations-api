"""Management command to seed demo data for testing and development."""

import random
from argparse import ArgumentParser

from django.core.management.base import BaseCommand
from django.db import transaction

from api.factories.annotation import (
    AnnotationFactory,
    AnnotatorFactory,
)
from api.factories.annotation_set import AnnotationSetFactory, AnnotationSetModelFactory
from api.factories.image import ImageFactory
from api.factories.image_set import ImageSetFactory
from api.factories.label import LabelFactory
from api.factories.label_set import LabelSetFactory


class Command(BaseCommand):
    """Django management command to seed demo data for testing and development."""

    help = (
        "Seed demo data with configurable counts.\n\n"
        "Defaults replicate:\n"
        "- 2 image_sets\n"
        "- 2 annotation_sets (1 per image_set)\n"
        "- 2 label_sets (1 per annotation_set)\n"
        "- 20 images (10 per image_set)\n"
        "- 40 labels (20 per label_set)\n"
        "- 10 annotators\n"
        "- 40 annotations (2 per image)\n"
        "- 2 annotation models (1 per annotation_set)\n"
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
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
            "--labels-per-label-set",
            type=int,
            default=20,
            help="Number of Labels to create per LabelSet",
        )
        parser.add_argument("--annotators", type=int, default=10, help="Total number of Annotators to create")
        parser.add_argument(
            "--annotations-per-image",
            type=int,
            default=2,
            help="Number of Annotations to create per Image",
        )
        parser.add_argument(
            "--annotation-models-per-annotation-set",
            type=int,
            default=1,
            help="Number of AnnotationSetModel rows to create per AnnotationSet",
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
        labels_per_lset: int = options["labels_per_label_set"]
        n_annotators: int = options["annotators"]
        annotations_per_image: int = options["annotations_per_image"]
        annotation_models_per_set: int = options["annotation_models_per_annotation_set"]

        if n_image_annotation_sets <= 0:
            raise ValueError("--image-annotation-sets must be > 0")
        if (
            images_per_iset < 0
            or labels_per_lset < 0
            or n_annotators < 0
            or annotations_per_image < 0
            or annotation_models_per_set < 0
        ):
            raise ValueError("Counts must be >= 0")
        if images_per_iset > 0 and annotations_per_image > 0 and labels_per_lset == 0:
            raise ValueError("--labels-per-label-set must be > 0 when annotations are created")

        annotators = [AnnotatorFactory() for _ in range(n_annotators)]

        image_sets = []
        annotation_sets = []
        label_sets = []
        total_annotations = 0
        total_annotation_models = 0
        for _ in range(n_image_annotation_sets):
            image_set = ImageSetFactory(
                with_relations=True,
                with_camera_models=True,
                related_materials=3,
                creators=2,
                with_limits=True,
            )
            image_sets.append(image_set)
            label_set = LabelSetFactory(with_relations=True, creators=2, related_materials=2)
            label_sets.append(label_set)
            annotation_set = AnnotationSetFactory(
                with_relations=True,
                image_set_ids=[image_set.id],
                label_sets=[label_set],
            )
            annotation_sets.append(annotation_set)

            labels = [LabelFactory(label_set_id=label_set.id) for _ in range(labels_per_lset)]
            for _ in range(annotation_models_per_set):
                AnnotationSetModelFactory(annotation_set=annotation_set, label_set=label_set)
                total_annotation_models += 1
            images = [
                ImageFactory(
                    image_set_id=image_set.id,
                    with_relations=False,
                )
                for _ in range(images_per_iset)
            ]
            for img in images:
                for _ in range(annotations_per_image):
                    creators = [random.choice(annotators)] if annotators else []
                    AnnotationFactory(
                        image=img,
                        annotation_set=annotation_set,
                        label=random.choice(labels),
                        creators=creators,
                )
                    total_annotations += 1
        self.stdout.write(self.style.SUCCESS("Seed complete!"))
        self.stdout.write(f"ImageSets: {n_image_annotation_sets}")
        self.stdout.write(f"AnnotationSets: {n_image_annotation_sets} (each linked to one ImageSet)")
        self.stdout.write(f"Images: {images_per_iset} per ImageSet)")
        self.stdout.write(f"LabelSets: {len(label_sets)} (each linked to one AnnotationSet)")
        self.stdout.write(f"Labels: {labels_per_lset} per LabelSet)")
        self.stdout.write(f"Annotators: {n_annotators}")
        self.stdout.write(f"Annotations: {total_annotations}")
        self.stdout.write(f"AnnotationSetModels: {total_annotation_models}")
