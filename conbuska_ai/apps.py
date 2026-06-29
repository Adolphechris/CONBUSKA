"""
conbuska_ai/apps.py

Configuration de l'application Conbuska AI.
"""

from django.apps import AppConfig


class ConbuskaAiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'conbuska_ai'
    verbose_name = 'Conbuska AI'

    def ready(self):
        """Import des signaux et initialisations."""
        pass