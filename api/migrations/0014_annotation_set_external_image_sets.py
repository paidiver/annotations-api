"""Store external image-set names and handles on annotation sets."""

from django.contrib.postgres.fields import ArrayField
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add fields for image sets that are not stored in the database."""

    dependencies = [
        ("api", "0013_annotation_set_quantification_arrays"),
    ]

    operations = [
        migrations.AddField(
            model_name="annotationset",
            name="image_set_names",
            field=ArrayField(
                base_field=models.CharField(max_length=255),
                blank=True,
                default=list,
                help_text="Names of external image sets when no database image-set relation is available.",
                size=None,
            ),
        ),
        migrations.AddField(
            model_name="annotationset",
            name="image_set_handles",
            field=ArrayField(
                base_field=models.CharField(max_length=2048),
                blank=True,
                default=list,
                help_text="Handles of external image sets when no database image-set relation is available.",
                size=None,
            ),
        ),
    ]
