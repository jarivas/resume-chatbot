import structlog
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Interest
from app.models import Interest as InterestItem

logger = structlog.get_logger(__name__)


class InterestService:
    def __init__(
        self,
        session: AsyncSession,
        chroma_collection: Chroma,
        embeddings: OpenAIEmbeddings,
    ):
        self.session = session
        self.chroma_collection = chroma_collection
        self.embeddings = embeddings

    async def create_interest(self, interest_data: InterestItem) -> Interest:
        logger.info("Creating interest entry", name=interest_data.name)

        interest = Interest(
            name=interest_data.name,
            keywords="|".join(interest_data.keywords) if interest_data.keywords else None,
        )

        try:
            self.session.add(interest)
            await self.session.commit()
            await self.session.refresh(interest)
            await self._index_interest_in_chroma(interest)
            logger.info("Interest entry created successfully", interest_id=interest.id)
            return interest
        except Exception as e:
            await self.session.rollback()
            self.session.expunge(interest)
            logger.error(
                "Failed to create interest entry", error=str(e), name=interest_data.name
            )
            raise

    async def get_interest(self, interest_id: str) -> Interest | None:
        logger.info("Retrieving interest entry", interest_id=interest_id)
        result = await self.session.execute(select(Interest).where(Interest.id == interest_id))
        interest = result.scalar_one_or_none()
        if interest:
            logger.info("Interest entry found", interest_id=interest_id)
        else:
            logger.warning("Interest entry not found", interest_id=interest_id)
        return interest

    async def get_all_interests(self) -> list[Interest]:
        logger.info("Retrieving all interest entries")
        result = await self.session.execute(select(Interest))
        interest_entries = list(result.scalars().all())
        logger.info("Retrieved interest entries", count=len(interest_entries))
        return interest_entries

    async def update_interest(self, interest_id: str, interest_data: InterestItem) -> Interest | None:
        logger.info("Updating interest entry", interest_id=interest_id)
        interest = await self.get_interest(interest_id)
        if not interest:
            logger.warning("Cannot update non-existent interest entry", interest_id=interest_id)
            return None

        interest.name = interest_data.name
        interest.keywords = "|".join(interest_data.keywords) if interest_data.keywords else None

        try:
            await self.session.commit()
            await self.session.refresh(interest)
            await self._index_interest_in_chroma(interest)
            logger.info("Interest entry updated successfully", interest_id=interest_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to update interest entry", interest_id=interest_id, error=str(e))
            raise

        return interest

    async def delete_interest(self, interest_id: str) -> bool:
        logger.info("Deleting interest entry", interest_id=interest_id)
        interest = await self.get_interest(interest_id)
        if not interest:
            logger.warning("Cannot delete non-existent interest entry", interest_id=interest_id)
            return False

        await self._delete_from_chroma(interest_id, "interest")
        await self.session.delete(interest)
        await self.session.commit()
        logger.info("Interest entry deleted successfully", interest_id=interest_id)
        return True

    async def _index_interest_in_chroma(self, interest: Interest) -> None:
        logger.info("Indexing interest entry in ChromaDB", interest_id=interest.id)

        parts = []

        if interest.name:
            parts.append(f"Interest: {interest.name}")
        if interest.keywords:
            keywords_list = interest.keywords.split("|")
            parts.append(f"Keywords: {', '.join(keywords_list)}")

        content = " | ".join(parts)

        metadata = {
            "entity_type": "interest",
            "entity_id": interest.id,
            "name": interest.name or "",
            "created_at": interest.created_at.isoformat() if interest.created_at else "",
            "updated_at": interest.updated_at.isoformat() if interest.updated_at else "",
        }

        await self.chroma_collection.aadd_texts(
            texts=[content],
            metadatas=[metadata],
            ids=[f"interest_{interest.id}"],
        )
        logger.info("Interest entry indexed successfully", interest_id=interest.id)

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
