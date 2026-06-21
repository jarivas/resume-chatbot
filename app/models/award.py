from pydantic import BaseModel


class Award(BaseModel):
    title: str | None = None
    date: str | None = None
    awarder: str | None = None
    summary: str | None = None
