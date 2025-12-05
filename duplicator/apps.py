from django.apps import AppConfig


class DuplicatorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "duplicator"
    verbose_name = "Django duplicator utility"

    def ready(self):
        pass
