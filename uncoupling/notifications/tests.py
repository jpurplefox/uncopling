"""Tests for notifications module."""
from django.contrib.auth.models import User
from my_auth.models import MeliUser
from notifications.services import NotificationService
from notifications.repositories import (
    QuestionNotificationData,
    OrderNotificationData,
)


def test_create_question_notification_returns_question_type(notification_repository):
    """Test that creating a question notification returns QuestionNotificationData."""
    # Arrange
    user = User(username='testuser', email='test@example.com')
    meli_user = MeliUser(id=12345, user=user)
    service = NotificationService(notification_repository)

    # Act
    notification = service.create_question_notification(
        meli_user=meli_user,
        question_id=111,
        question_text='¿Tiene garantía?'
    )

    # Assert
    assert isinstance(notification, QuestionNotificationData)
    assert notification.type == 'question'
    assert notification.question_id == 111
    assert notification.title == 'Nueva pregunta recibida'
    assert '¿Tiene garantía?' in notification.message
    assert notification.get_icon() == '❓'
    assert notification.get_url() == '/questions/'


def test_create_order_notification_returns_order_type(notification_repository):
    """Test that creating an order notification returns OrderNotificationData."""
    # Arrange
    user = User(username='testuser', email='test@example.com')
    meli_user = MeliUser(id=12345, user=user)
    service = NotificationService(notification_repository)

    # Act
    notification = service.create_order_notification(
        meli_user=meli_user,
        order_id=987654321,
        status='paid'
    )

    # Assert
    assert isinstance(notification, OrderNotificationData)
    assert notification.type == 'order'
    assert notification.order_id == 987654321
    assert notification.status_change == 'paid'
    assert notification.title == 'Tu orden ha sido pagada'
    assert '987654321' in notification.message
    assert notification.get_icon() == '📦'
    assert notification.get_status_display() == 'Pagada'


def test_get_by_user_returns_all_notification_types(notification_repository):
    """Test that get_by_user returns mixed notification types."""
    # Arrange
    user = User(username='testuser', email='test@example.com')
    meli_user = MeliUser(id=12345, user=user)
    service = NotificationService(notification_repository)

    # Act - Create multiple notification types
    service.create_question_notification(
        meli_user=meli_user,
        question_id=111,
        question_text='Primera pregunta'
    )
    service.create_order_notification(
        meli_user=meli_user,
        order_id=987654321,
        status='paid'
    )
    service.create_question_notification(
        meli_user=meli_user,
        question_id=222,
        question_text='Segunda pregunta'
    )

    notifications = notification_repository.get_by_user(meli_user)

    # Assert
    assert len(notifications) == 3
    assert isinstance(notifications[0], QuestionNotificationData)
    assert isinstance(notifications[1], OrderNotificationData)
    assert isinstance(notifications[2], QuestionNotificationData)

    # Verify polymorphic behavior - each type has its own icon
    assert notifications[0].get_icon() == '❓'
    assert notifications[1].get_icon() == '📦'
    assert notifications[2].get_icon() == '❓'


def test_order_notification_status_display_variations(notification_repository):
    """Test that OrderNotificationData displays different statuses correctly."""
    # Arrange
    user = User(username='testuser', email='test@example.com')
    meli_user = MeliUser(id=12345, user=user)
    service = NotificationService(notification_repository)

    # Act & Assert - Test different statuses
    paid_notification = service.create_order_notification(
        meli_user=meli_user,
        order_id=1,
        status='paid'
    )
    assert paid_notification.get_status_display() == 'Pagada'

    confirmed_notification = service.create_order_notification(
        meli_user=meli_user,
        order_id=2,
        status='confirmed'
    )
    assert confirmed_notification.get_status_display() == 'Confirmada'

    cancelled_notification = service.create_order_notification(
        meli_user=meli_user,
        order_id=3,
        status='cancelled'
    )
    assert cancelled_notification.get_status_display() == 'Cancelada'


def test_notifications_are_unread_by_default(notification_repository):
    """Test that newly created notifications are unread."""
    # Arrange
    user = User(username='testuser', email='test@example.com')
    meli_user = MeliUser(id=12345, user=user)
    service = NotificationService(notification_repository)

    # Act
    notification = service.create_question_notification(
        meli_user=meli_user,
        question_id=111,
        question_text='Test question'
    )

    # Assert
    assert notification.is_read is False
    assert notification.read_at is None
