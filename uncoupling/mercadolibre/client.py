import requests

from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

from django.conf import settings
from pydantic import BaseModel


MELI_BASE_URL = "https://api.mercadolibre.com"


class MeliToken(BaseModel):
    user_id: int
    access_token: str
    refresh_token: str
    expires_at: datetime


class MeliClient:
    def __init__(self):
        self.session = requests.Session()

    def get_login_url(self):
        auth_url = "https://auth.mercadolibre.com.ar/authorization"
        params = {
            'response_type': 'code',
            'client_id': settings.MELI_CLIENT_ID,
            'redirect_uri': settings.MELI_REDIRECT_URI,
            'scope': 'read write offline_access'
        }

        return f"{auth_url}?{urlencode(params)}"

    def get_token(self, code: str) -> MeliToken:
        token_url = f'{MELI_BASE_URL}/oauth/token'
        data = {
            'grant_type': 'authorization_code',
            'client_id': settings.MELI_CLIENT_ID,
            'client_secret': settings.MELI_CLIENT_SECRET,
            'code': code,
            'redirect_uri': settings.MELI_REDIRECT_URI,
        }

        response = self.session.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()

        expires_in = token_data.get('expires_in', 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        token_data['expires_at'] = expires_at

        return MeliToken(**token_data)

    def get(self, url, token: MeliToken):
        auth_headers = {
            'Authorization': f'Bearer {token.access_token}'
        }
        response = self.session.get(f'{MELI_BASE_URL}{url}', headers=auth_headers)
        response.raise_for_status()
        return response
