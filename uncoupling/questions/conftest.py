"""
Pytest fixtures for questions tests.

conftest.py is automatically discovered by pytest and makes fixtures
available to all test files in this directory.
"""
from unittest.mock import create_autospec
from datetime import datetime, timezone

import pytest
from django.contrib.auth.models import User

from mercadolibre.clients import MeliToken
from my_auth.models import MeliUser
from questions.models import Question
from questions.services import MeliQuestionGateway


class InMemoryQuestionRepository:
    """In-memory implementation of QuestionRepository for testing"""

    def __init__(self):
        self._questions = {}

    def save_or_update(
        self,
        question_id: int,
        meli_user: MeliUser,
        item_id: str,
        text: str,
        status: str,
        date_created: datetime,
        from_user_id: int,
        answer_text: str | None,
        answer_date_created: datetime | None
    ) -> Question:
        question = Question(
            id=question_id,
            meli_user=meli_user,
            item_id=item_id,
            text=text,
            status=status,
            date_created=date_created,
            from_user_id=from_user_id,
            answer_text=answer_text,
            answer_date_created=answer_date_created
        )
        self._questions[question_id] = question
        return question

    def get_by_user(self, meli_user: MeliUser) -> list[Question]:
        return [
            q for q in self._questions.values()
            if q.meli_user.id == meli_user.id
        ]


@pytest.fixture
def question_repository():
    return InMemoryQuestionRepository()


@pytest.fixture
def mock_meli_gateway():
    return create_autospec(MeliQuestionGateway, instance=True)


@pytest.fixture
def sample_token():
    """Sample MeliToken for testing"""
    return MeliToken(
        user_id=12345,
        access_token='test_access',
        refresh_token='test_refresh',
        expires_at=datetime.now(timezone.utc)
    )
