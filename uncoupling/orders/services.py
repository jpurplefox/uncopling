import logging
from datetime import datetime
from typing import Protocol, Optional, List
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, ValidationError
from django.db import transaction

from mercadolibre.clients import MeliToken
from orders.models import Order, OrderItem, Payment
from my_auth.models import MeliUser


logger = logging.getLogger(__name__)


# ========== Pydantic Models (Domain) - API responses ==========

class MeliBuyer(BaseModel):
    """Buyer information from MercadoLibre API"""
    id: int
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[dict] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class MeliOrderItem(BaseModel):
    """Order item from MercadoLibre API"""
    item: dict
    quantity: int
    unit_price: float
    currency_id: str = 'BRL'

    @property
    def item_id(self) -> str:
        return self.item.get('id', '')

    @property
    def item_title(self) -> str:
        return self.item.get('title', '')


class MeliPayment(BaseModel):
    """Payment information from MercadoLibre API"""
    id: int
    transaction_amount: float
    currency_id: str
    status: str
    payment_type: Optional[str] = None


class MeliOrder(BaseModel):
    """Order from MercadoLibre API"""
    id: int
    status: str
    date_created: str
    date_closed: Optional[str] = None
    last_updated: str
    buyer: MeliBuyer
    order_items: List[MeliOrderItem]
    total_amount: float
    paid_amount: Optional[float] = None
    currency_id: str = 'BRL'
    payments: List[MeliPayment] = []
    shipping: Optional[dict] = None


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


class MeliOrderGateway(Protocol):
    """Protocol for fetching orders from MercadoLibre API"""

    def get_orders(self, token: MeliToken) -> List[MeliOrder]:
        """Fetch orders from MercadoLibre API"""
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


class MeliOrderAPIGateway:
    """Implementation of MeliOrderGateway using MercadoLibre API"""

    def __init__(self, meli_client):
        self.meli_client = meli_client

    def get_orders(self, token: MeliToken) -> List[MeliOrder]:
        """Fetch orders from MercadoLibre API"""
        # Use /orders/search?seller endpoint
        response = self.meli_client.get(
            f'/orders/search?seller={token.user_id}&sort=date_desc',
            token
        )
        response.raise_for_status()
        data = response.json()

        orders = []
        for order_data in data.get('results', []):
            try:
                orders.append(MeliOrder(**order_data))
            except ValidationError:
                logger.exception(f"Failed to parse order {order_data.get('id')}")
                continue

        logger.info(f"Fetched {len(orders)} orders from MercadoLibre for user {token.user_id}")
        return orders


class OrderSyncService:
    """Service for synchronizing orders from MercadoLibre"""

    def __init__(
        self,
        order_repository: OrderRepository,
        meli_gateway: MeliOrderGateway
    ):
        self.order_repository = order_repository
        self.meli_gateway = meli_gateway

    def sync_orders(self, meli_user: MeliUser, token: MeliToken) -> int:
        """
        Synchronize orders from MercadoLibre for a user.

        Returns the number of orders synchronized.
        """
        orders = self.meli_gateway.get_orders(token)

        saved_count = 0
        for order in orders:
            self._save_order(meli_user, order)
            saved_count += 1

        logger.info(f"Synchronized {saved_count} orders for user {meli_user.id}")
        return saved_count

    def _save_order(self, meli_user: MeliUser, order: MeliOrder) -> OrderData:
        """Parse MeliOrder and save as OrderData"""
        # Parse buyer phone
        buyer_phone = None
        if order.buyer.phone:
            area_code = order.buyer.phone.get('area_code', '')
            number = order.buyer.phone.get('number', '')
            buyer_phone = f"{area_code} {number}".strip() if area_code or number else None

        # Create OrderItemData list
        order_items = [
            OrderItemData(
                item_id=item.item_id,
                title=item.item_title,
                quantity=item.quantity,
                unit_price=Decimal(str(item.unit_price)),
                currency_id=item.currency_id,
            )
            for item in order.order_items
        ]

        # Create PaymentData list
        payments = [
            PaymentData(
                payment_id=payment.id,
                transaction_amount=Decimal(str(payment.transaction_amount)),
                currency_id=payment.currency_id,
                status=payment.status,
                payment_type=payment.payment_type,
            )
            for payment in order.payments
        ]

        # Parse shipping ID
        shipping_id = None
        if order.shipping and isinstance(order.shipping, dict):
            shipping_id = order.shipping.get('id')

        # Create OrderData aggregate
        order_data = OrderData(
            id=order.id,
            meli_user_id=meli_user.id,
            status=order.status,
            date_created=self._parse_iso_datetime(order.date_created),
            date_closed=self._parse_iso_datetime(order.date_closed) if order.date_closed else None,
            last_updated=self._parse_iso_datetime(order.last_updated),
            buyer_id=order.buyer.id,
            buyer_nickname=order.buyer.nickname,
            buyer_email=order.buyer.email,
            buyer_phone=buyer_phone,
            buyer_first_name=order.buyer.first_name,
            buyer_last_name=order.buyer.last_name,
            total_amount=Decimal(str(order.total_amount)),
            paid_amount=Decimal(str(order.paid_amount)) if order.paid_amount else None,
            currency_id=order.currency_id,
            shipping_id=shipping_id,
            order_items=order_items,
            payments=payments
        )

        return self.order_repository.save(order_data)

    @staticmethod
    def _parse_iso_datetime(iso_string: str) -> datetime:
        """Parse ISO 8601 datetime string to datetime object"""
        # Handle both 'Z' (UTC) and '+00:00' format
        normalized = iso_string.replace('Z', '+00:00')
        return datetime.fromisoformat(normalized)
