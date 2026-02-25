"""Views for notifications module."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from dependency_injector.wiring import inject, Provide

from notifications.containers import NotificationContainer
from notifications.repositories import NotificationRepository


@login_required
@inject
def notifications_list(
    request,
    notification_repository: NotificationRepository = Provide[NotificationContainer.notification_repository]
):
    """Display list of notifications for the authenticated user."""
    notifications = notification_repository.get_by_user(request.user.meliuser)

    return render(request, 'notifications/notifications_list.html', {
        'notifications': notifications
    })
