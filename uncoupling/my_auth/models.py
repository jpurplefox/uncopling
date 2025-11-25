from django.db import models
from django.contrib.auth.models import User


class MeliUser(models.Model):
    id = models.BigIntegerField(primary_key=True, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'MeliUser {self.id} - {self.user.username}'


class Token(models.Model):
    meli_user = models.OneToOneField(MeliUser, on_delete=models.CASCADE, primary_key=True)
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Token {self.user_id}'
