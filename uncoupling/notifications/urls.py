"""URL configuration for notifications module."""
from django.urls import path
from notifications import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notifications_list, name='list'),
]
