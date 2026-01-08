"""Question synchronization service."""
import logging
from datetime import datetime

from mercadolibre.clients import MeliToken
from my_auth.models import MeliUser
from questions.models import Question
from questions.repositories import QuestionRepository
from questions.meli import MeliQuestion, MeliQuestionGateway


logger = logging.getLogger(__name__)


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
