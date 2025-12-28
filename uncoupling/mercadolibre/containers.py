from dependency_injector import containers, providers

from mercadolibre.clients import MeliClient


class MeliContainer(containers.DeclarativeContainer):
    """Container for MercadoLibre client"""

    meli_client = providers.Singleton(MeliClient)
