"""Test fixtures for notifications module."""
import pytest
from datetime import datetime
from unittest.mock import create_autospec
from notifications.repositories import (
    NotificationRepository,
    NotificationData,
    QuestionNotificationData,
    OrderNotificationData,
)


class InMemoryNotificationRepository:
    """In-memory implementation of NotificationRepository for testing."""

    def __init__(self):
        self._notifications = []
        self._next_id = 1

    def save(self, notification_data):
        """Save a notification in memory and return persisted version with ID."""
        # Create a new instance with the generated ID
        persisted_data = notification_data.model_copy(update={'id': self._next_id})

        self._notifications.append(persisted_data)
        self._next_id += 1

        return persisted_data

    def get_by_user(self, meli_user):
        """Get all notifications for a user."""
        return [
            n for n in self._notifications
            if n.meli_user_id == meli_user.id
        ]

    def mark_as_read(self, notification_id: int):
        """Mark a notification as read."""
        for notification in self._notifications:
            if notification.id == notification_id:
                notification.is_read = True
                notification.read_at = datetime.now()
                return notification
        return None


@pytest.fixture
def notification_repository():
    """Provide an in-memory notification repository."""
    return InMemoryNotificationRepository()


@pytest.fixture
def mock_notification_repository():
    """Provide a mock notification repository."""
    return create_autospec(NotificationRepository, instance=True)
