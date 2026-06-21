from pydantic import BaseModel


class Skill(BaseModel):
    name: str | None = None
    level: str | None = None
    keywords: list[str] | None = None
