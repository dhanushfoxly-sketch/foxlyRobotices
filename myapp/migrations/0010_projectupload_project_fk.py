from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0009_remove_project_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectupload',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploads', to='myapp.project'),
        ),
    ]
