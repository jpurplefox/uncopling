from unittest.mock import Mock
from datetime import datetime, timezone

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

from mercadolibre.clients import MeliToken

from my_auth.views import meli_login, meli_callback, meli_logout
from my_auth.models import MeliUser
from my_auth.services import MeliAuthService
from my_auth.signals import user_registered
from my_auth.containers import auth_container
from my_auth.meli import MeliUserInfo


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


class MeliLoginViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_meli_login_redirects_to_meli_auth_url(self):
        # Arrange
        mock_auth_service = Mock()
        mock_auth_service.get_login_url.return_value = 'https://auth.mercadolibre.com.ar/authorization?test=params'

        with auth_container.auth_service.override(mock_auth_service):
            request = self.factory.get('/auth/login')

            # Act
            response = meli_login(request)

            # Assert
            mock_auth_service.get_login_url.assert_called_once()
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, 'https://auth.mercadolibre.com.ar/authorization?test=params')


class MeliCallbackViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_meli_callback_handles_successful_authentication(self):
        # Arrange
        mock_user = Mock(spec=User)
        mock_meli_user = Mock(spec=MeliUser)
        mock_meli_user.user = mock_user

        mock_auth_service = Mock()
        mock_auth_service.handle_callback.return_value = mock_meli_user

        mock_session_auth = Mock()

        with auth_container.auth_service.override(mock_auth_service), \
                auth_container.session_authenticator.override(mock_session_auth):
            request = self.factory.get('/auth/callback', {'code': 'test_code_123'})

            # Act
            response = meli_callback(request)

            # Assert
            mock_auth_service.handle_callback.assert_called_once_with('test_code_123')
            mock_session_auth.authenticate_session.assert_called_once_with(request, mock_user)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, '/')

    def test_meli_callback_returns_error_when_code_is_missing(self):
        # Arrange
        mock_auth_service = Mock()

        with auth_container.auth_service.override(mock_auth_service):
            request = self.factory.get('/auth/callback')

            # Act
            response = meli_callback(request)

            # Assert
            self.assertEqual(response.status_code, 400)
            mock_auth_service.handle_callback.assert_not_called()


class MeliLogoutViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_meli_logout_terminates_session_and_redirects(self):
        # Arrange
        mock_session_terminator = Mock()

        with auth_container.session_terminator.override(mock_session_terminator):
            request = self.factory.get('/auth/logout')

            # Act
            response = meli_logout(request)

            # Assert
            mock_session_terminator.terminate_session.assert_called_once_with(request)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, '/')


class MeliAuthServiceTest(TestCase):
    def test_handle_callback_registers_new_user_when_not_exists(self):
        # Arrange
        mock_event_dispatcher = Mock()
        user_repository = InMemoryUserRepository()
        mock_meli_user_service = Mock()

        token = MeliToken(
            user_id=12345,
            access_token='test_access',
            refresh_token='test_refresh',
            expires_at=datetime.now(timezone.utc)
        )

        user_info = MeliUserInfo(
            id=12345,
            nickname='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )

        mock_meli_user_service.get_token.return_value = token
        mock_meli_user_service.get_user_info.return_value = user_info

        service = MeliAuthService(
            user_repository=user_repository,
            meli_user_service=mock_meli_user_service,
            event_dispatcher=mock_event_dispatcher
        )

        # Act
        result = service.handle_callback('test_code')

        # Assert
        created_user = user_repository.get_by_id(12345)
        self.assertEqual(created_user.id, 12345)
        self.assertEqual(created_user.user.username, 'testuser')
        self.assertEqual(created_user.user.email, 'test@example.com')
        self.assertEqual(result, created_user)

    def test_handle_callback_updates_token_when_user_exists(self):
        # Arrange
        mock_event_dispatcher = Mock()
        user_repository = InMemoryUserRepository()
        mock_meli_user_service = Mock()

        # Create existing user in repository
        existing_user = user_repository.create(
            username='existinguser',
            email='existing@example.com',
            first_name='Existing',
            last_name='User',
            meli_user_id=67890
        )

        # Save old token
        old_token = MeliToken(
            user_id=67890,
            access_token='old_access_token',
            refresh_token='old_refresh_token',
            expires_at=datetime.now(timezone.utc)
        )
        user_repository.save_token(old_token)

        # New token for the same user
        new_token = MeliToken(
            user_id=67890,
            access_token='new_access_token',
            refresh_token='new_refresh_token',
            expires_at=datetime.now(timezone.utc)
        )

        mock_meli_user_service.get_token.return_value = new_token

        service = MeliAuthService(
            user_repository=user_repository,
            meli_user_service=mock_meli_user_service,
            event_dispatcher=mock_event_dispatcher
        )

        # Act
        result = service.handle_callback('test_code')

        # Assert
        self.assertEqual(result, existing_user)
        # Verify the token was updated
        updated_token = user_repository._tokens[67890]
        self.assertEqual(updated_token.access_token, 'new_access_token')
        self.assertEqual(updated_token.refresh_token, 'new_refresh_token')
        # Verify user info was not fetched (user already existed)
        mock_meli_user_service.get_user_info.assert_not_called()

    def test_handle_callback_dispatches_user_registered_event_for_new_user(self):
        # Arrange
        mock_event_dispatcher = Mock()
        user_repository = InMemoryUserRepository()
        mock_meli_user_service = Mock()

        token = MeliToken(
            user_id=12345,
            access_token='test_access',
            refresh_token='test_refresh',
            expires_at=datetime.now(timezone.utc)
        )

        user_info = MeliUserInfo(
            id=12345,
            nickname='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )

        mock_meli_user_service.get_token.return_value = token
        mock_meli_user_service.get_user_info.return_value = user_info

        service = MeliAuthService(
            user_repository=user_repository,
            meli_user_service=mock_meli_user_service,
            event_dispatcher=mock_event_dispatcher
        )

        # Act
        result = service.handle_callback('test_code')

        # Assert
        created_user = user_repository.get_by_id(12345)
        mock_event_dispatcher.dispatch.assert_called_once_with(
            user_registered,
            sender=MeliUser,
            meli_user=created_user,
            token=token
        )
        self.assertEqual(result, created_user)
