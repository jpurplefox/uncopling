"""Order synchronization service."""
import logging
from datetime import datetime
from decimal import Decimal

from mercadolibre.clients import MeliToken
from my_auth.models import MeliUser
from my_auth.services import EventDispatcher
from orders.models import Order
from orders.repositories import OrderRepository, OrderData, OrderItemData, PaymentData
from orders.meli import MeliOrder, MeliOrderGateway
from orders.events import order_synced


logger = logging.getLogger(__name__)


class OrderSyncService:
    """Service for synchronizing orders from MercadoLibre"""

    def __init__(
        self,
        order_repository: OrderRepository,
        meli_gateway: MeliOrderGateway,
        event_dispatcher: EventDispatcher,
    ):
        self.order_repository = order_repository
        self.meli_gateway = meli_gateway
        self.event_dispatcher = event_dispatcher

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

        saved = self.order_repository.save(order_data)

        self.event_dispatcher.dispatch(
            order_synced,
            sender=Order,
            meli_user=meli_user,
            order_id=order.id,
            status=order.status,
        )

        return saved

    @staticmethod
    def _parse_iso_datetime(iso_string: str) -> datetime:
        """Parse ISO 8601 datetime string to datetime object"""
        # Handle both 'Z' (UTC) and '+00:00' format
        normalized = iso_string.replace('Z', '+00:00')
        return datetime.fromisoformat(normalized)
