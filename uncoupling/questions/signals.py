from django.dispatch import receiver

from my_auth.signals import user_registered
from questions.services import fetch_and_save_questions_from_meli


@receiver(user_registered)
def on_user_registered(sender, meli_user, token, **kwargs):
    fetch_and_save_questions_from_meli(meli_user, token)
