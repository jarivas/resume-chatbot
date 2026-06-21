import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.db.models import Project
from app.services import ProjectService

os.environ["OPENAI_API_KEY"] = "test_key"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Project.metadata.create_all)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def mock_chroma():
    mock_chroma = MagicMock()
    mock_chroma.aadd_texts = AsyncMock()
    mock_chroma.adelete = AsyncMock()
    return mock_chroma


@pytest_asyncio.fixture
async def mock_embeddings():
    return MagicMock()


@pytest_asyncio.fixture
async def project_service(db_session: AsyncSession, mock_chroma, mock_embeddings):
    return ProjectService(db_session, mock_chroma, mock_embeddings)


@pytest.mark.asyncio
async def test_project_service_create(project_service: ProjectService):
    from app.models import Project as ProjectItem

    project_data = ProjectItem(
        name="AI Chatbot",
        description="Intelligent conversational AI",
        entity="Personal",
        type="Software",
        keywords=["AI", "NLP", "Python"],
    )

    created_project = await project_service.create_project(project_data)

    assert created_project is not None
    assert created_project.name == "AI Chatbot"
    assert created_project.entity == "Personal"


@pytest.mark.asyncio
async def test_project_service_get(project_service: ProjectService):
    from app.models import Project as ProjectItem

    project_data = ProjectItem(name="Web App", entity="Company", type="Web")
    created_project = await project_service.create_project(project_data)

    retrieved_project = await project_service.get_project(created_project.id)

    assert retrieved_project is not None
    assert retrieved_project.id == created_project.id
    assert retrieved_project.name == "Web App"


@pytest.mark.asyncio
async def test_project_service_get_all(project_service: ProjectService):
    from app.models import Project as ProjectItem

    await project_service.create_project(ProjectItem(name="Project 1", entity="Personal"))
    await project_service.create_project(ProjectItem(name="Project 2", entity="Work"))

    all_projects = await project_service.get_all_projects()

    assert len(all_projects) == 2


@pytest.mark.asyncio
async def test_project_service_update(project_service: ProjectService):
    from app.models import Project as ProjectItem

    project_data = ProjectItem(name="Original Project", entity="Personal")
    created_project = await project_service.create_project(project_data)

    update_data = ProjectItem(
        name="Original Project",
        entity="Personal",
        description="Updated description",
        type="Mobile",
    )

    updated_project = await project_service.update_project(created_project.id, update_data)

    assert updated_project is not None
    assert updated_project.description == "Updated description"
    assert updated_project.type == "Mobile"


@pytest.mark.asyncio
async def test_project_service_delete(project_service: ProjectService):
    from app.models import Project as ProjectItem

    project_data = ProjectItem(name="Project to Delete", entity="Test")
    created_project = await project_service.create_project(project_data)

    deleted = await project_service.delete_project(created_project.id)

    assert deleted is True

    retrieved_project = await project_service.get_project(created_project.id)
    assert retrieved_project is None


@pytest.mark.asyncio
async def test_project_service_indexing(project_service: ProjectService, mock_chroma):
    from app.models import Project as ProjectItem

    project_data = ProjectItem(name="Test Project", entity="Personal")
    created_project = await project_service.create_project(project_data)

    assert mock_chroma.aadd_texts.called
    call_args = mock_chroma.aadd_texts.call_args
    assert len(call_args[0][0]) == 1
    assert "Test Project" in call_args[0][0][0]


@pytest.mark.asyncio
async def test_project_service_delete_indexing(project_service: ProjectService, mock_chroma):
    from app.models import Project as ProjectItem

    project_data = ProjectItem(name="Test Project", entity="Personal")
    created_project = await project_service.create_project(project_data)

    await project_service.delete_project(created_project.id)

    assert mock_chroma.adelete.called
    call_args = mock_chroma.adelete.call_args
    assert f"project_{created_project.id}" in call_args[0][0]
