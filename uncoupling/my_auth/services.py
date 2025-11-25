from django.db import transaction
from django.contrib.auth.models import User

from mercadolibre.client import MeliToken

from my_auth.models import Token, MeliUser
from my_auth.meli import get_user_info
from my_auth.signals import user_registered


def save_token(token: MeliToken):
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

def register_user(token: MeliToken) -> MeliUser:
    user_info = get_user_info(token)

    with transaction.atomic():
        user = User.objects.create(
            username=user_info.nickname,
            email=user_info.email,
            first_name=user_info.first_name,
            last_name=user_info.last_name,
        )
        meli_user = MeliUser.objects.create(
            id=user_info.id,
            user=user,
        )

    user_registered.send(sender=MeliUser, meli_user=meli_user, token=token)

    return meli_user
