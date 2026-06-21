from pydantic import BaseModel, HttpUrl


class Project(BaseModel):
    name: str | None = None
    description: str | None = None
    highlights: list[str] | None = None
    keywords: list[str] | None = None
    start_date: str | None = None
    end_date: str | None = None
    url: HttpUrl | None = None
    roles: list[str] | None = None
    entity: str | None = None
    type: str | None = None
