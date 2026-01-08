from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from dependency_injector.wiring import inject, Provide

from orders.containers import OrderContainer
from orders.services import OrderRepository


@login_required
@inject
def orders_list(
    request,
    order_repository: OrderRepository = Provide[OrderContainer.order_repository]
):
    """Display list of orders for the authenticated user"""
    orders = order_repository.get_by_user(request.user.meliuser)
    return render(request, 'orders/orders_list.html', {
        'orders': orders
    })
