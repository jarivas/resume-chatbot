import structlog
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Work
from app.models import Work as WorkItem

logger = structlog.get_logger(__name__)


class WorkService:
    def __init__(
        self,
        session: AsyncSession,
        chroma_collection: Chroma,
        embeddings: OpenAIEmbeddings,
    ):
        self.session = session
        self.chroma_collection = chroma_collection
        self.embeddings = embeddings

    async def create_work(self, work_data: WorkItem) -> Work:
        logger.info(
            "Creating work entry", company=work_data.name, position=work_data.position
        )

        work = Work(
            name=work_data.name,
            location=work_data.location,
            description=work_data.description,
            position=work_data.position,
            url=str(work_data.url) if work_data.url else None,
            start_date=str(work_data.start_date) if work_data.start_date else None,
            end_date=str(work_data.end_date) if work_data.end_date else None,
            summary=work_data.summary,
            highlights="|".join(work_data.highlights) if work_data.highlights else None,
        )

        try:
            self.session.add(work)
            await self.session.commit()
            await self.session.refresh(work)
            await self._index_work_in_chroma(work)
            logger.info("Work entry created successfully", work_id=work.id)
            return work
        except Exception as e:
            await self.session.rollback()
            self.session.expunge(work)
            logger.error(
                "Failed to create work entry", error=str(e), company=work_data.name
            )
            raise

    async def get_work(self, work_id: str) -> Work | None:
        logger.info("Retrieving work entry", work_id=work_id)
        result = await self.session.execute(select(Work).where(Work.id == work_id))
        work = result.scalar_one_or_none()
        if work:
            logger.info("Work entry found", work_id=work_id)
        else:
            logger.warning("Work entry not found", work_id=work_id)
        return work

    async def get_all_work(self) -> list[Work]:
        logger.info("Retrieving all work entries")
        result = await self.session.execute(select(Work))
        work_entries = list(result.scalars().all())
        logger.info("Retrieved work entries", count=len(work_entries))
        return work_entries

    async def update_work(self, work_id: str, work_data: WorkItem) -> Work | None:
        logger.info("Updating work entry", work_id=work_id)
        work = await self.get_work(work_id)
        if not work:
            logger.warning("Cannot update non-existent work entry", work_id=work_id)
            return None

        work.name = work_data.name
        work.location = work_data.location
        work.description = work_data.description
        work.position = work_data.position
        work.url = str(work_data.url) if work_data.url else None
        work.start_date = str(work_data.start_date) if work_data.start_date else None
        work.end_date = str(work_data.end_date) if work_data.end_date else None
        work.summary = work_data.summary
        work.highlights = (
            "|".join(work_data.highlights) if work_data.highlights else None
        )

        try:
            await self.session.commit()
            await self.session.refresh(work)
            await self._index_work_in_chroma(work)
            logger.info("Work entry updated successfully", work_id=work_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to update work entry", work_id=work_id, error=str(e))
            raise

        return work

    async def delete_work(self, work_id: str) -> bool:
        logger.info("Deleting work entry", work_id=work_id)
        work = await self.get_work(work_id)
        if not work:
            logger.warning("Cannot delete non-existent work entry", work_id=work_id)
            return False

        await self._delete_from_chroma(work_id, "work")
        await self.session.delete(work)
        await self.session.commit()
        logger.info("Work entry deleted successfully", work_id=work_id)
        return True

    async def _index_work_in_chroma(self, work: Work) -> None:
        logger.info("Indexing work entry in ChromaDB", work_id=work.id)

        parts = []

        if work.position:
            parts.append(f"Position: {work.position}")
        if work.name:
            parts.append(f"Company: {work.name}")
        if work.summary:
            parts.append(f"Summary: {work.summary}")
        if work.highlights:
            highlights_list = work.highlights.split("|")
            parts.append(f"Highlights: {', '.join(highlights_list)}")
        if work.start_date or work.end_date:
            parts.append(
                f"Period: {work.start_date or 'Present'} - {work.end_date or 'Present'}"
            )

        content = " | ".join(parts)

        metadata = {
            "entity_type": "work",
            "entity_id": work.id,
            "position": work.position or "",
            "company": work.name or "",
            "created_at": work.created_at.isoformat() if work.created_at else "",
            "updated_at": work.updated_at.isoformat() if work.updated_at else "",
        }

        await self.chroma_collection.aadd_texts(
            texts=[content],
            metadatas=[metadata],
            ids=[f"work_{work.id}"],
        )
        logger.info("Work entry indexed successfully", work_id=work.id)

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
