import structlog
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Language
from app.models import Language as LanguageItem

logger = structlog.get_logger(__name__)


class LanguageService:
    def __init__(
        self,
        session: AsyncSession,
        chroma_collection: Chroma,
        embeddings: OpenAIEmbeddings,
    ):
        self.session = session
        self.chroma_collection = chroma_collection
        self.embeddings = embeddings

    async def create_language(self, language_data: LanguageItem) -> Language:
        logger.info("Creating language entry", language=language_data.language)

        language = Language(
            language=language_data.language,
            fluency=language_data.fluency,
        )

        try:
            self.session.add(language)
            await self.session.commit()
            await self.session.refresh(language)
            await self._index_language_in_chroma(language)
            logger.info("Language entry created successfully", language_id=language.id)
            return language
        except Exception as e:
            await self.session.rollback()
            self.session.expunge(language)
            logger.error(
                "Failed to create language entry", error=str(e), language=language_data.language
            )
            raise

    async def get_language(self, language_id: str) -> Language | None:
        logger.info("Retrieving language entry", language_id=language_id)
        result = await self.session.execute(select(Language).where(Language.id == language_id))
        language = result.scalar_one_or_none()
        if language:
            logger.info("Language entry found", language_id=language_id)
        else:
            logger.warning("Language entry not found", language_id=language_id)
        return language

    async def get_all_languages(self) -> list[Language]:
        logger.info("Retrieving all language entries")
        result = await self.session.execute(select(Language))
        language_entries = list(result.scalars().all())
        logger.info("Retrieved language entries", count=len(language_entries))
        return language_entries

    async def update_language(self, language_id: str, language_data: LanguageItem) -> Language | None:
        logger.info("Updating language entry", language_id=language_id)
        language = await self.get_language(language_id)
        if not language:
            logger.warning("Cannot update non-existent language entry", language_id=language_id)
            return None

        language.language = language_data.language
        language.fluency = language_data.fluency

        try:
            await self.session.commit()
            await self.session.refresh(language)
            await self._index_language_in_chroma(language)
            logger.info("Language entry updated successfully", language_id=language_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to update language entry", language_id=language_id, error=str(e))
            raise

        return language

    async def delete_language(self, language_id: str) -> bool:
        logger.info("Deleting language entry", language_id=language_id)
        language = await self.get_language(language_id)
        if not language:
            logger.warning("Cannot delete non-existent language entry", language_id=language_id)
            return False

        await self._delete_from_chroma(language_id, "language")
        await self.session.delete(language)
        await self.session.commit()
        logger.info("Language entry deleted successfully", language_id=language_id)
        return True

    async def _index_language_in_chroma(self, language: Language) -> None:
        logger.info("Indexing language entry in ChromaDB", language_id=language.id)

        parts = []

        if language.language:
            parts.append(f"Language: {language.language}")
        if language.fluency:
            parts.append(f"Fluency: {language.fluency}")

        content = " | ".join(parts)

        metadata = {
            "entity_type": "language",
            "entity_id": language.id,
            "language": language.language or "",
            "fluency": language.fluency or "",
            "created_at": language.created_at.isoformat() if language.created_at else "",
            "updated_at": language.updated_at.isoformat() if language.updated_at else "",
        }

        await self.chroma_collection.aadd_texts(
            texts=[content],
            metadatas=[metadata],
            ids=[f"language_{language.id}"],
        )
        logger.info("Language entry indexed successfully", language_id=language.id)

    async def _delete_from_chroma(self, entity_id: str, entity_type: str) -> None:
        logger.info(
            "Deleting entry from ChromaDB", entity_id=entity_id, entity_type=entity_type
        )
        await self.chroma_collection.adelete(ids=[f"{entity_type}_{entity_id}"])
        logger.info(
            "Entry deleted from ChromaDB successfully",
            entity_id=entity_id,
            entity_type=entity_type,
        )
