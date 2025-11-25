from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    path('meli/login/', views.meli_login, name='meli_login'),
    path('meli/callback/', views.meli_callback, name='meli_callback'),
    path('logout/', views.meli_logout, name='logout'),
]