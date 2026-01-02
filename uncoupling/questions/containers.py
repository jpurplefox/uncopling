from dependency_injector import containers, providers

from mercadolibre.containers import MeliContainer
from questions.services import (
    DBQuestionRepository,
    MeliQuestionAPIGateway,
    QuestionSyncService,
)


class QuestionContainer(containers.DeclarativeContainer):
    """Dependency injection container for questions module"""

    # MercadoLibre container
    meli_container = providers.Container(MeliContainer)

    # Repositories
    question_repository = providers.Singleton(DBQuestionRepository)

    # Gateways
    meli_question_gateway = providers.Singleton(
        MeliQuestionAPIGateway,
        meli_client=meli_container.meli_client
    )

    # Services
    question_sync_service = providers.Singleton(
        QuestionSyncService,
        question_repository=question_repository,
        meli_gateway=meli_question_gateway
    )


# Global container instance
question_container = QuestionContainer()
