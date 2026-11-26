"""Allow annotations to reference external images by filename."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0014_annotation_set_external_image_sets"),
    ]

    operations = [
        migrations.AddField(
            model_name="annotation",
            name="image_filename",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AlterField(
            model_name="annotation",
            name="image",
            field=models.ForeignKey(
                blank=True,
                help_text="A unique identifier to the image this annotation belongs to",
                null=True,
                on_delete=models.CASCADE,
                related_name="annotations",
                to="api.image",
            ),
        ),
    ]
