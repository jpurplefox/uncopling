"""Django admin configuration for notifications."""
from django.contrib import admin
from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'meli_user', 'title', 'created_at', 'read_at')
    list_filter = ('type', 'created_at', 'read_at')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
