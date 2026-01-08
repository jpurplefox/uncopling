"""MercadoLibre API integration for questions."""
import logging
from typing import Protocol, Optional, List
from pydantic import BaseModel, Field

from mercadolibre.clients import MeliToken


logger = logging.getLogger(__name__)


# ========== Pydantic Models (Domain) - API responses ==========

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


# ========== Protocols (Abstractions) ==========

class MeliQuestionGateway(Protocol):
    """Protocol for fetching questions from MercadoLibre API"""

    def get_questions(self, token: MeliToken) -> List[MeliQuestion]:
        """Fetch questions from MercadoLibre API"""
        ...


# ========== Implementations ==========

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
