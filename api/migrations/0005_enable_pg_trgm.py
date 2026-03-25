from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0004_rename_material_in_imagesetrelatedmaterial_table_to_related_material'),
    ]
    operations = [
        TrigramExtension(),
    ]
