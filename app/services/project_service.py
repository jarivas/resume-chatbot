import structlog
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project
from app.models import Project as ProjectItem

logger = structlog.get_logger(__name__)


class ProjectService:
    def __init__(
        self,
        session: AsyncSession,
        chroma_collection: Chroma,
        embeddings: OpenAIEmbeddings,
    ):
        self.session = session
        self.chroma_collection = chroma_collection
        self.embeddings = embeddings

    async def create_project(self, project_data: ProjectItem) -> Project:
        logger.info("Creating project entry", name=project_data.name)

        project = Project(
            name=project_data.name,
            description=project_data.description,
            highlights="|".join(project_data.highlights) if project_data.highlights else None,
            keywords="|".join(project_data.keywords) if project_data.keywords else None,
            start_date=str(project_data.start_date) if project_data.start_date else None,
            end_date=str(project_data.end_date) if project_data.end_date else None,
            url=str(project_data.url) if project_data.url else None,
            roles="|".join(project_data.roles) if project_data.roles else None,
            entity=project_data.entity,
            type=project_data.type,
        )

        try:
            self.session.add(project)
            await self.session.commit()
            await self.session.refresh(project)
            await self._index_project_in_chroma(project)
            logger.info("Project entry created successfully", project_id=project.id)
            return project
        except Exception as e:
            await self.session.rollback()
            self.session.expunge(project)
            logger.error(
                "Failed to create project entry", error=str(e), name=project_data.name
            )
            raise

    async def get_project(self, project_id: str) -> Project | None:
        logger.info("Retrieving project entry", project_id=project_id)
        result = await self.session.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if project:
            logger.info("Project entry found", project_id=project_id)
        else:
            logger.warning("Project entry not found", project_id=project_id)
        return project

    async def get_all_projects(self) -> list[Project]:
        logger.info("Retrieving all project entries")
        result = await self.session.execute(select(Project))
        project_entries = list(result.scalars().all())
        logger.info("Retrieved project entries", count=len(project_entries))
        return project_entries

    async def update_project(self, project_id: str, project_data: ProjectItem) -> Project | None:
        logger.info("Updating project entry", project_id=project_id)
        project = await self.get_project(project_id)
        if not project:
            logger.warning("Cannot update non-existent project entry", project_id=project_id)
            return None

        project.name = project_data.name
        project.description = project_data.description
        project.highlights = "|".join(project_data.highlights) if project_data.highlights else None
        project.keywords = "|".join(project_data.keywords) if project_data.keywords else None
        project.start_date = str(project_data.start_date) if project_data.start_date else None
        project.end_date = str(project_data.end_date) if project_data.end_date else None
        project.url = str(project_data.url) if project_data.url else None
        project.roles = "|".join(project_data.roles) if project_data.roles else None
        project.entity = project_data.entity
        project.type = project_data.type

        try:
            await self.session.commit()
            await self.session.refresh(project)
            await self._index_project_in_chroma(project)
            logger.info("Project entry updated successfully", project_id=project_id)
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to update project entry", project_id=project_id, error=str(e))
            raise

        return project

    async def delete_project(self, project_id: str) -> bool:
        logger.info("Deleting project entry", project_id=project_id)
        project = await self.get_project(project_id)
        if not project:
            logger.warning("Cannot delete non-existent project entry", project_id=project_id)
            return False

        await self._delete_from_chroma(project_id, "project")
        await self.session.delete(project)
        await self.session.commit()
        logger.info("Project entry deleted successfully", project_id=project_id)
        return True

    async def _index_project_in_chroma(self, project: Project) -> None:
        logger.info("Indexing project entry in ChromaDB", project_id=project.id)

        parts = []

        if project.name:
            parts.append(f"Project: {project.name}")
        if project.description:
            parts.append(f"Description: {project.description}")
        if project.entity:
            parts.append(f"Entity: {project.entity}")
        if project.type:
            parts.append(f"Type: {project.type}")
        if project.highlights:
            highlights_list = project.highlights.split("|")
            parts.append(f"Highlights: {', '.join(highlights_list)}")
        if project.keywords:
            keywords_list = project.keywords.split("|")
            parts.append(f"Keywords: {', '.join(keywords_list)}")
        if project.roles:
            roles_list = project.roles.split("|")
            parts.append(f"Roles: {', '.join(roles_list)}")
        if project.start_date or project.end_date:
            parts.append(
                f"Period: {project.start_date or 'Present'} - {project.end_date or 'Present'}"
            )

        content = " | ".join(parts)

        metadata = {
            "entity_type": "project",
            "entity_id": project.id,
            "name": project.name or "",
            "entity": project.entity or "",
            "type": project.type or "",
            "created_at": project.created_at.isoformat() if project.created_at else "",
            "updated_at": project.updated_at.isoformat() if project.updated_at else "",
        }

        await self.chroma_collection.aadd_texts(
            texts=[content],
            metadatas=[metadata],
            ids=[f"project_{project.id}"],
        )
        logger.info("Project entry indexed successfully", project_id=project.id)

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
