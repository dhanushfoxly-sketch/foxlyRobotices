from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0008_alter_projectupload_options_alter_projectupload_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='circuit_diagram',
        ),
        migrations.RemoveField(
            model_name='project',
            name='code_file',
        ),
    ]
