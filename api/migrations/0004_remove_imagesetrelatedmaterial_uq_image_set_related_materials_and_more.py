from django.db import migrations, models
import django.db.models.deletion


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

        # Only needed if you are changing/pinning db_column
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
