from django.db import migrations, models
import django.db.models.deletion
"""
This migration removes the unique constraint on the combination of image_set and material in the ImageSetRelatedMaterial model.
And also renames the material field to related_material, and updates the corresponding db_column to related_material_id
and the constraint to uq_image_set_related_materials.
"""

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_remove_image_name_image_filename_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='imagesetrelatedmaterial',
            name='uq_image_set_related_materials',
        ),

        migrations.RenameField(
            model_name='imagesetrelatedmaterial',
            old_name='material',
            new_name='related_material',
        ),

        migrations.AlterField(
            model_name='imagesetrelatedmaterial',
            name='related_material',
            field=models.ForeignKey(
                db_column='related_material_id',
                on_delete=django.db.models.deletion.CASCADE,
                to='api.relatedmaterial',
            ),
        ),

        migrations.AddConstraint(
            model_name='imagesetrelatedmaterial',
            constraint=models.UniqueConstraint(
                fields=('image_set', 'related_material'),
                name='uq_image_set_related_materials',
            ),
        ),
    ]
