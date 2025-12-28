from dependency_injector import containers, providers

from mercadolibre.containers import MeliContainer
from my_auth.services import MeliAuthService, DBUserRepository
from my_auth.meli import MeliUserService


class AuthContainer(containers.DeclarativeContainer):
    """Container for authentication services"""

    meli_container = providers.Container(MeliContainer)

    user_repository = providers.Singleton(DBUserRepository)

    meli_user_service = providers.Singleton(
        MeliUserService,
        meli_client=meli_container.meli_client
    )

    auth_service = providers.Singleton(
        MeliAuthService,
        user_repository=user_repository,
        meli_user_service=meli_user_service
    )


auth_container = AuthContainer()
