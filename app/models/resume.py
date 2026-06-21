from pydantic import BaseModel, HttpUrl

from app.models.basics import Basics
from app.models.work import Work
from app.models.volunteer import Volunteer
from app.models.education import Education
from app.models.award import Award
from app.models.certificate import Certificate
from app.models.publication import Publication
from app.models.skill import Skill
from app.models.language import Language
from app.models.interest import Interest
from app.models.reference import Reference
from app.models.project import Project


class Meta(BaseModel):
    canonical: HttpUrl | None = None
    version: str | None = None
    last_modified: str | None = None


class Resume(BaseModel):
    resume_schema: str | None = None
    basics: Basics | None = None
    work: list[Work] | None = None
    volunteer: list[Volunteer] | None = None
    education: list[Education] | None = None
    awards: list[Award] | None = None
    certificates: list[Certificate] | None = None
    publications: list[Publication] | None = None
    skills: list[Skill] | None = None
    languages: list[Language] | None = None
    interests: list[Interest] | None = None
    references: list[Reference] | None = None
    projects: list[Project] | None = None
    meta: Meta | None = None
