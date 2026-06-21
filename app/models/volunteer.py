from pydantic import BaseModel, HttpUrl


class Volunteer(BaseModel):
    organization: str | None = None
    position: str | None = None
    url: HttpUrl | None = None
    start_date: str | None = None
    end_date: str | None = None
    summary: str | None = None
    highlights: list[str] | None = None
