from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel, Field

from mercadolibre.clients import MeliClient, MeliToken
from questions.models import Question
from my_auth.models import MeliUser


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


def get_questions_from_meli(token: MeliToken):
    client = MeliClient()

    response = client.get(
        f'/questions/search?seller_id={token.user_id}'
        f'&sort_fields=date_created',
        token
    )
    data = response.json()

    questions = []
    for question_data in data.get('questions', []):
        questions.append(MeliQuestion(**question_data))

    return questions


def save_questions(meli_user: MeliUser, questions: list[MeliQuestion]):
    for question in questions:
        answer_text = None
        answer_date_created = None

        if question.answer:
            answer_text = question.answer.text
            answer_date_created = datetime.fromisoformat(
                question.answer.date_created.replace('Z', '+00:00')
            )

        Question.objects.update_or_create(
            id=question.id,
            defaults={
                'meli_user': meli_user,
                'item_id': question.item_id,
                'text': question.text,
                'status': question.status,
                'date_created': datetime.fromisoformat(
                    question.date_created.replace('Z', '+00:00')
                ),
                'from_user_id': question.from_['id'],
                'answer_text': answer_text,
                'answer_date_created': answer_date_created,
            }
        )


def fetch_and_save_questions_from_meli(meli_user: MeliUser, token: MeliToken):
    questions = get_questions_from_meli(token)
    save_questions(meli_user, questions)
    return len(questions)
