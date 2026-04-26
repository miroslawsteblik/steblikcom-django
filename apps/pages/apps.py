from django.apps import AppConfig


class PagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.pages"
    label = "pages"

    def ready(self) -> None:
        from django.db.models.signals import post_migrate
        post_migrate.connect(_sync_site, sender=self)


def _sync_site(**_) -> None:
    from django.conf import settings
    from django.contrib.sites.models import Site
    Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={"domain": settings.SITE_DOMAIN, "name": settings.SITE_DOMAIN},
    )
