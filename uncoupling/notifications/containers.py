"""Dependency injection container for notifications module."""
from dependency_injector import containers, providers

from notifications.repositories import DBNotificationRepository
from notifications.services import NotificationService


class NotificationContainer(containers.DeclarativeContainer):
    """Dependency injection container for notifications module."""

    # Repositories
    notification_repository = providers.Singleton(DBNotificationRepository)

    # Services
    notification_service = providers.Singleton(
        NotificationService,
        notification_repository=notification_repository
    )


# Global container instance
notification_container = NotificationContainer()
