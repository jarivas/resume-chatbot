import structlog
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Volunteer
from app.models import Volunteer as VolunteerItem

logger = structlog.get_logger(__name__)


class VolunteerService:
    def __init__(
        self,
        session: AsyncSession,
        chroma_collection: Chroma,
        embeddings: OpenAIEmbeddings,
    ):
        self.session = session
        self.chroma_collection = chroma_collection
        self.embeddings = embeddings

    async def create_volunteer(self, volunteer_data: VolunteerItem) -> Volunteer:
        logger.info("Creating volunteer entry", organization=volunteer_data.organization)

        volunteer = Volunteer(
            organization=volunteer_data.organization,
            position=volunteer_data.position,
            url=str(volunteer_data.url) if volunteer_data.url else None,
            start_date=str(volunteer_data.start_date) if volunteer_data.start_date else None,
            end_date=str(volunteer_data.end_date) if volunteer_data.end_date else None,
            summary=volunteer_data.summary,
            highlights="|".join(volunteer_data.highlights) if volunteer_data.highlights else None,
        )

        try:
            self.session.add(volunteer)
            await self.session.commit()
            await self.session.refresh(volunteer)
            await self._index_volunteer_in_chroma(volunteer)
            logger.info("Volunteer entry created successfully", volunteer_id=volunteer.id)
            return volunteer
        except Exception as e:
            await self.session.rollback()
            self.session.expunge(volunteer)
            logger.error(
                "Failed to create volunteer entry", error=str(e), organization=volunteer_data.organization
            )
            raise

    async def get_volunteer(self, volunteer_id: str) -> Volunteer | None:
        logger.info("Retrieving volunteer entry", volunteer_id=volunteer_id)
        result = await self.session.execute(select(Volunteer).where(Volunteer.id == volunteer_id))
        volunteer = result.scalar_one_or_none()
        if volunteer:
            logger.info("Volunteer entry found", volunteer_id=volunteer_id)
        else:
            logger.warning("Volunteer entry not found", volunteer_id=volunteer_id)
        return volunteer

    async def get_all_volunteer(self) -> list[Volunteer]:
        logger.info("Retrieving all volunteer entries")
        result = await self.session.execute(select(Volunteer))
        volunteer_entries = list(result.scalars().all())
        logger.info("Retrieved volunteer entries", count=len(volunteer_entries))
        return volunteer_entries

    async def update_volunteer(self, volunteer_id: str, volunteer_data: VolunteerItem) -> Volunteer | None:
        logger.info("Updating volunteer entry", volunteer_id=volunteer_id)
        volunteer = await self.get_volunteer(volunteer_id)
        if not volunteer:
            logger.warning("Cannot update non-existent volunteer entry", volunteer_id=volunteer_id)
            return None

        volunteer.organization = volunteer_data.organization
        volunteer.position = volunteer_data.position
        volunteer.url = str(volunteer_data.url) if volunteer_data.url else None
        volunteer.start_date = str(volunteer_data.start_date) if volunteer_data.start_date else None
        volunteer.end_date = str(volunteer_data.end_date) if volunteer_data.end_date else None
        volunteer.summary = volunteer_data.summary
        volunteer.highlights = "|".join(volunteer_data.highlights) if volunteer_data.highlights else None

        try:
            await self.session.commit()
            await self.session.refresh(volunteer)
            await self._index_volunteer_in_chroma(volunteer)
            logger.info("Volunteer entry updated successfully", volunteer_id=volunteer_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to update volunteer entry", volunteer_id=volunteer_id, error=str(e))
            raise

        return volunteer

    async def delete_volunteer(self, volunteer_id: str) -> bool:
        logger.info("Deleting volunteer entry", volunteer_id=volunteer_id)
        volunteer = await self.get_volunteer(volunteer_id)
        if not volunteer:
            logger.warning("Cannot delete non-existent volunteer entry", volunteer_id=volunteer_id)
            return False

        await self._delete_from_chroma(volunteer_id, "volunteer")
        await self.session.delete(volunteer)
        await self.session.commit()
        logger.info("Volunteer entry deleted successfully", volunteer_id=volunteer_id)
        return True

    async def _index_volunteer_in_chroma(self, volunteer: Volunteer) -> None:
        logger.info("Indexing volunteer entry in ChromaDB", volunteer_id=volunteer.id)

        parts = []

        if volunteer.position:
            parts.append(f"Position: {volunteer.position}")
        if volunteer.organization:
            parts.append(f"Organization: {volunteer.organization}")
        if volunteer.summary:
            parts.append(f"Summary: {volunteer.summary}")
        if volunteer.highlights:
            highlights_list = volunteer.highlights.split("|")
            parts.append(f"Highlights: {', '.join(highlights_list)}")
        if volunteer.start_date or volunteer.end_date:
            parts.append(
                f"Period: {volunteer.start_date or 'Present'} - {volunteer.end_date or 'Present'}"
            )

        content = " | ".join(parts)

        metadata = {
            "entity_type": "volunteer",
            "entity_id": volunteer.id,
            "position": volunteer.position or "",
            "organization": volunteer.organization or "",
            "created_at": volunteer.created_at.isoformat() if volunteer.created_at else "",
            "updated_at": volunteer.updated_at.isoformat() if volunteer.updated_at else "",
        }

        await self.chroma_collection.aadd_texts(
            texts=[content],
            metadatas=[metadata],
            ids=[f"volunteer_{volunteer.id}"],
        )
        logger.info("Volunteer entry indexed successfully", volunteer_id=volunteer.id)

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
