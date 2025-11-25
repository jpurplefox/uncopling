from django.db import models
from my_auth.models import MeliUser


class Question(models.Model):
    STATUS_CHOICES = [
        ('UNANSWERED', 'Sin responder'),
        ('ANSWERED', 'Respondida'),
        ('CLOSED_UNANSWERED', 'Cerrada sin responder'),
        ('UNDER_REVIEW', 'En revisión'),
        ('BANNED', 'Bloqueada'),
    ]

    id = models.BigIntegerField(primary_key=True)
    meli_user = models.ForeignKey(MeliUser, on_delete=models.CASCADE, related_name='questions')
    item_id = models.CharField(max_length=50)
    text = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    date_created = models.DateTimeField()
    from_user_id = models.BigIntegerField()
    answer_text = models.TextField(null=True, blank=True)
    answer_date_created = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        return f'Question {self.id} - {self.text[:50]}'
