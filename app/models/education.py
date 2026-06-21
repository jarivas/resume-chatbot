from pydantic import BaseModel, HttpUrl


class Education(BaseModel):
    institution: str | None = None
    url: HttpUrl | None = None
    area: str | None = None
    study_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    score: str | None = None
    courses: list[str] | None = None
