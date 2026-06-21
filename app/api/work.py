import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Work
from app.models.resume_schema import Work as WorkItem
from app.services.cv_service import ResumeService

logger = structlog.get_logger(__name__)


async def get_db_session() -> AsyncSession:
    raise NotImplementedError("Database session dependency not implemented")


async def get_resume_service(
    session: AsyncSession = Depends(get_db_session),
) -> ResumeService:
    raise NotImplementedError("Resume service dependency not implemented")


class WorkCreate(BaseModel):
    name: str
    location: str | None = None
    description: str | None = None
    position: str | None = None
    url: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    summary: str | None = None
    highlights: list[str] | None = None


class WorkUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    description: str | None = None
    position: str | None = None
    url: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    summary: str | None = None
    highlights: list[str] | None = None


class WorkResponse(BaseModel):
    id: str
    name: str | None
    location: str | None
    description: str | None
    position: str | None
    url: str | None
    start_date: str | None
    end_date: str | None
    summary: str | None
    highlights: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_work(cls, work: Work) -> "WorkResponse":
        return cls(
            id=work.id,
            name=work.name,
            location=work.location,
            description=work.description,
            position=work.position,
            url=work.url,
            start_date=work.start_date,
            end_date=work.end_date,
            summary=work.summary,
            highlights=work.highlights,
            created_at=work.created_at.isoformat() if work.created_at else "",
            updated_at=work.updated_at.isoformat() if work.updated_at else "",
        )


router = APIRouter(prefix="/work", tags=["work"])


@router.post(
    "",
    response_model=WorkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create work experience",
    description="Creates a new work experience entry and synchronizes it with the vector database.",
)
async def create_work(
    work_data: WorkCreate,
    service: ResumeService = Depends(get_resume_service),
) -> Work:
    logger.info(
        "Creating work experience endpoint",
        company=work_data.name,
        position=work_data.position,
    )

    work_item = WorkItem(
        name=work_data.name,
        location=work_data.location,
        description=work_data.description,
        position=work_data.position,
        url=work_data.url,
        startDate=work_data.start_date,
        endDate=work_data.end_date,
        summary=work_data.summary,
        highlights=work_data.highlights,
    )

    try:
        created_work = await service.create_work(work_item)
        logger.info("Work experience created successfully", work_id=created_work.id)
        return WorkResponse.from_work(created_work)
    except Exception as e:
        logger.error(
            "Failed to create work experience", error=str(e), company=work_data.name
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create work experience: {str(e)}",
        )


@router.get(
    "/{work_id}",
    response_model=WorkResponse,
    summary="Get work experience by ID",
    description="Retrieves a specific work experience entry by its unique identifier.",
)
async def get_work(
    work_id: str,
    service: ResumeService = Depends(get_resume_service),
) -> Work:
    logger.info("Retrieving work experience", work_id=work_id)
    work = await service.get_work(work_id)
    if not work:
        logger.warning("Work experience not found", work_id=work_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work experience with id {work_id} not found",
        )
    return WorkResponse.from_work(work)


@router.get(
    "",
    response_model=list[WorkResponse],
    summary="Get all work experiences",
    description="Retrieves all work experience entries from the database.",
)
async def get_all_work(
    service: ResumeService = Depends(get_resume_service),
) -> list[WorkResponse]:
    logger.info("Retrieving all work experiences")
    works = await service.get_all_work()
    logger.info("Work experiences retrieved", count=len(works))
    return [WorkResponse.from_work(work) for work in works]


@router.patch(
    "/{work_id}",
    response_model=WorkResponse,
    summary="Update work experience",
    description="Updates specific fields of a work experience entry and synchronizes changes with the vector database.",
)
async def update_work(
    work_id: str,
    work_update: WorkUpdate,
    service: ResumeService = Depends(get_resume_service),
) -> Work:
    logger.info("Updating work experience", work_id=work_id)
    existing_work = await service.get_work(work_id)
    if not existing_work:
        logger.warning("Cannot update non-existent work experience", work_id=work_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work experience with id {work_id} not found",
        )

    updated_data = WorkItem(
        name=work_update.name if work_update.name is not None else existing_work.name,
        location=(
            work_update.location
            if work_update.location is not None
            else existing_work.location
        ),
        description=(
            work_update.description
            if work_update.description is not None
            else existing_work.description
        ),
        position=(
            work_update.position
            if work_update.position is not None
            else existing_work.position
        ),
        url=work_update.url if work_update.url is not None else existing_work.url,
        start_date=(
            work_update.start_date
            if work_update.start_date is not None
            else existing_work.start_date
        ),
        end_date=(
            work_update.end_date
            if work_update.end_date is not None
            else existing_work.end_date
        ),
        summary=(
            work_update.summary
            if work_update.summary is not None
            else existing_work.summary
        ),
        highlights=(
            work_update.highlights
            if work_update.highlights is not None
            else existing_work.highlights.split("|")
            if existing_work.highlights
            else None
        ),
    )

    updated_work = await service.update_work(work_id, updated_data)
    logger.info("Work experience updated successfully", work_id=work_id)
    return WorkResponse.from_work(updated_work)


@router.delete(
    "/{work_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete work experience",
    description="Deletes a work experience entry from both SQLite and ChromaDB.",
)
async def delete_work(
    work_id: str,
    service: ResumeService = Depends(get_resume_service),
):
    logger.info("Deleting work experience", work_id=work_id)
    deleted = await service.delete_work(work_id)
    if not deleted:
        logger.warning("Cannot delete non-existent work experience", work_id=work_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work experience with id {work_id} not found",
        )
    logger.info("Work experience deleted successfully", work_id=work_id)
    return None
