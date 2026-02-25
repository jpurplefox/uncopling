"""App configuration for notifications module."""
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        import notifications.signals  # noqa: F401
        from notifications.containers import notification_container

        notification_container.wire(modules=['notifications.views', 'notifications.signals'])
