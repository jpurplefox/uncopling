from typing import Optional

from pydantic import BaseModel

from mercadolibre.clients import MeliClient, MeliToken


class MeliUserInfo(BaseModel):
    id: int
    email: str
    nickname: str
    first_name: Optional[str]
    last_name: Optional[str]


class MeliUserService:
    def __init__(self, meli_client: MeliClient):
        self.meli_client = meli_client

    def get_login_url(self):
        return self.meli_client.get_login_url()

    def get_token(self, code: str) -> MeliToken:
        return self.meli_client.get_token(code)

    def get_user_info(self, token: MeliToken) -> MeliUserInfo:
        response = self.meli_client.get('/users/me', token)
        user_info = response.json()
        return MeliUserInfo(**user_info)
