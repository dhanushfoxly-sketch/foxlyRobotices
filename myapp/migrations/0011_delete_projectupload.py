from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0010_projectupload_project_fk'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ProjectUpload',
        ),
    ]
