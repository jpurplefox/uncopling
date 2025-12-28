from unittest.mock import Mock
from datetime import datetime, timezone

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

from mercadolibre.client import MeliToken

from my_auth.views import meli_login, meli_callback, meli_logout
from my_auth.models import MeliUser
from my_auth.services import MeliAuthService
from my_auth.signals import user_registered
from my_auth.containers import auth_container
from my_auth.meli import MeliUserInfo


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


class MeliAuthServiceEventDispatchTest(TestCase):
    def test_register_user_dispatches_user_registered_event(self):
        # Arrange
        mock_event_dispatcher = Mock()
        mock_user_repository = Mock()
        mock_meli_user_service = Mock()

        user_info = MeliUserInfo(
            id=12345,
            nickname='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )

        mock_meli_user_service.get_user_info.return_value = user_info

        django_user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        meli_user = MeliUser(
            id=12345,
            user=django_user
        )
        mock_user_repository.create.return_value = meli_user

        token = MeliToken(
            user_id=12345,
            access_token='test_access',
            refresh_token='test_refresh',
            expires_at=datetime.now(timezone.utc)
        )

        # Create service with mocked dependencies
        service = MeliAuthService(
            user_repository=mock_user_repository,
            meli_user_service=mock_meli_user_service,
            event_dispatcher=mock_event_dispatcher
        )

        # Act
        result = service.register_user(token)

        # Assert
        mock_event_dispatcher.dispatch.assert_called_once_with(
            user_registered,
            sender=MeliUser,
            meli_user=meli_user,
            token=token
        )
        self.assertEqual(result, meli_user)
