import structlog
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Reference
from app.models import Reference as ReferenceItem

logger = structlog.get_logger(__name__)


class ReferenceService:
    def __init__(
        self,
        session: AsyncSession,
        chroma_collection: Chroma,
        embeddings: OpenAIEmbeddings,
    ):
        self.session = session
        self.chroma_collection = chroma_collection
        self.embeddings = embeddings

    async def create_reference(self, reference_data: ReferenceItem) -> Reference:
        logger.info("Creating reference entry", name=reference_data.name)

        reference = Reference(
            name=reference_data.name,
            reference=reference_data.reference,
        )

        try:
            self.session.add(reference)
            await self.session.commit()
            await self.session.refresh(reference)
            await self._index_reference_in_chroma(reference)
            logger.info("Reference entry created successfully", reference_id=reference.id)
            return reference
        except Exception as e:
            await self.session.rollback()
            self.session.expunge(reference)
            logger.error(
                "Failed to create reference entry", error=str(e), name=reference_data.name
            )
            raise

    async def get_reference(self, reference_id: str) -> Reference | None:
        logger.info("Retrieving reference entry", reference_id=reference_id)
        result = await self.session.execute(select(Reference).where(Reference.id == reference_id))
        reference = result.scalar_one_or_none()
        if reference:
            logger.info("Reference entry found", reference_id=reference_id)
        else:
            logger.warning("Reference entry not found", reference_id=reference_id)
        return reference

    async def get_all_references(self) -> list[Reference]:
        logger.info("Retrieving all reference entries")
        result = await self.session.execute(select(Reference))
        reference_entries = list(result.scalars().all())
        logger.info("Retrieved reference entries", count=len(reference_entries))
        return reference_entries

    async def update_reference(self, reference_id: str, reference_data: ReferenceItem) -> Reference | None:
        logger.info("Updating reference entry", reference_id=reference_id)
        reference = await self.get_reference(reference_id)
        if not reference:
            logger.warning("Cannot update non-existent reference entry", reference_id=reference_id)
            return None

        reference.name = reference_data.name
        reference.reference = reference_data.reference

        try:
            await self.session.commit()
            await self.session.refresh(reference)
            await self._index_reference_in_chroma(reference)
            logger.info("Reference entry updated successfully", reference_id=reference_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to update reference entry", reference_id=reference_id, error=str(e))
            raise

        return reference

    async def delete_reference(self, reference_id: str) -> bool:
        logger.info("Deleting reference entry", reference_id=reference_id)
        reference = await self.get_reference(reference_id)
        if not reference:
            logger.warning("Cannot delete non-existent reference entry", reference_id=reference_id)
            return False

        await self._delete_from_chroma(reference_id, "reference")
        await self.session.delete(reference)
        await self.session.commit()
        logger.info("Reference entry deleted successfully", reference_id=reference_id)
        return True

    async def _index_reference_in_chroma(self, reference: Reference) -> None:
        logger.info("Indexing reference entry in ChromaDB", reference_id=reference.id)

        parts = []

        if reference.name:
            parts.append(f"Reference: {reference.name}")
        if reference.reference:
            parts.append(f"Reference Text: {reference.reference}")

        content = " | ".join(parts)

        metadata = {
            "entity_type": "reference",
            "entity_id": reference.id,
            "name": reference.name or "",
            "created_at": reference.created_at.isoformat() if reference.created_at else "",
            "updated_at": reference.updated_at.isoformat() if reference.updated_at else "",
        }

        await self.chroma_collection.aadd_texts(
            texts=[content],
            metadatas=[metadata],
            ids=[f"reference_{reference.id}"],
        )
        logger.info("Reference entry indexed successfully", reference_id=reference.id)

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
