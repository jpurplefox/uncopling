"""Repository pattern for order persistence operations."""
from datetime import datetime
from typing import Protocol, List, Optional
from decimal import Decimal
from django.db import transaction
from pydantic import BaseModel, ConfigDict

from my_auth.models import MeliUser
from orders.models import Order, OrderItem, Payment


# ========== Pydantic Models (Domain) - Internal aggregates ==========

class OrderItemData(BaseModel):
    """Order item domain model"""
    item_id: str
    title: str
    quantity: int
    unit_price: Decimal
    currency_id: str

    model_config = ConfigDict(from_attributes=True)


class PaymentData(BaseModel):
    """Payment domain model"""
    payment_id: int
    transaction_amount: Decimal
    currency_id: str
    status: str
    payment_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderData(BaseModel):
    """Order aggregate root - contains all order data"""
    id: int
    meli_user_id: int
    status: str
    date_created: datetime
    date_closed: Optional[datetime] = None
    last_updated: datetime
    buyer_id: int
    buyer_nickname: Optional[str] = None
    buyer_email: Optional[str] = None
    buyer_phone: Optional[str] = None
    buyer_first_name: Optional[str] = None
    buyer_last_name: Optional[str] = None
    total_amount: Decimal
    paid_amount: Optional[Decimal] = None
    currency_id: str
    shipping_id: Optional[int] = None
    order_items: List[OrderItemData] = []
    payments: List[PaymentData] = []

    model_config = ConfigDict(from_attributes=True)

    def get_total_items(self) -> int:
        """Calculate total number of items in order"""
        return sum(item.quantity for item in self.order_items)

    def get_status_display(self) -> str:
        """Get human-readable status"""
        status_map = {
            'paid': 'Pagada',
            'confirmed': 'Confirmada',
            'payment_required': 'Pago requerido',
            'payment_in_process': 'Pago en proceso',
            'cancelled': 'Cancelada',
            'invalid': 'Inválida',
        }
        return status_map.get(self.status, self.status)


# ========== Protocols (Abstractions) ==========

class OrderRepository(Protocol):
    """Protocol for order persistence operations"""

    def save(self, order_data: OrderData) -> OrderData:
        """Save or update an order"""
        ...

    def get_by_user(self, meli_user: MeliUser) -> List[OrderData]:
        """Get all orders for a user"""
        ...


# ========== Implementations ==========

class DBOrderRepository:
    """Django ORM implementation of OrderRepository"""

    def save(self, order_data: OrderData) -> OrderData:
        """Save or update an order in the database"""
        with transaction.atomic():
            # Get the MeliUser
            meli_user = MeliUser.objects.get(id=order_data.meli_user_id)

            # Create or update Order
            order, created = Order.objects.update_or_create(
                id=order_data.id,
                defaults={
                    'meli_user': meli_user,
                    'status': order_data.status,
                    'date_created': order_data.date_created,
                    'date_closed': order_data.date_closed,
                    'last_updated': order_data.last_updated,
                    'buyer_id': order_data.buyer_id,
                    'buyer_nickname': order_data.buyer_nickname,
                    'buyer_email': order_data.buyer_email,
                    'buyer_phone': order_data.buyer_phone,
                    'buyer_first_name': order_data.buyer_first_name,
                    'buyer_last_name': order_data.buyer_last_name,
                    'total_amount': order_data.total_amount,
                    'paid_amount': order_data.paid_amount,
                    'currency_id': order_data.currency_id,
                    'shipping_id': order_data.shipping_id,
                }
            )

            # Delete existing items and payments to recreate them
            if not created:
                order.order_items.all().delete()
                order.payments.all().delete()

            # Create order items
            for item_data in order_data.order_items:
                OrderItem.objects.create(
                    order=order,
                    item_id=item_data.item_id,
                    title=item_data.title,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    currency_id=item_data.currency_id
                )

            # Create payments
            for payment_data in order_data.payments:
                Payment.objects.create(
                    order=order,
                    payment_id=payment_data.payment_id,
                    transaction_amount=payment_data.transaction_amount,
                    currency_id=payment_data.currency_id,
                    status=payment_data.status,
                    payment_type=payment_data.payment_type
                )

            # Return updated order as OrderData
            return self._to_order_data(order)

    def get_by_user(self, meli_user: MeliUser) -> List[OrderData]:
        """Get all orders for a user"""
        orders = Order.objects.filter(meli_user=meli_user).prefetch_related('order_items', 'payments')
        return [self._to_order_data(order) for order in orders]

    def _to_order_data(self, order: Order) -> OrderData:
        """Convert Django Order model to OrderData Pydantic model"""
        return OrderData(
            id=order.id,
            meli_user_id=order.meli_user.id,
            status=order.status,
            date_created=order.date_created,
            date_closed=order.date_closed,
            last_updated=order.last_updated,
            buyer_id=order.buyer_id,
            buyer_nickname=order.buyer_nickname,
            buyer_email=order.buyer_email,
            buyer_phone=order.buyer_phone,
            buyer_first_name=order.buyer_first_name,
            buyer_last_name=order.buyer_last_name,
            total_amount=order.total_amount,
            paid_amount=order.paid_amount,
            currency_id=order.currency_id,
            shipping_id=order.shipping_id,
            order_items=[
                OrderItemData.model_validate(item)
                for item in order.order_items.all()
            ],
            payments=[
                PaymentData.model_validate(payment)
                for payment in order.payments.all()
            ]
        )
