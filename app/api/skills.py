import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Skill
from app.models.resume_schema import Skill as SkillItem
from app.services.cv_service import ResumeService

logger = structlog.get_logger(__name__)


async def get_db_session() -> AsyncSession:
    raise NotImplementedError("Database session dependency not implemented")


async def get_resume_service(
    session: AsyncSession = Depends(get_db_session),
) -> ResumeService:
    raise NotImplementedError("Resume service dependency not implemented")


class SkillCreate(BaseModel):
    name: str
    level: str | None = None
    keywords: list[str] | None = None


class SkillUpdate(BaseModel):
    name: str | None = None
    level: str | None = None
    keywords: list[str] | None = None


class SkillResponse(BaseModel):
    id: str
    name: str | None
    level: str | None
    keywords: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_skill(cls, skill: Skill) -> "SkillResponse":
        return cls(
            id=skill.id,
            name=skill.name,
            level=skill.level,
            keywords=skill.keywords,
            created_at=skill.created_at.isoformat() if skill.created_at else "",
            updated_at=skill.updated_at.isoformat() if skill.updated_at else "",
        )


router = APIRouter(prefix="/skills", tags=["skills"])


@router.post(
    "",
    response_model=SkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create skill entry",
    description="Creates a new skill entry and synchronizes it with the vector database.",
)
async def create_skill(
    skill_data: SkillCreate,
    service: ResumeService = Depends(get_resume_service),
) -> Skill:
    logger.info(
        "Creating skill entry endpoint",
        name=skill_data.name,
        level=skill_data.level,
    )

    skill_item = SkillItem(
        name=skill_data.name,
        level=skill_data.level,
        keywords=skill_data.keywords,
    )

    try:
        created_skill = await service.create_skill(skill_item)
        logger.info("Skill entry created successfully", skill_id=created_skill.id)
        return SkillResponse.from_skill(created_skill)
    except Exception as e:
        logger.error(
            "Failed to create skill entry", error=str(e), name=skill_data.name
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create skill entry: {str(e)}",
        )


@router.get(
    "/{skill_id}",
    response_model=SkillResponse,
    summary="Get skill entry by ID",
    description="Retrieves a specific skill entry by its unique identifier.",
)
async def get_skill(
    skill_id: str,
    service: ResumeService = Depends(get_resume_service),
) -> Skill:
    logger.info("Retrieving skill entry", skill_id_id=skill_id)
    skill = await service.get_skill(skill_id)
    if not skill:
        logger.warning("Skill entry not found", skill_id=skill_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill entry with id {skill_id} not found",
        )
    return SkillResponse.from_skill(skill)


@router.get(
    "",
    response_model=list[SkillResponse],
    summary="Get all skill entries",
    description="Retrieves all skill entries from the database.",
)
async def get_all_skills(
    service: ResumeService = Depends(get_resume_service),
) -> list[SkillResponse]:
    logger.info("Retrieving all skill entries")
    skills = await service.get_all_skills()
    logger.info("Skill entries retrieved", count=len(skills))
    return [SkillResponse.from_skill(skill) for skill in skills]


@router.patch(
    "/{skill_id}",
    response_model=SkillResponse,
    summary="Update skill entry",
    description="Updates specific fields of a skill entry and synchronizes changes with the vector database.",
)
async def update_skill(
    skill_id: str,
    skill_update: SkillUpdate,
    service: ResumeService = Depends(get_resume_service),
) -> Skill:
    logger.info("Updating skill entry", skill_id=skill_id)
    existing_skill = await service.get_skill(skill_id)
    if not existing_skill:
        logger.warning("Cannot update non-existent skill entry", skill_id=skill_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill entry with id {skill_id} not found",
        )

    updated_data = SkillItem(
        name=skill_update.name if skill_update.name is not None else existing_skill.name,
        level=skill_update.level if skill_update.level is not None else existing_skill.level,
        keywords=(
            skill_update.keywords
            if skill_update.keywords is not None
            else existing_skill.keywords.split("|")
            if existing_skill.keywords
            else None
        ),
    )

    updated_skill = await service.update_skill(skill_id, updated_data)
    logger.info("Skill entry updated successfully", skill_id=skill_id)
    return SkillResponse.from_skill(updated_skill)


@router.delete(
    "/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete skill entry",
    description="Deletes a skill entry from both SQLite and ChromaDB.",
)
async def delete_skill(
    skill_id: str,
    service: ResumeService = Depends(get_resume_service),
):
    logger.info("Deleting skill entry", skill_id=skill_id)
    deleted = await service.delete_skill(skill_id)
    if not deleted:
        logger.warning("Cannot delete non-existent skill entry", skill_id=skill_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill entry with id {skill_id} not found",
        )
    logger.info("Skill entry deleted successfully", skill_id=skill_id)
    return None
