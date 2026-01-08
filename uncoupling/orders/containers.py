from dependency_injector import containers, providers

from mercadolibre.containers import MeliContainer
from orders.services import (
    DBOrderRepository,
    MeliOrderAPIGateway,
    OrderSyncService,
)


class OrderContainer(containers.DeclarativeContainer):
    """Dependency injection container for orders module"""

    # MercadoLibre container (reuse existing)
    meli_container = providers.Container(MeliContainer)

    # Repositories
    order_repository = providers.Singleton(DBOrderRepository)

    # Gateways
    meli_order_gateway = providers.Singleton(
        MeliOrderAPIGateway,
        meli_client=meli_container.meli_client
    )

    # Services
    order_sync_service = providers.Singleton(
        OrderSyncService,
        order_repository=order_repository,
        meli_gateway=meli_order_gateway
    )


# Global container instance
order_container = OrderContainer()
