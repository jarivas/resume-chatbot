import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Reference
from app.models import Reference as ReferenceItem
from app.services import ReferenceService

logger = structlog.get_logger(__name__)


async def get_db_session() -> AsyncSession:
    raise NotImplementedError("Database session dependency not implemented")


async def get_resume_service(
    session: AsyncSession = Depends(get_db_session),
) -> ReferenceService:
    raise NotImplementedError("Resume service dependency not implemented")


class ReferenceCreate(BaseModel):
    name: str
    reference: str | None = None


class ReferenceUpdate(BaseModel):
    name: str | None = None
    reference: str | None = None


class ReferenceResponse(BaseModel):
    id: str
    name: str | None
    reference: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_reference(cls, reference: Reference) -> "ReferenceResponse":
        return cls(
            id=reference.id,
            name=reference.name,
            reference=reference.reference,
            created_at=reference.created_at.isoformat() if reference.created_at else "",
            updated_at=reference.updated_at.isoformat() if reference.updated_at else "",
        )


router = APIRouter(prefix="/references", tags=["references"])


@router.post(
    "",
    response_model=ReferenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create reference entry",
    description="Creates a new reference entry and synchronizes it with vector database.",
)
async def create_reference(
    reference_data: ReferenceCreate,
    service: ReferenceService = Depends(get_resume_service),
) -> Reference:
    logger.info(
        "Creating reference entry endpoint",
        name=reference_data.name,
    )

    reference_item = ReferenceItem(
        name=reference_data.name,
        reference=reference_data.reference,
    )

    try:
        created_reference = await service.create_reference(reference_item)
        logger.info("Reference entry created successfully", reference_id=created_reference.id)
        return ReferenceResponse.from_reference(created_reference)
    except Exception as e:
        logger.error(
            "Failed to create reference entry", error=str(e), name=reference_data.name
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create reference entry: {str(e)}",
        )


@router.get(
    "/{reference_id}",
    response_model=ReferenceResponse,
    summary="Get reference entry by ID",
    description="Retrieves a specific reference entry by its unique identifier.",
)
async def get_reference(
    reference_id: str,
    service: ReferenceService = Depends(get_resume_service),
) -> Reference:
    logger.info("Retrieving reference entry", reference_id=reference_id)
    reference = await service.get_reference(reference_id)
    if not reference:
        logger.warning("Reference entry not found", reference_id=reference_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference entry with id {reference_id} not found",
        )
    return ReferenceResponse.from_reference(reference)


@router.get(
    "",
    response_model=list[ReferenceResponse],
    summary="Get all reference entries",
    description="Retrieves all reference entries from database.",
)
async def get_all_references(
    service: ReferenceService = Depends(get_resume_service),
) -> list[ReferenceResponse]:
    logger.info("Retrieving all reference entries")
    references = await service.get_all_references()
    logger.info("Reference entries retrieved", count=len(references))
    return [ReferenceResponse.from_reference(reference) for reference in references]


@router.patch(
    "/{reference_id}",
    response_model=ReferenceResponse,
    summary="Update reference entry",
    description="Updates specific fields of a reference entry and synchronizes changes with vector database.",
)
async def update_reference(
    reference_id: str,
    reference_update: ReferenceUpdate,
    service: ReferenceService = Depends(get_resume_service),
) -> Reference:
    logger.info("Updating reference entry", reference_id=reference_id)
    existing_reference = await service.get_reference(reference_id)
    if not existing_reference:
        logger.warning("Cannot update non-existent reference entry", reference_id=reference_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference entry with id {reference_id} not found",
        )

    updated_data = ReferenceItem(
        name=reference_update.name if reference_update.name is not None else existing_reference.name,
        reference=reference_update.reference if reference_update.reference is not None else existing_reference.reference,
    )

    updated_reference = await service.update_reference(reference_id, updated_data)
    logger.info("Reference entry updated successfully", reference_id=reference_id)
    return ReferenceResponse.from_reference(updated_reference)


@router.delete(
    "/{reference_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete reference entry",
    description="Deletes a reference entry from both SQLite and ChromaDB.",
)
async def delete_reference(
    reference_id: str,
    service: ReferenceService = Depends(get_resume_service),
):
    logger.info("Deleting reference entry", reference_id=reference_id)
    deleted = await service.delete_reference(reference_id)
    if not deleted:
        logger.warning("Cannot delete non-existent reference entry", reference_id=reference_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reference entry with id {reference_id} not found",
        )
    logger.info("Reference entry deleted successfully", reference_id=reference_id)
    return None
