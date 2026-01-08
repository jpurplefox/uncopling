"""
Pytest fixtures for orders tests.

conftest.py is automatically discovered by pytest and makes fixtures
available to all test files in this directory.
"""
from unittest.mock import create_autospec
from datetime import datetime, timezone

import pytest

from mercadolibre.clients import MeliToken
from my_auth.models import MeliUser
from orders.services import MeliOrderGateway
from orders.repositories import OrderData


class InMemoryOrderRepository:
    """In-memory implementation of OrderRepository for testing"""

    def __init__(self):
        self._orders = {}

    def save(self, order_data: OrderData) -> OrderData:
        """Save order data (Pydantic model)"""
        self._orders[order_data.id] = order_data
        return order_data

    def get_by_user(self, meli_user: MeliUser) -> list[OrderData]:
        """Get orders for a user"""
        return [
            order for order in self._orders.values()
            if order.meli_user_id == meli_user.id
        ]


@pytest.fixture
def order_repository():
    return InMemoryOrderRepository()


@pytest.fixture
def mock_meli_order_gateway():
    return create_autospec(MeliOrderGateway, instance=True)


@pytest.fixture
def sample_token():
    """Sample MeliToken for testing"""
    return MeliToken(
        user_id=12345,
        access_token='test_access',
        refresh_token='test_refresh',
        expires_at=datetime.now(timezone.utc)
    )
