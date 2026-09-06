from django.apps import AppConfig


class SiteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.site"
    label = "site_publico"
    verbose_name = "Site"

    def ready(self):
        from . import signals  # noqa: F401
