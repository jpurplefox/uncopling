from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.http import JsonResponse

from mercadolibre.client import get_meli_login_url, get_token

from my_auth.forms import MeliCallbackForm
from my_auth.models import MeliUser
from my_auth.services import register_user, save_token


def home(request):
    """Display home page with login button or user nickname"""
    return render(request, 'my_auth/home.html')


def meli_login(request):
    """Redirect user to MercadoLibre OAuth authorization page"""
    url = get_meli_login_url()
    return redirect(url)


def meli_callback(request):
    """Handle MercadoLibre OAuth callback"""
    form = MeliCallbackForm(request.GET)
    if not form.is_valid():
        return JsonResponse(
            {'error': form.errors.as_json()},
            status=400
        )
    code = form.cleaned_data.get('code')

    token = get_token(code)
    try:
        meli_user = MeliUser.objects.get(id=token.user_id)
    except MeliUser.DoesNotExist:
        meli_user = register_user(token)

    save_token(token)
    login(request, meli_user.user)

    return redirect('/')


def meli_logout(request):
    """Logout user from the application"""
    logout(request)
    return redirect('/')
