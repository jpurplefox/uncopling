from typing import Protocol

from django.db import transaction
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.contrib.auth import login as django_login, logout as django_logout
from django.dispatch import Signal

from mercadolibre.client import MeliToken

from my_auth.models import Token, MeliUser
from my_auth.meli import MeliUserService
from my_auth.signals import user_registered


class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> MeliUser:
        ...

    def create(self, username: str, email: str, first_name: str, last_name: str, meli_user_id: int) -> MeliUser:
        ...

    def save_token(self, token: MeliToken) -> None:
        ...


class DBUserRepository:
    def get_by_id(self, user_id: int) -> MeliUser:
        return MeliUser.objects.get(id=user_id)

    def create(self, username: str, email: str, first_name: str, last_name: str, meli_user_id: int) -> MeliUser:
        with transaction.atomic():
            user = User.objects.create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            meli_user = MeliUser.objects.create(
                id=meli_user_id,
                user=user,
            )
        return meli_user

    def save_token(self, token: MeliToken) -> None:
        instance, created = Token.objects.get_or_create(
            meli_user_id=token.user_id,
            defaults={
                'access_token': token.access_token,
                'refresh_token': token.refresh_token,
                'expires_at': token.expires_at,
            }
        )
        if not created:
            instance.access_token = token.access_token
            instance.refresh_token = token.refresh_token
            instance.expires_at = token.expires_at
            instance.save()


class DjangoSessionManager:
    """Concrete implementation for session management using Django's built-in auth.
    Implements both SessionAuthenticator and SessionTerminator protocols.
    """

    def authenticate_session(self, request: HttpRequest, user: User) -> None:
        """Authenticate user using Django's session-based auth"""
        django_login(request, user)

    def terminate_session(self, request: HttpRequest) -> None:
        """Terminate session using Django's logout"""
        django_logout(request)


class DjangoSignalEventDispatcher:
    """Concrete implementation for event dispatching using Django signals.
    Implements the EventDispatcher protocol.
    """

    def dispatch(self, signal: Signal, sender: type, **kwargs) -> None:
        """Dispatch an event using Django's signal system"""
        signal.send(sender=sender, **kwargs)


class LoginUrlProvider(Protocol):
    def get_login_url(self) -> str:
        ...


class CallbackHandler(Protocol):
    def handle_callback(self, code: str) -> MeliUser:
        ...


class SessionAuthenticator(Protocol):
    """Protocol for authenticating a user in the current session"""
    def authenticate_session(self, request: HttpRequest, user: User) -> None:
        """Authenticate the user in the current session"""
        ...


class SessionTerminator(Protocol):
    """Protocol for terminating the current user session"""
    def terminate_session(self, request: HttpRequest) -> None:
        """Terminate/logout the current user session"""
        ...


class EventDispatcher(Protocol):
    """Protocol for dispatching events/signals"""
    def dispatch(self, signal: Signal, sender: type, **kwargs) -> None:
        """
        Dispatch an event using the given signal.

        Args:
            signal: The Django Signal to dispatch
            sender: The sender of the signal (typically a model class)
            **kwargs: Arbitrary keyword arguments to pass to signal receivers
        """
        ...


class MeliAuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        meli_user_service: MeliUserService,
        event_dispatcher: EventDispatcher
    ):
        self.user_repository = user_repository
        self.meli_user_service = meli_user_service
        self.event_dispatcher = event_dispatcher

    def get_login_url(self) -> str:
        return self.meli_user_service.get_login_url()

    def handle_callback(self, code: str) -> MeliUser:
        token = self.meli_user_service.get_token(code)

        try:
            meli_user = self.user_repository.get_by_id(token.user_id)
        except MeliUser.DoesNotExist:
            meli_user = self._register_user(token)

        self.user_repository.save_token(token)
        return meli_user

    def _register_user(self, token: MeliToken) -> MeliUser:
        user_info = self.meli_user_service.get_user_info(token)

        meli_user = self.user_repository.create(
            username=user_info.nickname,
            email=user_info.email,
            first_name=user_info.first_name,
            last_name=user_info.last_name,
            meli_user_id=user_info.id,
        )

        self.event_dispatcher.dispatch(user_registered, sender=MeliUser, meli_user=meli_user, token=token)

        return meli_user
