"""Signal handlers for creating notifications."""
from django.dispatch import receiver
from dependency_injector.wiring import inject, Provide

from questions.events import question_received
from orders.events import order_synced
from notifications.containers import NotificationContainer


@receiver(question_received)
@inject
def on_question_received(
    sender,
    meli_user,
    question_id,
    question_text,
    notification_service=Provide[NotificationContainer.notification_service],
    **kwargs
):
    """Create notification when a new question is received."""
    notification_service.create_question_notification(
        meli_user=meli_user,
        question_id=question_id,
        question_text=question_text,
    )


@receiver(order_synced)
@inject
def on_order_synced(
    sender,
    meli_user,
    order_id,
    status,
    notification_service=Provide[NotificationContainer.notification_service],
    **kwargs
):
    """Create notification when an order is synced."""
    notification_service.create_order_notification(
        meli_user=meli_user,
        order_id=order_id,
        status=status,
    )
