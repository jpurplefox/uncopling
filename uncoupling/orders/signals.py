from django.dispatch import receiver
from dependency_injector.wiring import inject, Provide

from my_auth.signals import user_registered
from orders.containers import OrderContainer
from orders.services import OrderSyncService


@receiver(user_registered)
@inject
def on_user_registered(
    sender,
    meli_user,
    token,
    sync_service: OrderSyncService = Provide[OrderContainer.order_sync_service],
    **kwargs
):
    """Synchronize orders when a new user registers"""
    sync_service.sync_orders(meli_user, token)
