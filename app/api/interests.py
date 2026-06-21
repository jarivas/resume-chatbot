import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Interest
from app.models import Interest as InterestItem
from app.services import InterestService

logger = structlog.get_logger(__name__)


async def get_db_session() -> AsyncSession:
    raise NotImplementedError("Database session dependency not implemented")


async def get_resume_service(
    session: AsyncSession = Depends(get_db_session),
) -> InterestService:
    raise NotImplementedError("Resume service dependency not implemented")


class InterestCreate(BaseModel):
    name: str
    keywords: list[str] | None = None


class InterestUpdate(BaseModel):
    name: str | None = None
    keywords: list[str] | None = None


class InterestResponse(BaseModel):
    id: str
    name: str | None
    keywords: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_interest(cls, interest: Interest) -> "InterestResponse":
        return cls(
            id=interest.id,
            name=interest.name,
            keywords=interest.keywords,
            created_at=interest.created_at.isoformat() if interest.created_at else "",
            updated_at=interest.updated_at.isoformat() if interest.updated_at else "",
        )


router = APIRouter(prefix="/interests", tags=["interests"])


@router.post(
    "",
    response_model=InterestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create interest entry",
    description="Creates a new interest entry and synchronizes it with vector database.",
)
async def create_interest(
    interest_data: InterestCreate,
    service: InterestService = Depends(get_resume_service),
) -> Interest:
    logger.info(
        "Creating interest entry endpoint",
        name=interest_data.name,
    )

    interest_item = InterestItem(
        name=interest_data.name,
        keywords=interest_data.keywords,
    )

    try:
        created_interest = await service.create_interest(interest_item)
        logger.info("Interest entry created successfully", interest_id=created_interest.id)
        return InterestResponse.from_interest(created_interest)
    except Exception as e:
        logger.error(
            "Failed to create interest entry", error=str(e), name=interest_data.name
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create interest entry: {str(e)}",
        )


@router.get(
    "/{interest_id}",
    response_model=InterestResponse,
    summary="Get interest entry by ID",
    description="Retrieves a specific interest entry by its unique identifier.",
)
async def get_interest(
    interest_id: str,
    service: InterestService = Depends(get_resume_service),
) -> Interest:
    logger.info("Retrieving interest entry", interest_id=interest_id)
    interest = await service.get_interest(interest_id)
    if not interest:
        logger.warning("Interest entry not found", interest_id=interest_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interest entry with id {interest_id} not found",
        )
    return InterestResponse.from_interest(interest)


@router.get(
    "",
    response_model=list[InterestResponse],
    summary="Get all interest entries",
    description="Retrieves all interest entries from database.",
)
async def get_all_interests(
    service: InterestService = Depends(get_resume_service),
) -> list[InterestResponse]:
    logger.info("Retrieving all interest entries")
    interests = await service.get_all_interests()
    logger.info("Interest entries retrieved", count=len(interests))
    return [InterestResponse.from_interest(interest) for interest in interests]


@router.patch(
    "/{interest_id}",
    response_model=InterestResponse,
    summary="Update interest entry",
    description="Updates specific fields of an interest entry and synchronizes changes with vector database.",
)
async def update_interest(
    interest_id: str,
    interest_update: InterestUpdate,
    service: InterestService = Depends(get_resume_service),
) -> Interest:
    logger.info("Updating interest entry", interest_id=interest_id)
    existing_interest = await service.get_interest(interest_id)
    if not existing_interest:
        logger.warning("Cannot update non-existent interest entry", interest_id=interest_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interest entry with id {interest_id} not found",
        )

    updated_data = InterestItem(
        name=interest_update.name if interest_update.name is not None else existing_interest.name,
        keywords=(
            interest_update.keywords
            if interest_update.keywords is not None
            else existing_interest.keywords.split("|")
            if existing_interest.keywords
            else None
        ),
    )

    updated_interest = await service.update_interest(interest_id, updated_data)
    logger.info("Interest entry updated successfully", interest_id=interest_id)
    return InterestResponse.from_interest(updated_interest)


@router.delete(
    "/{interest_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete interest entry",
    description="Deletes an interest entry from both SQLite and ChromaDB.",
)
async def delete_interest(
    interest_id: str,
    service: InterestService = Depends(get_resume_service),
):
    logger.info("Deleting interest entry", interest_id=interest_id)
    deleted = await service.delete_interest(interest_id)
    if not deleted:
        logger.warning("Cannot delete non-existent interest entry", interest_id=interest_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interest entry with id {interest_id} not found",
        )
    logger.info("Interest entry deleted successfully", interest_id=interest_id)
    return None
