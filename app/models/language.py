from pydantic import BaseModel


class Language(BaseModel):
    language: str | None = None
    fluency: str | None = None
