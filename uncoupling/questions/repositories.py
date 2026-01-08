"""Repository pattern for question persistence operations."""
from datetime import datetime
from typing import Protocol, Optional, List
from django.db import transaction

from my_auth.models import MeliUser
from questions.models import Question


# ========== Protocols (Abstractions) ==========

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


# ========== Implementations ==========

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
