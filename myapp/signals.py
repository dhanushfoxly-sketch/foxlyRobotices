from django.contrib.auth.models import User
from django.conf import settings

def create_admin():
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="Admin@12345"
        )