"""
Pytest fixtures for my_auth tests.

conftest.py is automatically discovered by pytest and makes fixtures
available to all test files in this directory.
"""
from unittest.mock import Mock, create_autospec
from datetime import datetime, timezone

import pytest
from django.contrib.auth.models import User

from mercadolibre.clients import MeliToken
from my_auth.models import MeliUser
from my_auth.meli import MeliUserInfo, MeliOAuthProvider
from my_auth.services import (
    EventDispatcher,
    SessionAuthenticator,
    SessionTerminator,
)


class InMemoryUserRepository:
    """In-memory implementation of UserRepository for testing"""

    def __init__(self):
        self._users = {}
        self._tokens = {}

    def get_by_id(self, user_id: int) -> MeliUser:
        if user_id not in self._users:
            raise MeliUser.DoesNotExist
        return self._users[user_id]

    def create(self, username: str, email: str, first_name: str, last_name: str, meli_user_id: int) -> MeliUser:
        django_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        meli_user = MeliUser(
            id=meli_user_id,
            user=django_user
        )
        self._users[meli_user_id] = meli_user
        return meli_user

    def save_token(self, token: MeliToken) -> None:
        self._tokens[token.user_id] = token


@pytest.fixture
def user_repository():
    return InMemoryUserRepository()


@pytest.fixture
def mock_event_dispatcher():
    return create_autospec(EventDispatcher, instance=True)


@pytest.fixture
def mock_meli_user_service():
    return create_autospec(MeliOAuthProvider, instance=True)


@pytest.fixture
def mock_auth_service():
    return Mock(spec=['get_login_url', 'handle_callback'])


@pytest.fixture
def mock_session_authenticator():
    return create_autospec(SessionAuthenticator, instance=True)


@pytest.fixture
def mock_session_terminator():
    return create_autospec(SessionTerminator, instance=True)
