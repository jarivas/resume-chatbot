from pydantic import BaseModel


class Reference(BaseModel):
    name: str | None = None
    reference: str | None = None
