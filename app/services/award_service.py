import structlog
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Award
from app.models import Award as AwardItem

logger = structlog.get_logger(__name__)


class AwardService:
    def __init__(
        self,
        session: AsyncSession,
        chroma_collection: Chroma,
        embeddings: OpenAIEmbeddings,
    ):
        self.session = session
        self.chroma_collection = chroma_collection
        self.embeddings = embeddings

    async def create_award(self, award_data: AwardItem) -> Award:
        logger.info("Creating award entry", title=award_data.title)

        award = Award(
            title=award_data.title,
            date=award_data.date,
            awarder=award_data.awarder,
            summary=award_data.summary,
        )

        try:
            self.session.add(award)
            await self.session.commit()
            await self.session.refresh(award)
            await self._index_award_in_chroma(award)
            logger.info("Award entry created successfully", award_id=award.id)
            return award
        except Exception as e:
            await self.session.rollback()
            self.session.expunge(award)
            logger.error(
                "Failed to create award entry", error=str(e), title=award_data.title
            )
            raise

    async def get_award(self, award_id: str) -> Award | None:
        logger.info("Retrieving award entry", award_id=award_id)
        result = await self.session.execute(select(Award).where(Award.id == award_id))
        award = result.scalar_one_or_none()
        if award:
            logger.info("Award entry found", award_id=award_id)
        else:
            logger.warning("Award entry not found", award_id=award_id)
        return award

    async def get_all_awards(self) -> list[Award]:
        logger.info("Retrieving all award entries")
        result = await self.session.execute(select(Award))
        award_entries = list(result.scalars().all())
        logger.info("Retrieved award entries", count=len(award_entries))
        return award_entries

    async def update_award(self, award_id: str, award_data: AwardItem) -> Award | None:
        logger.info("Updating award entry", award_id=award_id)
        award = await self.get_award(award_id)
        if not award:
            logger.warning("Cannot update non-existent award entry", award_id=award_id)
            return None

        award.title = award_data.title
        award.date = award_data.date
        award.awarder = award_data.awarder
        award.summary = award_data.summary

        try:
            await self.session.commit()
            await self.session.refresh(award)
            await self._index_award_in_chroma(award)
            logger.info("Award entry updated successfully", award_id=award_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to update award entry", award_id=award_id, error=str(e))
            raise

        return award

    async def delete_award(self, award_id: str) -> bool:
        logger.info("Deleting award entry", award_id=award_id)
        award = await self.get_award(award_id)
        if not award:
            logger.warning("Cannot delete non-existent award entry", award_id=award_id)
            return False

        await self._delete_from_chroma(award_id, "award")
        await self.session.delete(award)
        await self.session.commit()
        logger.info("Award entry deleted successfully", award_id=award_id)
        return True

    async def _index_award_in_chroma(self, award: Award) -> None:
        logger.info("Indexing award entry in ChromaDB", award_id=award.id)

        parts = []

        if award.title:
            parts.append(f"Title: {award.title}")
        if award.awarder:
            parts.append(f"Awarder: {award.awarder}")
        if award.summary:
            parts.append(f"Summary: {award.summary}")
        if award.date:
            parts.append(f"Date: {award.date}")

        content = " | ".join(parts)

        metadata = {
            "entity_type": "award",
            "entity_id": award.id,
            "title": award.title or "",
            "awarder": award.awarder or "",
            "created_at": award.created_at.isoformat() if award.created_at else "",
            "updated_at": award.updated_at.isoformat() if award.updated_at else "",
        }

        await self.chroma_collection.aadd_texts(
            texts=[content],
            metadatas=[metadata],
            ids=[f"award_{award.id}"],
        )
        logger.info("Award entry indexed successfully", award_id=award.id)

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
