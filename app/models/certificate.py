from pydantic import BaseModel, HttpUrl


class Certificate(BaseModel):
    name: str | None = None
    date: str | None = None
    url: HttpUrl | None = None
    issuer: str | None = None
