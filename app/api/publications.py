import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Publication
from app.models import Publication as PublicationItem
from app.services import PublicationService

logger = structlog.get_logger(__name__)


async def get_db_session() -> AsyncSession:
    raise NotImplementedError("Database session dependency not implemented")


async def get_resume_service(
    session: AsyncSession = Depends(get_db_session),
) -> PublicationService:
    raise NotImplementedError("Resume service dependency not implemented")


class PublicationCreate(BaseModel):
    name: str
    publisher: str | None = None
    release_date: str | None = None
    url: str | None = None
    summary: str | None = None


class PublicationUpdate(BaseModel):
    name: str | None = None
    publisher: str | None = None
    release_date: str | None = None
    url: str | None = None
    summary: str | None = None


class PublicationResponse(BaseModel):
    id: str
    name: str | None
    publisher: str | None
    release_date: str | None
    url: str | None
    summary: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_publication(cls, publication: Publication) -> "PublicationResponse":
        return cls(
            id=publication.id,
            name=publication.name,
            publisher=publication.publisher,
            release_date=publication.release_date,
            url=publication.url,
            summary=publication.summary,
            created_at=publication.created_at.isoformat() if publication.created_at else "",
            updated_at=publication.updated_at.isoformat() if publication.updated_at else "",
        )


router = APIRouter(prefix="/publications", tags=["publications"])


@router.post(
    "",
    response_model=PublicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create publication entry",
    description="Creates a new publication entry and synchronizes it with vector database.",
)
async def create_publication(
    publication_data: PublicationCreate,
    service: PublicationService = Depends(get_resume_service),
) -> Publication:
    logger.info(
        "Creating publication entry endpoint",
        name=publication_data.name,
        publisher=publication_data.publisher,
    )

    publication_item = PublicationItem(
        name=publication_data.name,
        publisher=publication_data.publisher,
        releaseDate=publication_data.release_date,
        url=publication_data.url,
        summary=publication_data.summary,
    )

    try:
        created_publication = await service.create_publication(publication_item)
        logger.info("Publication entry created successfully", publication_id=created_publication.id)
        return PublicationResponse.from_publication(created_publication)
    except Exception as e:
        logger.error(
            "Failed to create publication entry", error=str(e), name=publication_data.name
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create publication entry: {str(e)}",
        )


@router.get(
    "/{publication_id}",
    response_model=PublicationResponse,
    summary="Get publication entry by ID",
    description="Retrieves a specific publication entry by its unique identifier.",
)
async def get_publication(
    publication_id: str,
    service: PublicationService = Depends(get_resume_service),
) -> Publication:
    logger.info("Retrieving publication entry", publication_id=publication_id)
    publication = await service.get_publication(publication_id)
    if not publication:
        logger.warning("Publication entry not found", publication_id=publication_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Publication entry with id {publication_id} not found",
        )
    return PublicationResponse.from_publication(publication)


@router.get(
    "",
    response_model=list[PublicationResponse],
    summary="Get all publication entries",
    description="Retrieves all publication entries from database.",
)
async def get_all_publications(
    service: PublicationService = Depends(get_resume_service),
) -> list[PublicationResponse]:
    logger.info("Retrieving all publication entries")
    publications = await service.get_all_publications()
    logger.info("Publication entries retrieved", count=len(publications))
    return [PublicationResponse.from_publication(publication) for publication in publications]


@router.patch(
    "/{publication_id}",
    response_model=PublicationResponse,
    summary="Update publication entry",
    description="Updates specific fields of a publication entry and synchronizes changes with vector database.",
)
async def update_publication(
    publication_id: str,
    publication_update: PublicationUpdate,
    service: PublicationService = Depends(get_resume_service),
) -> Publication:
    logger.info("Updating publication entry", publication_id=publication_id)
    existing_publication = await service.get_publication(publication_id)
    if not existing_publication:
        logger.warning("Cannot update non-existent publication entry", publication_id=publication_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Publication entry with id {publication_id} not found",
        )

    updated_data = PublicationItem(
        name=publication_update.name if publication_update.name is not None else existing_publication.name,
        publisher=publication_update.publisher if publication_update.publisher is not None else existing_publication.publisher,
        releaseDate=publication_update.release_date if publication_update.release_date is not None else existing_publication.release_date,
        url=publication_update.url if publication_update.url is not None else existing_publication.url,
        summary=publication_update.summary if publication_update.summary is not None else existing_publication.summary,
    )

    updated_publication = await service.update_publication(publication_id, updated_data)
    logger.info("Publication entry updated successfully", publication_id=publication_id)
    return PublicationResponse.from_publication(updated_publication)


@router.delete(
    "/{publication_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete publication entry",
    description="Deletes a publication entry from both SQLite and ChromaDB.",
)
async def delete_publication(
    publication_id: str,
    service: PublicationService = Depends(get_resume_service),
):
    logger.info("Deleting publication entry", publication_id=publication_id)
    deleted = await service.delete_publication(publication_id)
    if not deleted:
        logger.warning("Cannot delete non-existent publication entry", publication_id=publication_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Publication entry with id {publication_id} not found",
        )
    logger.info("Publication entry deleted successfully", publication_id=publication_id)
    return None
