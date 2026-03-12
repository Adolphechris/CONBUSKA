from django.apps import AppConfig


class ActivityLogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activity_logs'
    verbose_name = 'Journal d\'activités'

    def ready(self):
        from .signals import connect_all
        connect_all()
