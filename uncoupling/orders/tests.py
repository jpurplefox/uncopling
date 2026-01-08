from datetime import datetime, timezone
from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from my_auth.models import MeliUser
from orders.services import OrderSyncService
from orders.meli import MeliOrder


class TestOrderSyncService:
    def test_sync_orders_saves_paid_order(
        self,
        order_repository,
        mock_meli_order_gateway,
        sample_token
    ):
        # Arrange
        django_user = User(username='testuser', email='test@example.com')
        meli_user = MeliUser(id=12345, user=django_user)

        meli_order = MeliOrder(**{
            'id': 2000001234,
            'status': 'paid',
            'date_created': '2024-01-15T10:30:00Z',
            'date_closed': '2024-01-15T11:00:00Z',
            'last_updated': '2024-01-15T11:00:00Z',
            'buyer': {
                'id': 88888,
                'nickname': 'BUYER123',
                'email': 'buyer@example.com',
                'phone': {'area_code': '11', 'number': '12345678'},
                'first_name': 'Juan',
                'last_name': 'Pérez'
            },
            'order_items': [
                {
                    'item': {'id': 'MLB123', 'title': 'Producto Test'},
                    'quantity': 2,
                    'unit_price': 150.00,
                    'currency_id': 'BRL'
                }
            ],
            'total_amount': 300.00,
            'paid_amount': 300.00,
            'currency_id': 'BRL',
            'payments': [
                {
                    'id': 999,
                    'transaction_amount': 300.00,
                    'currency_id': 'BRL',
                    'status': 'approved',
                    'payment_type': 'credit_card'
                }
            ],
            'shipping': {'id': 7777}
        })

        mock_meli_order_gateway.get_orders.return_value = [meli_order]

        service = OrderSyncService(
            order_repository=order_repository,
            meli_gateway=mock_meli_order_gateway
        )

        # Act
        count = service.sync_orders(meli_user, sample_token)

        # Assert
        assert count == 1
        orders = order_repository.get_by_user(meli_user)
        assert len(orders) == 1

        # Verify order data (Pydantic model)
        saved_order = orders[0]
        assert saved_order.id == 2000001234
        assert saved_order.status == 'paid'
        assert saved_order.buyer_nickname == 'BUYER123'
        assert saved_order.buyer_email == 'buyer@example.com'
        assert saved_order.buyer_phone == '11 12345678'
        assert saved_order.total_amount == Decimal('300.00')

        # Check order items (Pydantic list)
        assert len(saved_order.order_items) == 1
        assert saved_order.order_items[0].title == 'Producto Test'
        assert saved_order.order_items[0].quantity == 2
        assert saved_order.order_items[0].unit_price == Decimal('150.00')

        # Check payments (Pydantic list)
        assert len(saved_order.payments) == 1
        assert saved_order.payments[0].status == 'approved'
        assert saved_order.payments[0].payment_type == 'credit_card'

    def test_sync_orders_saves_multiple_orders(
        self,
        order_repository,
        mock_meli_order_gateway,
        sample_token
    ):
        # Arrange
        django_user = User(username='testuser', email='test@example.com')
        meli_user = MeliUser(id=12345, user=django_user)

        orders = [
            MeliOrder(**{
                'id': 2000001,
                'status': 'paid',
                'date_created': '2024-01-15T10:00:00Z',
                'date_closed': None,
                'last_updated': '2024-01-15T10:00:00Z',
                'buyer': {'id': 1001, 'nickname': 'buyer1'},
                'order_items': [
                    {
                        'item': {'id': 'MLB1', 'title': 'Item 1'},
                        'quantity': 1,
                        'unit_price': 100.0,
                        'currency_id': 'BRL'
                    }
                ],
                'total_amount': 100.0,
                'currency_id': 'BRL',
                'payments': []
            }),
            MeliOrder(**{
                'id': 2000002,
                'status': 'confirmed',
                'date_created': '2024-01-16T10:00:00Z',
                'date_closed': None,
                'last_updated': '2024-01-16T10:00:00Z',
                'buyer': {'id': 1002, 'nickname': 'buyer2'},
                'order_items': [
                    {
                        'item': {'id': 'MLB2', 'title': 'Item 2'},
                        'quantity': 3,
                        'unit_price': 50.0,
                        'currency_id': 'BRL'
                    }
                ],
                'total_amount': 150.0,
                'currency_id': 'BRL',
                'payments': []
            }),
        ]

        mock_meli_order_gateway.get_orders.return_value = orders

        service = OrderSyncService(
            order_repository=order_repository,
            meli_gateway=mock_meli_order_gateway
        )

        # Act
        count = service.sync_orders(meli_user, sample_token)

        # Assert
        assert count == 2
        saved_orders = order_repository.get_by_user(meli_user)
        assert len(saved_orders) == 2

    def test_sync_orders_returns_zero_when_no_orders(
        self,
        order_repository,
        mock_meli_order_gateway,
        sample_token
    ):
        # Arrange
        django_user = User(username='testuser', email='test@example.com')
        meli_user = MeliUser(id=12345, user=django_user)

        mock_meli_order_gateway.get_orders.return_value = []

        service = OrderSyncService(
            order_repository=order_repository,
            meli_gateway=mock_meli_order_gateway
        )

        # Act
        count = service.sync_orders(meli_user, sample_token)

        # Assert
        assert count == 0
        orders = order_repository.get_by_user(meli_user)
        assert len(orders) == 0

    def test_sync_orders_calls_gateway_with_token(
        self,
        order_repository,
        mock_meli_order_gateway,
        sample_token
    ):
        # Arrange
        django_user = User(username='testuser', email='test@example.com')
        meli_user = MeliUser(id=12345, user=django_user)

        mock_meli_order_gateway.get_orders.return_value = []

        service = OrderSyncService(
            order_repository=order_repository,
            meli_gateway=mock_meli_order_gateway
        )

        # Act
        service.sync_orders(meli_user, sample_token)

        # Assert
        mock_meli_order_gateway.get_orders.assert_called_once_with(sample_token)

    def test_order_data_get_total_items(self):
        """Test that OrderData.get_total_items() calculates correctly"""
        from orders.repositories import OrderData, OrderItemData

        order = OrderData(
            id=1,
            meli_user_id=123,
            status='paid',
            date_created=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
            buyer_id=456,
            total_amount=Decimal('100.00'),
            currency_id='BRL',
            order_items=[
                OrderItemData(item_id='1', title='Item 1', quantity=2, unit_price=Decimal('10.00'), currency_id='BRL'),
                OrderItemData(item_id='2', title='Item 2', quantity=3, unit_price=Decimal('20.00'), currency_id='BRL'),
            ]
        )

        assert order.get_total_items() == 5
