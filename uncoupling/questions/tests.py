from datetime import datetime, timezone

import pytest
from django.contrib.auth.models import User

from my_auth.models import MeliUser
from questions.services import QuestionSyncService
from questions.meli import MeliQuestion, MeliAnswer


class TestQuestionSyncService:
    def test_sync_questions_saves_answered_question(
        self,
        question_repository,
        mock_meli_gateway,
        sample_token
    ):
        # Arrange
        django_user = User(username='testuser', email='test@example.com')
        meli_user = MeliUser(id=12345, user=django_user)

        meli_question = MeliQuestion(**{
            'id': 111,
            'item_id': 'MLB123456',
            'text': '¿Tiene garantía?',
            'status': 'ANSWERED',
            'date_created': '2024-01-15T10:30:00Z',
            'from': {'id': 99999},
            'answer': {
                'text': 'Sí, 12 meses de garantía.',
                'date_created': '2024-01-15T14:20:00Z'
            }
        })

        mock_meli_gateway.get_questions.return_value = [meli_question]

        service = QuestionSyncService(
            question_repository=question_repository,
            meli_gateway=mock_meli_gateway
        )

        # Act
        count = service.sync_questions(meli_user, sample_token)

        # Assert
        assert count == 1
        questions = question_repository.get_by_user(meli_user)
        assert len(questions) == 1

        saved_question = questions[0]
        assert saved_question.id == 111
        assert saved_question.item_id == 'MLB123456'
        assert saved_question.text == '¿Tiene garantía?'
        assert saved_question.status == 'ANSWERED'
        assert saved_question.from_user_id == 99999
        assert saved_question.answer_text == 'Sí, 12 meses de garantía.'
        assert saved_question.answer_date_created is not None

    def test_sync_questions_saves_unanswered_question(
        self,
        question_repository,
        mock_meli_gateway,
        sample_token
    ):
        # Arrange
        django_user = User(username='testuser', email='test@example.com')
        meli_user = MeliUser(id=12345, user=django_user)

        meli_question = MeliQuestion(**{
            'id': 222,
            'item_id': 'MLB789012',
            'text': '¿Hacen envíos?',
            'status': 'UNANSWERED',
            'date_created': '2024-01-16T09:15:00Z',
            'from': {'id': 88888},
            'answer': None
        })

        mock_meli_gateway.get_questions.return_value = [meli_question]

        service = QuestionSyncService(
            question_repository=question_repository,
            meli_gateway=mock_meli_gateway
        )

        # Act
        count = service.sync_questions(meli_user, sample_token)

        # Assert
        assert count == 1
        questions = question_repository.get_by_user(meli_user)
        assert len(questions) == 1

        saved_question = questions[0]
        assert saved_question.id == 222
        assert saved_question.text == '¿Hacen envíos?'
        assert saved_question.status == 'UNANSWERED'
        assert saved_question.answer_text is None
        assert saved_question.answer_date_created is None

    def test_sync_questions_saves_multiple_questions(
        self,
        question_repository,
        mock_meli_gateway,
        sample_token
    ):
        # Arrange
        django_user = User(username='testuser', email='test@example.com')
        meli_user = MeliUser(id=12345, user=django_user)

        questions = [
            MeliQuestion(**{
                'id': 111,
                'item_id': 'MLB111',
                'text': 'Pregunta 1',
                'status': 'ANSWERED',
                'date_created': '2024-01-15T10:00:00Z',
                'from': {'id': 1001},
                'answer': {'text': 'Respuesta 1', 'date_created': '2024-01-15T11:00:00Z'}
            }),
            MeliQuestion(**{
                'id': 222,
                'item_id': 'MLB222',
                'text': 'Pregunta 2',
                'status': 'UNANSWERED',
                'date_created': '2024-01-16T10:00:00Z',
                'from': {'id': 1002},
                'answer': None
            }),
            MeliQuestion(**{
                'id': 333,
                'item_id': 'MLB333',
                'text': 'Pregunta 3',
                'status': 'ANSWERED',
                'date_created': '2024-01-17T10:00:00Z',
                'from': {'id': 1003},
                'answer': {'text': 'Respuesta 3', 'date_created': '2024-01-17T12:00:00Z'}
            }),
        ]

        mock_meli_gateway.get_questions.return_value = questions

        service = QuestionSyncService(
            question_repository=question_repository,
            meli_gateway=mock_meli_gateway
        )

        # Act
        count = service.sync_questions(meli_user, sample_token)

        # Assert
        assert count == 3
        saved_questions = question_repository.get_by_user(meli_user)
        assert len(saved_questions) == 3

    def test_sync_questions_returns_zero_when_no_questions(
        self,
        question_repository,
        mock_meli_gateway,
        sample_token
    ):
        # Arrange
        django_user = User(username='testuser', email='test@example.com')
        meli_user = MeliUser(id=12345, user=django_user)

        mock_meli_gateway.get_questions.return_value = []

        service = QuestionSyncService(
            question_repository=question_repository,
            meli_gateway=mock_meli_gateway
        )

        # Act
        count = service.sync_questions(meli_user, sample_token)

        # Assert
        assert count == 0
        questions = question_repository.get_by_user(meli_user)
        assert len(questions) == 0

    def test_sync_questions_calls_gateway_with_token(
        self,
        question_repository,
        mock_meli_gateway,
        sample_token
    ):
        # Arrange
        django_user = User(username='testuser', email='test@example.com')
        meli_user = MeliUser(id=12345, user=django_user)

        mock_meli_gateway.get_questions.return_value = []

        service = QuestionSyncService(
            question_repository=question_repository,
            meli_gateway=mock_meli_gateway
        )

        # Act
        service.sync_questions(meli_user, sample_token)

        # Assert
        mock_meli_gateway.get_questions.assert_called_once_with(sample_token)
