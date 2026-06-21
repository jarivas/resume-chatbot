import structlog
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Education
from app.models import Education as EducationItem

logger = structlog.get_logger(__name__)


class EducationService:
    def __init__(
        self,
        session: AsyncSession,
        chroma_collection: Chroma,
        embeddings: OpenAIEmbeddings,
    ):
        self.session = session
        self.chroma_collection = chroma_collection
        self.embeddings = embeddings

    async def create_education(self, education_data: EducationItem) -> Education:
        logger.info("Creating education entry", institution=education_data.institution)

        education = Education(
            institution=education_data.institution,
            url=str(education_data.url) if education_data.url else None,
            area=education_data.area,
            study_type=education_data.study_type,
            start_date=str(education_data.start_date)
            if education_data.start_date
            else None,
            end_date=str(education_data.end_date) if education_data.end_date else None,
            score=education_data.score,
            courses="|".join(education_data.courses)
            if education_data.courses
            else None,
        )

        try:
            self.session.add(education)
            await self.session.commit()
            await self.session.refresh(education)
            await self._index_education_in_chroma(education)
            logger.info(
                "Education entry created successfully", education_id=education.id
            )
            return education
        except Exception as e:
            await self.session.rollback()
            self.session.expunge(education)
            logger.error(
                "Failed to create education entry",
                error=str(e),
                institution=education_data.institution,
            )
            raise

    async def get_education(self, education_id: str) -> Education | None:
        logger.info("Retrieving education entry", education_id=education_id)
        result = await self.session.execute(
            select(Education).where(Education.id == education_id)
        )
        education = result.scalar_one_or_none()
        if education:
            logger.info("Education entry found", education_id=education_id)
        else:
            logger.warning("Education entry not found", education_id=education_id)
        return education

    async def get_all_education(self) -> list[Education]:
        logger.info("Retrieving all education entries")
        result = await self.session.execute(select(Education))
        education_entries = list(result.scalars().all())
        logger.info("Retrieved education entries", count=len(education_entries))
        return education_entries

    async def update_education(
        self, education_id: str, education_data: EducationItem
    ) -> Education | None:
        logger.info("Updating education entry", education_id=education_id)
        education = await self.get_education(education_id)
        if not education:
            logger.warning(
                "Cannot update non-existent education entry", education_id=education_id
            )
            return None

        education.institution = education_data.institution
        education.url = str(education_data.url) if education_data.url else None
        education.area = education_data.area
        education.study_type = education_data.study_type
        education.start_date = (
            str(education_data.start_date) if education_data.start_date else None
        )
        education.end_date = (
            str(education_data.end_date) if education_data.end_date else None
        )
        education.score = education_data.score
        education.courses = (
            "|".join(education_data.courses) if education_data.courses else None
        )

        try:
            await self.session.commit()
            await self.session.refresh(education)
            await self._index_education_in_chroma(education)
            logger.info(
                "Education entry updated successfully", education_id=education_id
            )
        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to update education entry",
                education_id=education_id,
                error=str(e),
            )
            raise

        return education

    async def delete_education(self, education_id: str) -> bool:
        logger.info("Deleting education entry", education_id=education_id)
        education = await self.get_education(education_id)
        if not education:
            logger.warning(
                "Cannot delete non-existent education entry", education_id=education_id
            )
            return False

        await self._delete_from_chroma(education_id, "education")
        await self.session.delete(education)
        await self.session.commit()
        logger.info("Education entry deleted successfully", education_id=education_id)
        return True

    async def _index_education_in_chroma(self, education: Education) -> None:
        logger.info("Indexing education entry in ChromaDB", education_id=education.id)

        parts = []

        if education.institution:
            parts.append(f"Institution: {education.institution}")
        if education.area:
            parts.append(f"Area: {education.area}")
        if education.study_type:
            parts.append(f"Study Type: {education.study_type}")
        if education.courses:
            courses_list = education.courses.split("|")
            parts.append(f"Courses: {', '.join(courses_list)}")
        if education.start_date or education.end_date:
            parts.append(
                f"Period: {education.start_date or 'Present'} - {education.end_date or 'Present'}"
            )

        content = " | ".join(parts)

        metadata = {
            "entity_type": "education",
            "entity_id": education.id,
            "institution": education.institution or "",
            "area": education.area or "",
            "created_at": education.created_at.isoformat()
            if education.created_at
            else "",
            "updated_at": education.updated_at.isoformat()
            if education.updated_at
            else "",
        }

        await self.chroma_collection.aadd_texts(
            texts=[content],
            metadatas=[metadata],
            ids=[f"education_{education.id}"],
        )
        logger.info("Education entry indexed successfully", education_id=education.id)

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
