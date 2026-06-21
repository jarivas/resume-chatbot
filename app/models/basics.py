from pydantic import BaseModel, EmailStr, HttpUrl

from app.models.location import Location
from app.models.profile import Profile


class Basics(BaseModel):
    name: str | None = None
    label: str | None = None
    image: HttpUrl | None = None
    email: EmailStr | None = None
    phone: str | None = None
    url: HttpUrl | None = None
    summary: str | None = None
    location: Location | None = None
    profiles: list[Profile] | None = None
