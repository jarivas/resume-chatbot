import structlog
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Skill
from app.models import Skill as SkillItem

logger = structlog.get_logger(__name__)


class SkillService:
    def __init__(
        self,
        session: AsyncSession,
        chroma_collection: Chroma,
        embeddings: OpenAIEmbeddings,
    ):
        self.session = session
        self.chroma_collection = chroma_collection
        self.embeddings = embeddings

    async def create_skill(self, skill_data: SkillItem) -> Skill:
        logger.info("Creating skill entry", skill_name=skill_data.name)

        skill = Skill(
            name=skill_data.name,
            level=skill_data.level,
            keywords="|".join(skill_data.keywords) if skill_data.keywords else None,
        )

        try:
            self.session.add(skill)
            await self.session.commit()
            await self.session.refresh(skill)
            await self._index_skill_in_chroma(skill)
            logger.info("Skill entry created successfully", skill_id=skill.id)
            return skill
        except Exception as e:
            await self.session.rollback()
            self.session.expunge(skill)
            logger.error(
                "Failed to create skill entry", error=str(e), skill_name=skill_data.name
            )
            raise

    async def get_skill(self, skill_id: str) -> Skill | None:
        logger.info("Retrieving skill entry", skill_id=skill_id)
        result = await self.session.execute(select(Skill).where(Skill.id == skill_id))
        skill = result.scalar_one_or_none()
        if skill:
            logger.info("Skill entry found", skill_id=skill_id)
        else:
            logger.warning("Skill entry not found", skill_id=skill_id)
        return skill

    async def get_all_skills(self) -> list[Skill]:
        logger.info("Retrieving all skill entries")
        result = await self.session.execute(select(Skill))
        skill_entries = list(result.scalars().all())
        logger.info("Retrieved skill entries", count=len(skill_entries))
        return skill_entries

    async def update_skill(self, skill_id: str, skill_data: SkillItem) -> Skill | None:
        logger.info("Updating skill entry", skill_id=skill_id)
        skill = await self.get_skill(skill_id)
        if not skill:
            logger.warning("Cannot update non-existent skill entry", skill_id=skill_id)
            return None

        skill.name = skill_data.name
        skill.level = skill_data.level
        skill.keywords = "|".join(skill_data.keywords) if skill_data.keywords else None

        try:
            await self.session.commit()
            await self.session.refresh(skill)
            await self._index_skill_in_chroma(skill)
            logger.info("Skill entry updated successfully", skill_id=skill_id)
        except Exception as e:
            await self.session.rollback()
            logger.error(
                "Failed to update skill entry", skill_id=skill_id, error=str(e)
            )
            raise

        return skill

    async def delete_skill(self, skill_id: str) -> bool:
        logger.info("Deleting skill entry", skill_id=skill_id)
        skill = await self.get_skill(skill_id)
        if not skill:
            logger.warning("Cannot delete non-existent skill entry", skill_id=skill_id)
            return False

        await self._delete_from_chroma(skill_id, "skill")
        await self.session.delete(skill)
        await self.session.commit()
        logger.info("Skill entry deleted successfully", skill_id=skill_id)
        return True

    async def _index_skill_in_chroma(self, skill: Skill) -> None:
        logger.info("Indexing skill entry in ChromaDB", skill_id=skill.id)

        parts = []

        if skill.name:
            parts.append(f"Skill: {skill.name}")
        if skill.level:
            parts.append(f"Level: {skill.level}")
        if skill.keywords:
            keywords_list = skill.keywords.split("|")
            parts.append(f"Keywords: {', '.join(keywords_list)}")

        content = " | ".join(parts)

        metadata = {
            "entity_type": "skill",
            "entity_id": skill.id,
            "skill": skill.name or "",
            "level": skill.level or "",
            "created_at": skill.created_at.isoformat() if skill.created_at else "",
            "updated_at": skill.updated_at.isoformat() if skill.updated_at else "",
        }

        await self.chroma_collection.aadd_texts(
            texts=[content],
            metadatas=[metadata],
            ids=[f"skill_{skill.id}"],
        )
        logger.info("Skill entry indexed successfully", skill_id=skill.id)

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
