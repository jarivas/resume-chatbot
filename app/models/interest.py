from pydantic import BaseModel


class Interest(BaseModel):
    name: str | None = None
    keywords: list[str] | None = None
