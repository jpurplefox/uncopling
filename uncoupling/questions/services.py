import logging
from datetime import datetime
from typing import Protocol, Optional, List
from pydantic import BaseModel, Field
from django.db import transaction

from mercadolibre.clients import MeliToken
from questions.models import Question
from my_auth.models import MeliUser


logger = logging.getLogger(__name__)


class MeliAnswer(BaseModel):
    text: str
    date_created: str


class MeliQuestion(BaseModel):
    id: int
    item_id: str
    text: str
    status: str
    date_created: str
    from_: dict = Field(alias='from')
    answer: Optional[MeliAnswer] = None


class QuestionRepository(Protocol):
    """Protocol for question persistence operations"""

    def save_or_update(
        self,
        question_id: int,
        meli_user: MeliUser,
        item_id: str,
        text: str,
        status: str,
        date_created: datetime,
        from_user_id: int,
        answer_text: Optional[str],
        answer_date_created: Optional[datetime]
    ) -> Question:
        """Save or update a question"""
        ...

    def get_by_user(self, meli_user: MeliUser) -> List[Question]:
        """Get all questions for a user"""
        ...


class MeliQuestionGateway(Protocol):
    """Protocol for fetching questions from MercadoLibre API"""

    def get_questions(self, token: MeliToken) -> List[MeliQuestion]:
        """Fetch questions from MercadoLibre API"""
        ...


class DBQuestionRepository:
    """Django ORM implementation of QuestionRepository"""

    def save_or_update(
        self,
        question_id: int,
        meli_user: MeliUser,
        item_id: str,
        text: str,
        status: str,
        date_created: datetime,
        from_user_id: int,
        answer_text: Optional[str],
        answer_date_created: Optional[datetime]
    ) -> Question:
        """Save or update a question in the database"""
        with transaction.atomic():
            question, created = Question.objects.update_or_create(
                id=question_id,
                defaults={
                    'meli_user': meli_user,
                    'item_id': item_id,
                    'text': text,
                    'status': status,
                    'date_created': date_created,
                    'from_user_id': from_user_id,
                    'answer_text': answer_text,
                    'answer_date_created': answer_date_created,
                }
            )
            return question

    def get_by_user(self, meli_user: MeliUser) -> List[Question]:
        """Get all questions for a user"""
        return list(Question.objects.filter(meli_user=meli_user))


class MeliQuestionAPIGateway:
    """Implementation of MeliQuestionGateway using MercadoLibre API"""

    def __init__(self, meli_client):
        self.meli_client = meli_client

    def get_questions(self, token: MeliToken) -> List[MeliQuestion]:
        """Fetch questions from MercadoLibre API"""
        response = self.meli_client.get(
            f'/questions/search?seller_id={token.user_id}'
            f'&sort_fields=date_created',
            token
        )
        response.raise_for_status()
        data = response.json()

        questions = []
        for question_data in data.get('questions', []):
            questions.append(MeliQuestion(**question_data))

        logger.info(f"Fetched {len(questions)} questions from MercadoLibre for user {token.user_id}")
        return questions


class QuestionSyncService:
    """Service for synchronizing questions from MercadoLibre"""

    def __init__(
        self,
        question_repository: QuestionRepository,
        meli_gateway: MeliQuestionGateway
    ):
        self.question_repository = question_repository
        self.meli_gateway = meli_gateway

    def sync_questions(self, meli_user: MeliUser, token: MeliToken) -> int:
        """
        Synchronize questions from MercadoLibre for a user.

        Returns the number of questions synchronized.
        """
        questions = self.meli_gateway.get_questions(token)

        saved_count = 0
        for question in questions:
            self._save_question(meli_user, question)
            saved_count += 1

        logger.info(f"Synchronized {saved_count} questions for user {meli_user.id}")
        return saved_count

    def _save_question(self, meli_user: MeliUser, question: MeliQuestion) -> Question:
        """Parse and save a single question"""
        answer_text = None
        answer_date_created = None

        if question.answer:
            answer_text = question.answer.text
            answer_date_created = self._parse_iso_datetime(question.answer.date_created)

        return self.question_repository.save_or_update(
            question_id=question.id,
            meli_user=meli_user,
            item_id=question.item_id,
            text=question.text,
            status=question.status,
            date_created=self._parse_iso_datetime(question.date_created),
            from_user_id=question.from_['id'],
            answer_text=answer_text,
            answer_date_created=answer_date_created
        )

    @staticmethod
    def _parse_iso_datetime(iso_string: str) -> datetime:
        """Parse ISO 8601 datetime string to datetime object"""
        # Handle both 'Z' (UTC) and '+00:00' format
        normalized = iso_string.replace('Z', '+00:00')
        return datetime.fromisoformat(normalized)
