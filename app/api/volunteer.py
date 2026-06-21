import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Volunteer
from app.models import Volunteer as VolunteerItem
from app.services import VolunteerService

logger = structlog.get_logger(__name__)


async def get_db_session() -> AsyncSession:
    raise NotImplementedError("Database session dependency not implemented")


async def get_resume_service(
    session: AsyncSession = Depends(get_db_session),
) -> VolunteerService:
    raise NotImplementedError("Resume service dependency not implemented")


class VolunteerCreate(BaseModel):
    organization: str
    position: str | None = None
    url: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    summary: str | None = None
    highlights: list[str] | None = None


class VolunteerUpdate(BaseModel):
    organization: str | None = None
    position: str | None = None
    url: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    summary: str | None = None
    highlights: list[str] | None = None


class VolunteerResponse(BaseModel):
    id: str
    organization: str | None
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
    def from_volunteer(cls, volunteer: Volunteer) -> "VolunteerResponse":
        return cls(
            id=volunteer.id,
            organization=volunteer.organization,
            position=volunteer.position,
            url=volunteer.url,
            start_date=volunteer.start_date,
            end_date=volunteer.end_date,
            summary=volunteer.summary,
            highlights=volunteer.highlights,
            created_at=volunteer.created_at.isoformat() if volunteer.created_at else "",
            updated_at=volunteer.updated_at.isoformat() if volunteer.updated_at else "",
        )


router = APIRouter(prefix="/volunteer", tags=["volunteer"])


@router.post(
    "",
    response_model=VolunteerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create volunteer entry",
    description="Creates a new volunteer entry and synchronizes it with the vector database.",
)
async def create_volunteer(
    volunteer_data: VolunteerCreate,
    service: VolunteerService = Depends(get_resume_service),
) -> Volunteer:
    logger.info(
        "Creating volunteer entry endpoint",
        organization=volunteer_data.organization,
        position=volunteer_data.position,
    )

    volunteer_item = VolunteerItem(
        organization=volunteer_data.organization,
        position=volunteer_data.position,
        url=volunteer_data.url,
        start_date=volunteer_data.start_date,
        end_date=volunteer_data.end_date,
        summary=volunteer_data.summary,
        highlights=volunteer_data.highlights,
    )

    try:
        created_volunteer = await service.create_volunteer(volunteer_item)
        logger.info("Volunteer entry created successfully", volunteer_id=created_volunteer.id)
        return VolunteerResponse.from_volunteer(created_volunteer)
    except Exception as e:
        logger.error(
            "Failed to create volunteer entry", error=str(e), organization=volunteer_data.organization
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create volunteer entry: {str(e)}",
        )


@router.get(
    "/{volunteer_id}",
    response_model=VolunteerResponse,
    summary="Get volunteer entry by ID",
    description="Retrieves a specific volunteer entry by its unique identifier.",
)
async def get_volunteer(
    volunteer_id: str,
    get_resume_service),(get_resume_service),
) -> Volunteer:
    logger.info("Retrieving volunteer entry", volunteer_id=volunteer_id)
    volunteer = await service.get_volunteer(volunteer_id)
    if not volunteer:
        logger.warning("Volunteer entry not found", volunteer_id=volunteer_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Volunteer entry with id {volunteer_id} not found",
        )
    return VolunteerResponse.from_volunteer(volunteer)


@router.get(
    "",
    response_model=list[VolunteerResponse],
    summary="Get all volunteer entries",
    description="Retrieves all volunteer entries from the database.",
)
async def get_all_volunteer(
    get_resume_service),(get_resume_service),
) -> list[VolunteerResponse]:
    logger.info("Retrieving all volunteer entries")
    volunteers = await service.get_all_volunteer()
    logger.info("Volunteer entries retrieved", count=len(volunteers))
    return [VolunteerResponse.from_volunteer(volunteer) for volunteer in volunteers]


@router.patch(
    "/{volunteer_id}",
    response_model=VolunteerResponse,
    summary="Update volunteer entry",
    description="Updates specific fields of a volunteer entry and synchronizes changes with the vector database.",
)
async def update_volunteer(
    volunteer_id: str,
    volunteer_update: VolunteerUpdate,
    get_resume_service),(get_resume_service),
) -> Volunteer:
    logger.info("Updating volunteer entry", volunteer_id=volunteer_id)
    existing_volunteer = await service.get_volunteer(volunteer_id)
    if not existing_volunteer:
        logger.warning("Cannot update non-existent volunteer entry", volunteer_id=volunteer_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Volunteer entry with id {volunteer_id} not found",
        )

    updated_data = VolunteerItem(
        organization=(
            volunteer_update.organization
            if volunteer_update.organization is not None
            else existing_volunteer.organization
        ),
        position=(
            volunteer_update.position
            if volunteer_update.position is not None
            else existing_volunteer.position
        ),
        url=volunteer_update.url if volunteer_update.url is not None else existing_volunteer.url,
        start_date=(
            volunteer_update.start_date
            if volunteer_update.start_date is not None
            else existing_volunteer.start_date
        ),
        end_date=(
            volunteer_update.end_date
            if volunteer_update.end_date is not None
            else existing_volunteer.end_date
        ),
        summary=(
            volunteer_update.summary
            if volunteer_update.summary is not None
            else existing_volunteer.summary
        ),
        highlights=(
            volunteer_update.highlights
            if volunteer_update.highlights is not None
            else existing_volunteer.highlights.split("|")
            if existing_volunteer.highlights
            else None
        ),
    )

    updated_volunteer = await service.update_volunteer(volunteer_id, updated_data)
    logger.info("Volunteer entry updated successfully", volunteer_id=volunteer_id)
    return VolunteerResponse.from_volunteer(updated_volunteer)


@router.delete(
    "/{volunteer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete volunteer entry",
    description="Deletes a volunteer entry from both SQLite and ChromaDB.",
)
async def delete_volunteer(
    volunteer_id: str,
    get_resume_service),(get_resume_service),
):
    logger.info("Deleting volunteer entry", volunteer_id=volunteer_id)
    deleted = await service.delete_volunteer(volunteer_id)
    if not deleted:
        logger.warning("Cannot delete non-existent volunteer entry", volunteer_id=volunteer_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Volunteer entry with id {volunteer_id} not found",
        )
    logger.info("Volunteer entry deleted successfully", volunteer_id=volunteer_id)
    return None
