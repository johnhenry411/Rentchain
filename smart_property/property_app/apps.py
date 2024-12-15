from django.apps import AppConfig


class ProperyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'property_app'

    def ready(self):
        import property_app.signals  # Ensure the signals are loaded
