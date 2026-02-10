from __future__ import annotations

import random

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.utils import timezone

from api.models import AnnotationLabel, AnnotationSetImageSet

from .annotation import (
    AnnotationFactory,
    AnnotatorFactory,
)
from .annotation_set import AnnotationSetFactory
from .image import ImageFactory
from .image_set import ImageSetFactory
from .label import LabelFactory


class Command(BaseCommand):
    """Django management command to seed demo data for testing and development."""

    help = (
        "Seed demo data:\n"
        "- 2 image_sets\n"
        "- 2 annotation_sets, each linked to one image_set\n"
        "- 20 images (10 per image_set)\n"
        "- 40 labels (20 per annotation_set)\n"
        "- 10 annotators\n"
        "- 40 annotations (2 per image)\n"
        "- 100 annotation_labels (random label+annotator+annotation)\n"
    )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        """Seed the database with demo data following the specified relationships and constraints."""
        # -------------------------
        # 1) Create 2 ImageSets
        # -------------------------
        image_sets = [
            ImageSetFactory(with_relations=True, with_camera_models=True),
            ImageSetFactory(with_relations=True, with_camera_models=True),
        ]

        # -------------------------
        # 2) Create 2 AnnotationSets and link each to one ImageSet
        # -------------------------
        annotation_sets = [
            AnnotationSetFactory(with_relations=True),
            AnnotationSetFactory(with_relations=True),
        ]

        # Link each annotation_set to exactly one image_set (through table)
        for aset, iset in zip(annotation_sets, image_sets, strict=False):
            AnnotationSetImageSet.objects.get_or_create(annotation_set=aset, image_set=iset)

        # Convenience mapping: image_set_id -> annotation_set
        iset_to_aset: dict[int, object] = {
            iset.id: aset for iset, aset in zip(image_sets, annotation_sets, strict=False)
        }

        # -------------------------
        # 3) Create 20 Images (10 per ImageSet)
        # -------------------------
        images = []
        for iset in image_sets:
            for _ in range(10):
                img = ImageFactory(
                    image_set_id=iset.id,
                    with_relations=False,
                )
                images.append(img)

        # -------------------------
        # 4) Create 40 Labels (20 per AnnotationSet)
        # -------------------------
        labels_by_aset_id: dict[int, list[object]] = {}
        for aset in annotation_sets:
            labels = [LabelFactory(annotation_set=aset) for _ in range(20)]
            labels_by_aset_id[aset.id] = labels

        # -------------------------
        # 5) Create 10 Annotators
        # -------------------------
        annotators = [AnnotatorFactory() for _ in range(10)]

        # -------------------------
        # 6) Create 40 Annotations (2 per Image)
        #    AnnotationSet chosen based on the Image's ImageSet
        # -------------------------
        annotations = []
        for img in images:
            aset = iset_to_aset[img.image_set_id]
            for _ in range(2):
                ann = AnnotationFactory(image=img, annotation_set=aset)
                annotations.append(ann)

        # -------------------------
        # 7) Create 100 AnnotationLabels (random label + annotator + annotation)
        #    Ensure label.annotation_set matches annotation.annotation_set to keep data consistent.
        #    Respect unique constraint (label, annotation, annotator).
        # -------------------------
        target = 100
        created = 0
        attempts = 0
        max_attempts = 2000  # safety to avoid infinite loops if uniqueness collisions occur

        while created < target and attempts < max_attempts:
            attempts += 1
            ann = random.choice(annotations)

            # pick a label from the SAME annotation_set as the annotation
            label = random.choice(labels_by_aset_id[ann.annotation_set_id])

            annotator = random.choice(annotators)

            try:
                AnnotationLabel.objects.create(
                    annotation=ann,
                    label=label,
                    annotator=annotator,
                    creation_datetime=timezone.now(),
                )
                created += 1
            except IntegrityError:
                # likely hit uq_annotation_label_annotation_annotator; try again
                continue

        # -------------------------
        # Summary output
        # -------------------------
        self.stdout.write(self.style.SUCCESS("Seed complete!"))
        self.stdout.write(f"ImageSets: {len(image_sets)}")
        self.stdout.write(f"AnnotationSets: {len(annotation_sets)} (each linked to one ImageSet)")
        self.stdout.write(f"Images: {len(images)} (10 per ImageSet)")
        self.stdout.write("Labels: 40 (20 per AnnotationSet)")
        self.stdout.write(f"Annotators: {len(annotators)}")
        self.stdout.write(f"Annotations: {len(annotations)} (2 per Image)")
        self.stdout.write(f"AnnotationLabels created: {created} (attempts: {attempts})")

        if created < target:
            self.stdout.write(
                self.style.WARNING(
                    f"WARNING: Only created {created}/{target} AnnotationLabels due to uniqueness collisions."
                )
            )
