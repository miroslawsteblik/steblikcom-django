from django.apps import AppConfig


class EmailingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "steblik.emailing"
    label = "emailing"
    verbose_name = "Email"
