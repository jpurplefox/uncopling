from django.shortcuts import render, redirect
from django.http import JsonResponse
from dependency_injector.wiring import Provide, inject

from my_auth.forms import MeliCallbackForm
from my_auth.services import (
    LoginUrlProvider,
    CallbackHandler,
    SessionAuthenticator,
    SessionTerminator,
)
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
    callback_handler: CallbackHandler = Provide[AuthContainer.auth_service],
    session_auth: SessionAuthenticator = Provide[AuthContainer.session_authenticator]
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
    session_auth.authenticate_session(request, meli_user.user)

    return redirect('/')


@inject
def meli_logout(
    request,
    session_terminator: SessionTerminator = Provide[AuthContainer.session_terminator]
):
    """Logout user from the application"""
    session_terminator.terminate_session(request)
    return redirect('/')
