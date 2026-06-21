import structlog
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Publication
from app.models import Publication as PublicationItem

logger = structlog.get_logger(__name__)


class PublicationService:
    def __init__(
        self,
        session: AsyncSession,
        chroma_collection: Chroma,
        embeddings: OpenAIEmbeddings,
    ):
        self.session = session
        self.chroma_collection = chroma_collection
        self.embeddings = embeddings

    async def create_publication(self, publication_data: PublicationItem) -> Publication:
        logger.info("Creating publication entry", name=publication_data.name)

        publication = Publication(
            name=publication_data.name,
            publisher=publication_data.publisher,
            release_date=publication_data.release_date,
            url=str(publication_data.url) if publication_data.url else None,
            summary=publication_data.summary,
        )

        try:
            self.session.add(publication)
            await self.session.commit()
            await self.session.refresh(publication)
            await self._index_publication_in_chroma(publication)
            logger.info("Publication entry created successfully", publication_id=publication.id)
            return publication
        except Exception as e:
            await self.session.rollback()
            self.session.expunge(publication)
            logger.error(
                "Failed to create publication entry", error=str(e), name=publication_data.name
            )
            raise

    async def get_publication(self, publication_id: str) -> Publication | None:
        logger.info("Retrieving publication entry", publication_id=publication_id)
        result = await self.session.execute(select(Publication).where(Publication.id == publication_id))
        publication = result.scalar_one_or_none()
        if publication:
            logger.info("Publication entry found", publication_id=publication_id)
        else:
            logger.warning("Publication entry not found", publication_id=publication_id)
        return publication

    async def get_all_publications(self) -> list[Publication]:
        logger.info("Retrieving all publication entries")
        result = await self.session.execute(select(Publication))
        publication_entries = list(result.scalars().all())
        logger.info("Retrieved publication entries", count=len(publication_entries))
        return publication_entries

    async def update_publication(self, publication_id: str, publication_data: PublicationItem) -> Publication | None:
        logger.info("Updating publication entry", publication_id=publication_id)
        publication = await self.get_publication(publication_id)
        if not publication:
            logger.warning("Cannot update non-existent publication entry", publication_id=publication_id)
            return None

        publication.name = publication_data.name
        publication.publisher = publication_data.publisher
        publication.release_date = publication_data.release_date
        publication.url = str(publication_data.url) if publication_data.url else None
        publication.summary = publication_data.summary

        try:
            await self.session.commit()
            await self.session.refresh(publication)
            await self._index_publication_in_chroma(publication)
            logger.info("Publication entry updated successfully", publication_id=publication_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to update publication entry", publication_id=publication_id, error=str(e))
            raise

        return publication

    async def delete_publication(self, publication_id: str) -> bool:
        logger.info("Deleting publication entry", publication_id=publication_id)
        publication = await self.get_publication(publication_id)
        if not publication:
            logger.warning("Cannot delete non-existent publication entry", publication_id=publication_id)
            return False

        await self._delete_from_chroma(publication_id, "publication")
        await self.session.delete(publication)
        await self.session.commit()
        logger.info("Publication entry deleted successfully", publication_id=publication_id)
        return True

    async def _index_publication_in_chroma(self, publication: Publication) -> None:
        logger.info("Indexing publication entry in ChromaDB", publication_id=publication.id)

        parts = []

        if publication.name:
            parts.append(f"Publication: {publication.name}")
        if publication.publisher:
            parts.append(f"Publisher: {publication.publisher}")
        if publication.summary:
            parts.append(f"Summary: {publication.summary}")
        if publication.release_date:
            parts.append(f"Release Date: {publication.release_date}")

        content = " | ".join(parts)

        metadata = {
            "entity_type": "publication",
            "entity_id": publication.id,
            "name": publication.name or "",
            "publisher": publication.publisher or "",
            "created_at": publication.created_at.isoformat() if publication.created_at else "",
            "updated_at": publication.updated_at.isoformat() if publication.updated_at else "",
        }

        await self.chroma_collection.aadd_texts(
            texts=[content],
            metadatas=[metadata],
            ids=[f"publication_{publication.id}"],
        )
        logger.info("Publication entry indexed successfully", publication_id=publication.id)

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
