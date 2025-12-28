from unittest.mock import Mock
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

from my_auth.views import meli_login, meli_callback, meli_logout
from my_auth.models import MeliUser
from my_auth.containers import auth_container


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
