from dependency_injector import containers, providers

from mercadolibre.containers import MeliContainer
from my_auth.services import DjangoSignalEventDispatcher
from questions.repositories import DBQuestionRepository
from questions.meli import MeliQuestionAPIGateway
from questions.services import QuestionSyncService


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

    # Event dispatching
    event_dispatcher = providers.Singleton(DjangoSignalEventDispatcher)

    # Services
    question_sync_service = providers.Singleton(
        QuestionSyncService,
        question_repository=question_repository,
        meli_gateway=meli_question_gateway,
        event_dispatcher=event_dispatcher,
    )


# Global container instance
question_container = QuestionContainer()
