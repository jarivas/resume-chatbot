import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project
from app.models import Project as ProjectItem
from app.services import ProjectService

logger = structlog.get_logger(__name__)


async def get_db_session() -> AsyncSession:
    raise NotImplementedError("Database session dependency not implemented")


async def get_resume_service(
    session: AsyncSession = Depends(get_db_session),
) -> ProjectService:
    raise NotImplementedError("Resume service dependency not implemented")


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    highlights: list[str] | None = None
    keywords: list[str] | None = None
    start_date: str | None = None
    end_date: str | None = None
    url: str | None = None
    roles: list[str] | None = None
    entity: str | None = None
    type: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    highlights: list[str] | None = None
    keywords: list[str] | None = None
    start_date: str | None = None
    end_date: str | None = None
    url: str | None = None
    roles: list[str] | None = None
    entity: str | None = None
    type: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str | None
    description: str | None
    highlights: str | None
    keywords: str | None
    start_date: str | None
    end_date: str | None
    url: str | None
    roles: str | None
    entity: str | None
    type: str | None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_project(cls, project: Project) -> "ProjectResponse":
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            highlights=project.highlights,
            keywords=project.keywords,
            start_date=project.start_date,
            end_date=project.end_date,
            url=project.url,
            roles=project.roles,
            entity=project.entity,
            type=project.type,
            created_at=project.created_at.isoformat() if project.created_at else "",
            updated_at=project.updated_at.isoformat() if project.updated_at else "",
        )


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create project entry",
    description="Creates a new project entry and synchronizes it with vector database.",
)
async def create_project(
    project_data: ProjectCreate,
    service: ProjectService = Depends(get_resume_service),
) -> Project:
    logger.info(
        "Creating project entry endpoint",
        name=project_data.name,
        entity=project_data.entity,
    )

    project_item = ProjectItem(
        name=project_data.name,
        description=project_data.description,
        highlights=project_data.highlights,
        keywords=project_data.keywords,
        start_date=project_data.start_date,
        end_date=project_data.end_date,
        url=project_data.url,
        roles=project_data.roles,
        entity=project_data.entity,
        type=project_data.type,
    )

    try:
        created_project = await service.create_project(project_item)
        logger.info("Project entry created successfully", project_id=created_project.id)
        return ProjectResponse.from_project(created_project)
    except Exception as e:
        logger.error(
            "Failed to create project entry", error=str(e), name=project_data.name
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project entry: {str(e)}",
        )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project entry by ID",
    description="Retrieves a specific project entry by its unique identifier.",
)
async def get_project(
    project_id: str,
    service: ProjectService = Depends(get_resume_service),
) -> Project:
    logger.info("Retrieving project entry", project_id=project_id)
    project = await service.get_project(project_id)
    if not project:
        logger.warning("Project entry not found", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project entry with id {project_id} not found",
        )
    return ProjectResponse.from_project(project)


@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="Get all project entries",
    description="Retrieves all project entries from database.",
)
async def get_all_projects(
    service: ProjectService = Depends(get_resume_service),
) -> list[ProjectResponse]:
    logger.info("Retrieving all project entries")
    projects = await service.get_all_projects()
    logger.info("Project entries retrieved", count=len(projects))
    return [ProjectResponse.from_project(project) for project in projects]


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project entry",
    description="Updates specific fields of a project entry and synchronizes changes with vector database.",
)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    service: ProjectService = Depends(get_resume_service),
) -> Project:
    logger.info("Updating project entry", project_id=project_id)
    existing_project = await service.get_project(project_id)
    if not existing_project:
        logger.warning("Cannot update non-existent project entry", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project entry with id {project_id} not found",
        )

    updated_data = ProjectItem(
        name=project_update.name if project_update.name is not None else existing_project.name,
        description=project_update.description if project_update.description is not None else existing_project.description,
        highlights=(
            project_update.highlights
            if project_update.highlights is not None
            else existing_project.highlights.split("|")
            if existing_project.highlights
            else None
        ),
        keywords=(
            project_update.keywords
            if project_update.keywords is not None
            else existing_project.keywords.split("|")
            if existing_project.keywords
            else None
        ),
        start_date=project_update.start_date if project_update.start_date is not None else existing_project.start_date,
        end_date=project_update.end_date if project_update.end_date is not None else existing_project.end_date,
        url=project_update.url if project_update.url is not None else existing_project.url,
        roles=(
            project_update.roles
            if project_update.roles is not None
            else existing_project.roles.split("|")
            if existing_project.roles
            else None
        ),
        entity=project_update.entity if project_update.entity is not None else existing_project.entity,
        type=project_update.type if project_update.type is not None else existing_project.type,
    )

    updated_project = await service.update_project(project_id, updated_data)
    logger.info("Project entry updated successfully", project_id=project_id)
    return ProjectResponse.from_project(updated_project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project entry",
    description="Deletes a project entry from both SQLite and ChromaDB.",
)
async def delete_project(
    project_id: str,
    service: ProjectService = Depends(get_resume_service),
):
    logger.info("Deleting project entry", project_id=project_id)
    deleted = await service.delete_project(project_id)
    if not deleted:
        logger.warning("Cannot delete non-existent project entry", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project entry with id {project_id} not found",
        )
    logger.info("Project entry deleted successfully", project_id=project_id)
    return None
