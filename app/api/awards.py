import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Award
from app.models import Award as AwardItem
from app.services import AwardService

logger = structlog.get_logger(__name__)


async def get_db_session() -> AsyncSession:
    raise NotImplementedError("Database session dependency not implemented")


async def get_resume_service(
    session: AsyncSession = Depends(get_db_session),
) -> AwardService:
    raise NotImplementedError("Resume service dependency not implemented")


class AwardCreate(BaseModel):
    title: str
    date: str | None = None
    awarder: str | None = None
    summary: str | None = None


class AwardUpdate(BaseModel):
    title: str | None = None
    date: str | None = None
    awarder: str | None = None
    summary: str | None = None


class AwardResponse(BaseModel):
    id: str
    title: str | None
    date: str | None
    awarder: str | None
    summary: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_award(cls, award: Award) -> "AwardResponse":
        return cls(
            id=award.id,
            title=award.title,
            date=award.date,
            awarder=award.awarder,
            summary=award.summary,
            created_at=award.created_at.isoformat() if award.created_at else "",
            updated_at=award.updated_at.isoformat() if award.updated_at else "",
        )


router = APIRouter(prefix="/awards", tags=["awards"])


@router.post(
    "",
    response_model=AwardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create award entry",
    description="Creates a new award entry and synchronizes it with vector database.",
)
async def create_award(
    award_data: AwardCreate,
    service: AwardService = Depends(get_resume_service),
) -> Award:
    logger.info(
        "Creating award entry endpoint",
        title=award_data.title,
        awarder=award_data.awarder,
    )

    award_item = AwardItem(
        title=award_data.title,
        date=award_data.date,
        awarder=award_data.awarder,
        summary=award_data.summary,
    )

    try:
        created_award = await service.create_award(award_item)
        logger.info("Award entry created successfully", award_id=created_award.id)
        return AwardResponse.from_award(created_award)
    except Exception as e:
        logger.error(
            "Failed to create award entry", error=str(e), title=award_data.title
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create award entry: {str(e)}",
        )


@router.get(
    "/{award_id}",
    response_model=AwardResponse,
    summary="Get award entry by ID",
    description="Retrieves a specific award entry by its unique identifier.",
)
async def get_award(
    award_id: str,
    service: AwardService = Depends(get_resume_service),
) -> Award:
    logger.info("Retrieving award entry", award_id=award_id)
    award = await service.get_award(award_id)
    if not award:
        logger.warning("Award entry not found", award_id=award_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Award entry with id {award_id} not found",
        )
    return AwardResponse.from_award(award)


@router.get(
    "",
    response_model=list[AwardResponse],
    summary="Get all award entries",
    description="Retrieves all award entries from database.",
)
async def get_all_awards(
    service: AwardService = Depends(get_resume_service),
) -> list[AwardResponse]:
    logger.info("Retrieving all award entries")
    awards = await service.get_all_awards()
    logger.info("Award entries retrieved", count=len(awards))
    return [AwardResponse.from_award(award) for award in awards]


@router.patch(
    "/{award_id}",
    response_model=AwardResponse,
    summary="Update award entry",
    description="Updates specific fields of an award entry and synchronizes changes with vector database.",
)
async def update_award(
    award_id: str,
    award_update: AwardUpdate,
    service: AwardService = Depends(get_resume_service),
) -> Award:
    logger.info("Updating award entry", award_id=award_id)
    existing_award = await service.get_award(award_id)
    if not existing_award:
        logger.warning("Cannot update non-existent award entry", award_id=award_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Award entry with id {award_id} not found",
        )

    updated_data = AwardItem(
        title=award_update.title if award_update.title is not None else existing_award.title,
        date=award_update.date if award_update.date is not None else existing_award.date,
        awarder=award_update.awarder if award_update.awarder is not None else existing_award.awarder,
        summary=award_update.summary if award_update.summary is not None else existing_award.summary,
    )

    updated_award = await service.update_award(award_id, updated_data)
    logger.info("Award entry updated successfully", award_id=award_id)
    return AwardResponse.from_award(updated_award)


@router.delete(
    "/{award_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete award entry",
    description="Deletes an award entry from both SQLite and ChromaDB.",
)
async def delete_award(
    award_id: str,
    service: AwardService = Depends(get_resume_service),
):
    logger.info("Deleting award entry", award_id=award_id)
    deleted = await service.delete_award(award_id)
    if not deleted:
        logger.warning("Cannot delete non-existent award entry", award_id=award_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Award entry with id {award_id_id} not found",
        )
    logger.info("Award entry deleted successfully", award_id=award_id)
    return None
