from django.dispatch import receiver
from dependency_injector.wiring import inject, Provide

from my_auth.signals import user_registered
from questions.containers import QuestionContainer
from questions.services import QuestionSyncService


@receiver(user_registered)
@inject
def on_user_registered(
    sender,
    meli_user,
    token,
    sync_service: QuestionSyncService = Provide[QuestionContainer.question_sync_service],
    **kwargs
):
    """Synchronize questions when a new user registers"""
    sync_service.sync_questions(meli_user, token)
