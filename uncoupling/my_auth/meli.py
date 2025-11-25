from typing import Optional

from pydantic import BaseModel

from mercadolibre.client import MeliClient, MeliToken


class MeliUserInfo(BaseModel):
    id: int
    email: str
    nickname: str
    first_name: Optional[str]
    last_name: Optional[str]


def get_user_info(token: MeliToken) -> MeliUserInfo:
    client = MeliClient(token)
    response = client.get('/users/me')
    user_info = response.json()
    return MeliUserInfo(**user_info)
