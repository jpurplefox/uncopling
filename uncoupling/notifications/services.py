"""Notification service for creating and managing notifications."""
import logging
from datetime import datetime

from my_auth.models import MeliUser
from notifications.repositories import (
    NotificationRepository,
    NotificationData,
    QuestionNotificationData,
    OrderNotificationData,
)


logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications."""

    def __init__(self, notification_repository: NotificationRepository):
        self.repository = notification_repository

    def create_question_notification(
        self,
        meli_user: MeliUser,
        question_id: int,
        question_text: str
    ) -> NotificationData:
        """Create a notification for a new question."""
        preview = question_text[:100] + "..." if len(question_text) > 100 else question_text

        # Build domain object
        notification_data = QuestionNotificationData(
            id=None,
            type='question',
            meli_user_id=meli_user.id,
            title='Nueva pregunta recibida',
            message=f'Pregunta: {preview}',
            created_at=datetime.now(),
            question_id=question_id
        )

        # Save and get persisted version with ID
        notification = self.repository.save(notification_data)

        logger.info(f"Created question notification for user {meli_user.id}, question {question_id}")
        return notification

    def create_order_notification(
        self,
        meli_user: MeliUser,
        order_id: int,
        status: str
    ) -> NotificationData:
        """Create a notification for an order update."""
        status_messages = {
            'paid': 'Tu orden ha sido pagada',
            'confirmed': 'Tu orden ha sido confirmada',
            'payment_required': 'Tu orden requiere pago',
        }

        title = status_messages.get(status, f'Actualización de orden #{order_id}')
        message = f'La orden #{order_id} cambió a estado: {status}'

        # Build domain object
        notification_data = OrderNotificationData(
            id=None,
            type='order',
            meli_user_id=meli_user.id,
            title=title,
            message=message,
            created_at=datetime.now(),
            order_id=order_id,
            status_change=status
        )

        # Save and get persisted version with ID
        notification = self.repository.save(notification_data)

        logger.info(f"Created order notification for user {meli_user.id}, order {order_id}")
        return notification
