from datetime import datetime

from django.db import models
from django.contrib.auth.models import User


class MeliUser(models.Model):
    id: int = models.BigIntegerField(primary_key=True, unique=True)  # type: ignore[assignment]
    user: User = models.OneToOneField(User, on_delete=models.CASCADE)  # type: ignore[assignment]
    created_at: datetime = models.DateTimeField(auto_now_add=True)  # type: ignore[assignment]

    def __str__(self) -> str:
        return f'MeliUser {self.id} - {self.user.username}'


class Token(models.Model):
    meli_user: MeliUser = models.OneToOneField(MeliUser, on_delete=models.CASCADE, primary_key=True)  # type: ignore[assignment]
    access_token: str = models.TextField()  # type: ignore[assignment]
    refresh_token: str = models.TextField()  # type: ignore[assignment]
    expires_at: datetime = models.DateTimeField()  # type: ignore[assignment]
    updated_at: datetime = models.DateTimeField(auto_now=True)  # type: ignore[assignment]

    def __str__(self) -> str:
        return f'Token {self.meli_user.id}'
