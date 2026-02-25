"""Notification model for storing user notifications."""
from django.db import models
from my_auth.models import MeliUser


class Notification(models.Model):
    """Notification model with polymorphic type field."""

    TYPE_CHOICES = [
        ('question', 'Nueva pregunta'),
        ('order', 'Actualización de orden'),
    ]

    # Core fields
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    meli_user = models.ForeignKey(MeliUser, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Type-specific fields (nullable)
    question_id = models.BigIntegerField(null=True, blank=True)
    order_id = models.BigIntegerField(null=True, blank=True)
    status_change = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['meli_user', '-created_at']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f'{self.type} notification for {self.meli_user.user.username}'
