"""Service functions related to annotation data."""

from itertools import zip_longest

import pandas as pd
from django.db import transaction

from api.models.fields import PI, Context, Creator, License, Project
from api.models.image_set import ImageSet
from api.serializers import AnnotationSetSerializer


def insert_annotations_into_tables(data: pd.DataFrame):
    """Insert annotations related into respective tables.

    Args:
        data(pd.DataFrame): annotation dataframe.

    Returns:
        newly created annotation_set object
    """
    with transaction.atomic():
        # Handle Project
        project, _ = Project.objects.get_or_create(
                name=data.get("annotation-project-name", ""),
                defaults={"uri": data.get("annotation-project-uri", "")}
            )

        # Handle PI
        pi, _ = PI.objects.get_or_create(
            name=data.get("annotation-pi-name", ""),
            defaults={"uri": data.get("annotation-pi-uri", "")}
        )

        # Handle Context
        context, _ = Context.objects.get_or_create(
            name=data.get("annotation-context-name", ""),
            defaults={"uri": data.get("annotation-context-uri", "")}
        )

        # handle License
        license, _ = License.objects.get_or_create(  # noqa: A001
            name=data.get("annotation-license-name", ""),
            defaults={"uri": data.get("annotation-license-uri", "")}
        )

        # Prepare data for AnnotationSet
        set_data = {
            "name": data.get("annotation-set-name", ""),
            "project": project.id,
            "context": context.id,
            "pi": pi.id,
            "license": license.id,
            "abstract": data.get("annotation-abstract", ""),
            "objective": data.get("annotation-objective", ""),
            "target_environment": data.get("annotation-target-environment", ""),
            "target_timescale": data.get("annotation-target-timescale", ""),
            "curation_protocol": data.get("annotation-curation-protocol", ""),
            "handle": data.get("annotation-set-handle", ""),
            "copyright": data.get("annotation-set-copyright", ""),
            "version": str(data.get("annotation-set-version", '1')),
        }

        serializer = AnnotationSetSerializer(data=set_data)
        if serializer.is_valid(raise_exception=True):
            annotation_set = serializer.save()

            # Handle Many-to-Many Creators
            if data.get('annotation-creators-names'):
                names_list = [n.strip() for n in data.get('annotation-creators-names', '').split(',') if n.strip()]
                uris_list  = [u.strip() for u in data.get('annotation-creators-uris', '').split(',') if u.strip()]

                for name, uri in zip_longest(names_list, uris_list, fillvalue=None):
                    creator, _ = Creator.objects.get_or_create(name=name, uri=uri)
                    annotation_set.creators.add(creator)

            # Handle Many-to-Many image-sets
            if data.get('annotation-image-set-name'):
                image_set, _ = ImageSet.objects.get_or_create(
                    name=data.get('annotation-image-set-name'),
                    id=data.get('annotation-image-set-uuid'),
                    handle=data.get('annotation-image-set-handle'))
                annotation_set.image_sets.add(image_set)

        return annotation_set
