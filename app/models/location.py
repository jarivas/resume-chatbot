from pydantic import BaseModel, EmailStr, HttpUrl


class Location(BaseModel):
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country_code: str | None = None
    region: str | None = None
