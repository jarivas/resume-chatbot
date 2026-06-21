import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Language
from app.models import Language as LanguageItem
from app.services import LanguageService

logger = structlog.get_logger(__name__)


async def get_db_session() -> AsyncSession:
    raise NotImplementedError("Database session dependency not implemented")


async def get_resume_service(
    session: AsyncSession = Depends(get_db_session),
) -> LanguageService:
    raise NotImplementedError("Resume service dependency not implemented")


class LanguageCreate(BaseModel):
    language: str
    fluency: str | None = None


class LanguageUpdate(BaseModel):
    language: str | None = None
    fluency: str | None = None


class LanguageResponse(BaseModel):
    id: str
    language: str | None
    fluency: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_language(cls, language: Language) -> "LanguageResponse":
        return cls(
            id=language.id,
            language=language.language,
            fluency=language.fluency,
            created_at=language.created_at.isoformat() if language.created_at else "",
            updated_at=language.updated_at.isoformat() if language.updated_at else "",
        )


router = APIRouter(prefix="/languages", tags=["languages"])


@router.post(
    "",
    response_model=LanguageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create language entry",
    description="Creates a new language entry and synchronizes it with vector database.",
)
async def create_language(
    language_data: LanguageCreate,
    service: LanguageService = Depends(get_resume_service),
) -> Language:
    logger.info(
        "Creating language entry endpoint",
        language=language_data.language,
        fluency=language_data.fluency,
    )

    language_item = LanguageItem(
        language=language_data.language,
        fluency=language_data.fluency,
    )

    try:
        created_language = await service.create_language(language_item)
        logger.info("Language entry created successfully", language_id=created_language.id)
        return LanguageResponse.from_language(created_language)
    except Exception as e:
        logger.error(
            "Failed to create language entry", error=str(e), language=language_data.language
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create language entry: {str(e)}",
        )


@router.get(
    "/{language_id}",
    response_model=LanguageResponse,
    summary="Get language entry by ID",
    description="Retrieves a specific language entry by its unique identifier.",
)
async def get_language(
    language_id: str,
    service: LanguageService = Depends(get_resume_service),
) -> Language:
    logger.info("Retrieving language entry", language_id=language_id)
    language = await service.get_language(language_id)
    if not language:
        logger.warning("Language entry not found", language_id=language_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language entry with id {language_id} not found",
        )
    return LanguageResponse.from_language(language)


@router.get(
    "",
    response_model=list[LanguageResponse],
    summary="Get all language entries",
    description="Retrieves all language entries from database.",
)
async def get_all_languages(
    service: LanguageService = Depends(get_resume_service),
) -> list[LanguageResponse]:
    logger.info("Retrieving all language entries")
    languages = await service.get_all_languages()
    logger.info("Language entries retrieved", count=len(languages))
    return [LanguageResponse.from_language(language) for language in languages]


@router.patch(
    "/{language_id}",
    response_model=LanguageResponse,
    summary="Update language entry",
    description="Updates specific fields of a language entry and synchronizes changes with vector database.",
)
async def update_language(
    language_id: str,
    language_update: LanguageUpdate,
    service: LanguageService = Depends(get_resume_service),
) -> Language:
    logger.info("Updating language entry", language_id=language_id)
    existing_language = await service.get_language(language_id)
    if not existing_language:
        logger.warning("Cannot update non-existent language entry", language_id=language_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language entry with id {language_id} not found",
        )

    updated_data = LanguageItem(
        language=language_update.language if language_update.language is not None else existing_language.language,
        fluency=language_update.fluency if language_update.fluency is not None else existing_language.fluency,
    )

    updated_language = await service.update_language(language_id, updated_data)
    logger.info("Language entry updated successfully", language_id=language_id)
    return LanguageResponse.from_language(updated_language)


@router.delete(
    "/{language_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete language entry",
    description="Deletes a language entry from both SQLite and ChromaDB.",
)
async def delete_language(
    language_id: str,
    service: LanguageService = Depends(get_resume_service),
):
    logger.info("Deleting language entry", language_id=language_id)
    deleted = await service.delete_language(language_id)
    if not deleted:
        logger.warning("Cannot delete non-existent language entry", language_id=language_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language entry with id {language_id} not found",
        )
    logger.info("Language entry deleted successfully", language_id=language_id)
    return None
