from django.apps import AppConfig


class EcommerceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ecommerce'
    verbose_name = "Boutique en ligne"

    def ready(self):
        """
        Enregistre les signaux Django au démarrage de l'application.
        """
        import ecommerce.signals  # noqa: F401