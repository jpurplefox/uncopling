from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.http import JsonResponse
from dependency_injector.wiring import Provide, inject

from my_auth.forms import MeliCallbackForm
from my_auth.services import LoginUrlProvider, CallbackHandler
from my_auth.containers import AuthContainer


def home(request):
    """Display home page with login button or user nickname"""
    return render(request, 'my_auth/home.html')


@inject
def meli_login(
    request,
    login_url_provider: LoginUrlProvider = Provide[AuthContainer.auth_service]
):
    """Redirect user to MercadoLibre OAuth authorization page"""
    url = login_url_provider.get_login_url()
    return redirect(url)


@inject
def meli_callback(
    request,
    callback_handler: CallbackHandler = Provide[AuthContainer.auth_service]
):
    """Handle MercadoLibre OAuth callback"""
    form = MeliCallbackForm(request.GET)
    if not form.is_valid():
        return JsonResponse(
            {'error': form.errors.as_json()},
            status=400
        )
    code = form.cleaned_data.get('code')

    meli_user = callback_handler.handle_callback(code)
    login(request, meli_user.user)

    return redirect('/')


def meli_logout(request):
    """Logout user from the application"""
    logout(request)
    return redirect('/')
