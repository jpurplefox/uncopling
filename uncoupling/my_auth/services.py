from typing import Protocol

from django.db import transaction
from django.contrib.auth.models import User

from mercadolibre.client import MeliToken

from my_auth.models import Token, MeliUser
from my_auth.meli import MeliUserService
from my_auth.signals import user_registered


class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> MeliUser:
        ...

    def create(self, username: str, email: str, first_name: str, last_name: str, meli_user_id: int) -> MeliUser:
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


class LoginUrlProvider(Protocol):
    def get_login_url(self) -> str:
        ...


class CallbackHandler(Protocol):
    def handle_callback(self, code: str) -> MeliUser:
        ...


class MeliAuthService:
    def __init__(self, user_repository: UserRepository, meli_user_service: MeliUserService):
        self.user_repository = user_repository
        self.meli_user_service = meli_user_service

    def get_login_url(self) -> str:
        return self.meli_user_service.get_login_url()

    def handle_callback(self, code: str) -> MeliUser:
        token = self.meli_user_service.get_token(code)

        try:
            meli_user = self.user_repository.get_by_id(token.user_id)
        except MeliUser.DoesNotExist:
            meli_user = self.register_user(token)

        self.save_token(token)
        return meli_user

    def save_token(self, token: MeliToken):
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

    def register_user(self, token: MeliToken) -> MeliUser:
        user_info = self.meli_user_service.get_user_info(token)

        meli_user = self.user_repository.create(
            username=user_info.nickname,
            email=user_info.email,
            first_name=user_info.first_name,
            last_name=user_info.last_name,
            meli_user_id=user_info.id,
        )

        user_registered.send(sender=MeliUser, meli_user=meli_user, token=token)

        return meli_user
