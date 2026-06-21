from pydantic import BaseModel, HttpUrl


class Profile(BaseModel):
    network: str | None = None
    username: str | None = None
    url: HttpUrl | None = None
