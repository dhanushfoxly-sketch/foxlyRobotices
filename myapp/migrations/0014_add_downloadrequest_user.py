from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0013_add_downloadrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='downloadrequest',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='download_requests', to=settings.AUTH_USER_MODEL),
        ),
    ]
