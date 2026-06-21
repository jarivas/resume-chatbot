from pydantic import BaseModel, HttpUrl


class Publication(BaseModel):
    name: str | None = None
    publisher: str | None = None
    release_date: str | None = None
    url: HttpUrl | None = None
    summary: str | None = None
