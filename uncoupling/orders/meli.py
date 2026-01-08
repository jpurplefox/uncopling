"""MercadoLibre API integration for orders."""
import logging
from typing import Protocol, Optional, List
from pydantic import BaseModel, ValidationError

from mercadolibre.clients import MeliToken


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


# ========== Protocols (Abstractions) ==========

class MeliOrderGateway(Protocol):
    """Protocol for fetching orders from MercadoLibre API"""

    def get_orders(self, token: MeliToken) -> List[MeliOrder]:
        """Fetch orders from MercadoLibre API"""
        ...


# ========== Implementations ==========

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
