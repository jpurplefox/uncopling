"""Repository pattern with polymorphic Pydantic models for notifications."""
from datetime import datetime
from typing import Protocol, Optional, List
from django.db import transaction
from pydantic import BaseModel, ConfigDict

from my_auth.models import MeliUser
from notifications.models import Notification


# ========== Pydantic Models (Domain) - Polymorphic ==========

class NotificationData(BaseModel):
    """Base notification domain model."""
    id: Optional[int] = None
    type: str
    meli_user_id: int
    title: str
    message: str
    created_at: datetime
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @property
    def is_read(self) -> bool:
        """Check if notification has been read."""
        return self.read_at is not None

    def get_icon(self) -> str:
        """Get icon for notification type."""
        return "🔔"

    def get_url(self) -> str:
        """Get URL to view the notification."""
        return "/notifications/"


class QuestionNotificationData(NotificationData):
    """Notification for new questions."""
    question_id: int

    def get_icon(self) -> str:
        return "❓"

    def get_url(self) -> str:
        """Get URL to view the question."""
        return f"/questions/"

    def get_preview(self) -> str:
        """Get preview text."""
        return self.message[:100] + "..." if len(self.message) > 100 else self.message


class OrderNotificationData(NotificationData):
    """Notification for order updates."""
    order_id: int
    status_change: str

    def get_icon(self) -> str:
        return "📦"

    def get_url(self) -> str:
        """Get URL to view the order."""
        return f"/orders/"

    def get_status_display(self) -> str:
        """Get human-readable status change."""
        status_map = {
            'paid': 'Pagada',
            'confirmed': 'Confirmada',
            'payment_required': 'Pago requerido',
            'cancelled': 'Cancelada',
        }
        return status_map.get(self.status_change, self.status_change)



# ========== Protocols (Abstractions) ==========

class NotificationRepository(Protocol):
    """Protocol for notification persistence operations."""

    def save(self, notification_data: NotificationData) -> NotificationData:
        """Save a notification and return the persisted version with ID."""
        ...

    def get_by_user(self, meli_user: MeliUser, unread_only: bool = False) -> List[NotificationData]:
        """Get all notifications for a user."""
        ...

    def mark_as_read(self, notification_id: int) -> NotificationData:
        """Mark notification as read."""
        ...


# ========== Serializers ==========

class NotificationSerializer(Protocol):
    def to_dto(self, notification: Notification) -> NotificationData: ...
    def to_model(self, dto: NotificationData) -> Notification: ...


class QuestionNotificationSerializer:
    def to_dto(self, notification: Notification) -> QuestionNotificationData:
        assert notification.question_id is not None
        return QuestionNotificationData(
            id=notification.id,
            type=notification.type,
            meli_user_id=notification.meli_user_id,
            title=notification.title,
            message=notification.message,
            created_at=notification.created_at,
            read_at=notification.read_at,
            question_id=notification.question_id,
        )

    def to_model(self, dto: NotificationData) -> Notification:
        assert isinstance(dto, QuestionNotificationData)
        return Notification(
            type=dto.type,
            meli_user_id=dto.meli_user_id,
            title=dto.title,
            message=dto.message,
            question_id=dto.question_id,
        )


class OrderNotificationSerializer:
    def to_dto(self, notification: Notification) -> OrderNotificationData:
        assert notification.order_id is not None
        return OrderNotificationData(
            id=notification.id,
            type=notification.type,
            meli_user_id=notification.meli_user_id,
            title=notification.title,
            message=notification.message,
            created_at=notification.created_at,
            read_at=notification.read_at,
            order_id=notification.order_id,
            status_change=notification.status_change or '',
        )

    def to_model(self, dto: NotificationData) -> Notification:
        assert isinstance(dto, OrderNotificationData)
        return Notification(
            type=dto.type,
            meli_user_id=dto.meli_user_id,
            title=dto.title,
            message=dto.message,
            order_id=dto.order_id,
            status_change=dto.status_change,
        )


class BaseNotificationSerializer:
    def to_dto(self, notification: Notification) -> NotificationData:
        return NotificationData(
            id=notification.id,
            type=notification.type,
            meli_user_id=notification.meli_user_id,
            title=notification.title,
            message=notification.message,
            created_at=notification.created_at,
            read_at=notification.read_at,
        )

    def to_model(self, dto: NotificationData) -> Notification:
        return Notification(
            type=dto.type,
            meli_user_id=dto.meli_user_id,
            title=dto.title,
            message=dto.message,
        )


# ========== Registry ==========

_SERIALIZERS: dict[str, NotificationSerializer] = {
    'question': QuestionNotificationSerializer(),
    'order': OrderNotificationSerializer(),
}

_DEFAULT_SERIALIZER = BaseNotificationSerializer()


def get_serializer(notification_type: str) -> NotificationSerializer:
    return _SERIALIZERS.get(notification_type, _DEFAULT_SERIALIZER)


# ========== Implementations ==========

class DBNotificationRepository:
    """Django ORM implementation of NotificationRepository."""

    def save(self, notification_data: NotificationData) -> NotificationData:
        """Save a notification in the database and return the persisted version."""
        with transaction.atomic():
            serializer = get_serializer(notification_data.type)
            notification = serializer.to_model(notification_data)
            notification.save()
            return serializer.to_dto(notification)

    def get_by_user(self, meli_user: MeliUser, unread_only: bool = False) -> List[NotificationData]:
        """Get all notifications for a user."""
        notifications = Notification.objects.filter(meli_user=meli_user)

        if unread_only:
            notifications = notifications.filter(read_at__isnull=True)

        return [get_serializer(n.type).to_dto(n) for n in notifications]

    def mark_as_read(self, notification_id: int) -> NotificationData:
        """Mark notification as read."""
        with transaction.atomic():
            notification = Notification.objects.get(id=notification_id)
            if not notification.read_at:
                notification.read_at = datetime.now()
                notification.save()
            return get_serializer(notification.type).to_dto(notification)
