from django.apps import AppConfig

class MyappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "myapp"

    def ready(self):
        try:
            from .signals import create_admin
            create_admin()
        except Exception:
            pass
