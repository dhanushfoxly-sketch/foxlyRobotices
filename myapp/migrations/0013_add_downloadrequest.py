from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0012_add_project_zip'),
    ]

    operations = [
        migrations.CreateModel(
            name='DownloadRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=30, null=True)),
                ('message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('access_code', models.CharField(blank=True, max_length=32, null=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('is_used', models.BooleanField(default=False)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('request_token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('project', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='download_requests', to='myapp.project')),
            ],
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'Download Request',
                'verbose_name_plural': 'Download Requests',
            },
        ),
    ]
