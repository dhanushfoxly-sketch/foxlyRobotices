# Generated migration to change circuit_diagram to ImageField and make files optional

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0004_projectcomponent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='circuit_diagram',
            field=models.ImageField(blank=True, null=True, upload_to='projects/circuit_diagrams/'),
        ),
        migrations.AlterField(
            model_name='project',
            name='code_file',
            field=models.FileField(blank=True, null=True, upload_to='projects/code_files/'),
        ),
    ]
