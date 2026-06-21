import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Education
from app.models.resume_schema import Education as EducationItem
from app.services.cv_service import ResumeService

logger = structlog.get_logger(__name__)


async def get_db_session() -> AsyncSession:
    raise NotImplementedError("Database session dependency not implemented")


async def get_resume_service(
    session: AsyncSession = Depends(get_db_session),
) -> ResumeService:
    raise NotImplementedError("Resume service dependency not implemented")


class EducationCreate(BaseModel):
    institution: str
    url: str | None = None
    area: str | None = None
    study_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    score: str | None = None
    courses: list[str] | None = None


class EducationUpdate(BaseModel):
    institution: str | None = None
    url: str | None = None
    area: str | None = None
    study_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    score: str | None = None
    courses: list[str] | None = None


class EducationResponse(BaseModel):
    id: str
    institution: str | None
    url: str | None
    area: str | None
    study_type: str | None
    start_date: str | None
    end_date: str | None
    score: str | None
    courses: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_education(cls, education: Education) -> "EducationResponse":
        return cls(
            id=education.id,
            institution=education.institution,
            url=education.url,
            area=education.area,
            study_type=education.study_type,
            start_date=education.start_date,
            end_date=education.end_date,
            score=education.score,
            courses=education.courses,
            created_at=education.created_at.isoformat() if education.created_at else "",
            updated_at=education.updated_at.isoformat() if education.updated_at else "",
        )


router = APIRouter(prefix="/education", tags=["education"])


@router.post(
    "",
    response_model=EducationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create education entry",
    description="Creates a new education entry and synchronizes it with the vector database.",
)
async def create_education(
    education_data: EducationCreate,
    service: ResumeService = Depends(get_resume_service),
) -> Education:
    logger.info(
        "Creating education entry endpoint",
        institution=education_data.institution,
        area=education_data.area,
    )

    education_item = EducationItem(
        institution=education_data.institution,
        url=education_data.url,
        area=education_data.area,
        study_type=education_data.study_type,
        start_date=education_data.start_date,
        end_date=education_data.end_date,
        score=education_data.score,
        courses=education_data.courses,
    )

    try:
        created_education = await service.create_education(education_item)
        logger.info("Education entry created successfully", education_id=created_education.id)
        return EducationResponse.from_education(created_education)
    except Exception as e:
        logger.error(
            "Failed to create education entry", error=str(e), institution=education_data.institution
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create education entry: {str(e)}",
        )


@router.get(
    "/{education_id}",
    response_model=EducationResponse,
    summary="Get education entry by ID",
    description="Retrieves a specific education entry by its unique identifier.",
)
async def get_education(
    education_id: str,
    service: ResumeService = Depends(get_resume_service),
) -> Education:
    logger.info("Retrieving education entry", education_id=education_id)
    education = await service.get_education(education_id)
    if not education:
        logger.warning("Education entry not found", education_id=education_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Education entry with id {education_id} not found",
        )
    return EducationResponse.from_education(education)


@router.get(
    "",
    response_model=list[EducationResponse],
    summary="Get all education entries",
    description="Retrieves all education entries from the database.",
)
async def get_all_education(
    service: ResumeService = Depends(get_resume_service),
) -> list[EducationResponse]:
    logger.info("Retrieving all education entries")
    educations = await service.get_all_education()
    logger.info("Education entries retrieved", count=len(educations))
    return [EducationResponse.from_education(education) for education in educations]


@router.patch(
    "/{education_id}",
    response_model=EducationResponse,
    summary="Update education entry",
    description="Updates specific fields of an education entry and synchronizes changes with the vector database.",
)
async def update_education(
    education_id: str,
    education_update: EducationUpdate,
    service: ResumeService = Depends(get_resume_service),
) -> Education:
    logger.info("Updating education entry", education_id=education_id)
    existing_education = await service.get_education(education_id)
    if not existing_education:
        logger.warning("Cannot update non-existent education entry", education_id=education_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Education entry with id {education_id} not found",
        )

    updated_data = EducationItem(
        institution=(
            education_update.institution
            if education_update.institution is not None
            else existing_education.institution
        ),
        url=education_update.url if education_update.url is not None else existing_education.url,
        area=education_update.area if education_update.area is not None else existing_education.area,
        study_type=(
            education_update.study_type
            if education_update.study_type is not None
            else existing_education.study_type
        ),
        start_date=(
            education_update.start_date
            if education_update.start_date is not None
            else existing_education.start_date
        ),
        end_date=(
            education_update.end_date
            if education_update.end_date is not None
            else existing_education.end_date
        ),
        score=education_update.score if education_update.score is not None else existing_education.score,
        courses=(
            education_update.courses
            if education_update.courses is not None
            else existing_education.courses.split("|")
            if existing_education.courses
            else None
        ),
    )

    updated_education = await service.update_education(education_id, updated_data)
    logger.info("Education entry updated successfully", education_id=education_id)
    return EducationResponse.from_education(updated_education)


@router.delete(
    "/{education_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete education entry",
    description="Deletes an education entry from both SQLite and ChromaDB.",
)
async def delete_education(
    education_id: str,
    service: ResumeService = Depends(get_resume_service),
):
    logger.info("Deleting education entry", education_id=education_id)
    deleted = await service.delete_education(education_id)
    if not deleted:
        logger.warning("Cannot delete non-existent education entry", education_id=education_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Education entry with id {education_id} not found",
        )
    logger.info("Education entry deleted successfully", education_id=education_id)
    return None
