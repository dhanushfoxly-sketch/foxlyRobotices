from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0011_delete_projectupload'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='zip_file',
            field=models.FileField(blank=True, null=True, upload_to='projects/zips/'),
        ),
    ]
