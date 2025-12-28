from dependency_injector import containers, providers

from mercadolibre.client import MeliClient


class MeliContainer(containers.DeclarativeContainer):
    """Container for MercadoLibre client"""

    meli_client = providers.Singleton(MeliClient)
