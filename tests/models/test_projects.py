import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.api.projects import router, get_db_session, get_resume_service
from app.db.models import Base

os.environ["OPENAI_API_KEY"] = "test_key"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def test_client(db_session: AsyncSession):
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    async def override_get_db_session():
        return db_session

    async def override_get_resume_service():
        from app.services import ProjectService

        mock_chroma = MagicMock()
        mock_chroma.aadd_texts = AsyncMock()
        mock_chroma.adelete = AsyncMock()
        mock_embeddings = MagicMock()

        return ProjectService(db_session, mock_chroma, mock_embeddings)

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_resume_service] = override_get_resume_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_project(test_client: AsyncClient):
    project_data = {
        "name": "AI Chatbot",
        "description": "Intelligent conversational AI",
        "entity": "Personal",
        "type": "Software",
        "keywords": ["AI", "NLP", "Python"],
    }

    response = await test_client.post("/projects", json=project_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "AI Chatbot"
    assert data["entity"] == "Personal"


@pytest.mark.asyncio
async def test_get_project(test_client: AsyncClient):
    project_data = {
        "name": "Web App",
        "entity": "Company",
        "type": "Web",
    }

    create_response = await test_client.post("/projects", json=project_data)
    project_id = create_response.json()["id"]

    response = await test_client.get(f"/projects/{project_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "Web App"


@pytest.mark.asyncio
async def test_get_all_projects(test_client: AsyncClient):
    project_data1 = {"name": "Project 1", "entity": "Personal"}
    project_data2 = {"name": "Project 2", "entity": "Work"}

    await test_client.post("/projects", json=project_data1)
    await test_client.post("/projects", json=project_data2)

    response = await test_client.get("/projects")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(proj["name"] == "Project 1" for proj in data)


@pytest.mark.asyncio
async def test_update_project(test_client: AsyncClient):
    project_data = {
        "name": "Original Project",
        "entity": "Personal",
    }

    create_response = await test_client.post("/projects", json=project_data)
    project_id = create_response.json()["id"]

    update_data = {
        "description": "Updated description",
        "type": "Mobile",
    }

    response = await test_client.patch(f"/projects/{project_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description"
    assert data["type"] == "Mobile"


@pytest.mark.asyncio
async def test_delete_project(test_client: AsyncClient):
    project_data = {
        "name": "Project to Delete",
        "entity": "Test",
    }

    create_response = await test_client.post("/projects", json=project_data)
    project_id = create_response.json()["id"]

    response = await test_client.delete(f"/projects/{project_id}")

    assert response.status_code == 204

    get_response = await test_client.get(f"/projects/{project_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio

async def test_get_project_not_found(test_client: AsyncClient):
    response = await test_client.get("/projects/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project_not_found(test_client: AsyncClient):
    update_data = {"description": "Test"}
    response = await test_client.patch("/projects/nonexistent-id", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_found(test_client: AsyncClient):
    response = await test_client.delete("/projects/nonexistent-id")
    assert response.status_code == 404
