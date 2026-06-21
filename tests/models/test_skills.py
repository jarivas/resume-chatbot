import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.api.skills import router, get_db_session, get_resume_service
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
        from app.services.cv_service import ResumeService

        mock_chroma = MagicMock()
        mock_chroma.aadd_texts = AsyncMock()
        mock_chroma.adelete = AsyncMock()
        mock_embeddings = MagicMock()

        return ResumeService(db_session, mock_chroma, mock_embeddings)

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_resume_service] = override_get_resume_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_skill(test_client: AsyncClient):
    skill_data = {
        "name": "Python",
        "level": "Expert",
        "keywords": ["programming", "development", "scripting"],
    }

    response = await test_client.post("/skills", json=skill_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Python"
    assert data["level"] == "Expert"
    assert "programming" in data["keywords"]


@pytest.mark.asyncio
async def test_get_skill(test_client: AsyncClient):
    skill_data = {
        "name": "FastAPI",
        "level": "Advanced",
    }

    create_response = await test_client.post("/skills", json=skill_data)
    skill_id = create_response.json()["id"]

    response = await test_client.get(f"/skills/{skill_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == skill_id
    assert data["name"] == "FastAPI"


@pytest.mark.asyncio
async def test_get_all_skills(test_client: AsyncClient):
    skill_data1 = {"name": "Python", "level": "Expert"}
    skill_data2 = {"name": "JavaScript", "level": "Intermediate"}

    await test_client.post("/skills", json=skill_data1)
    await test_client.post("/skills", json=skill_data2)

    response = await test_client.get("/skills")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(skill["name"] == "Python" for skill in data)
    assert any(skill["name"] == "JavaScript" for skill in data)


@pytest.mark.asyncio
async def test_update_skill(test_client: AsyncClient):
    skill_data = {
        "name": "Python",
        "level": "Intermediate",
    }

    create_response = await test_client.post("/skills", json=skill_data)
    skill_id = create_response.json()["id"]

    update_data = {
        "level": "Expert",
        "keywords": ["programming", "development"],
    }

    response = await test_client.patch(f"/skills/{skill_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["level"] == "Expert"
    assert "programming" in data["keywords"]


@pytest.mark.asyncio
async def test_delete_skill(test_client: AsyncClient):
    skill_data = {
        "name": "Python",
        "level": "Expert",
    }

    create_response = await test_client.post("/skills", json=skill_data)
    skill_id = create_response.json()["id"]

    response = await test_client.delete(f"/skills/{skill_id}")

    assert response.status_code == 204

    get_response = await test_client.get(f"/skills/{skill_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_skill_not_found(test_client: AsyncClient):
    response = await test_client.get("/skills/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_skill_not_found(test_client: AsyncClient):
    update_data = {"level": "Expert"}
    response = await test_client.patch("/skills/nonexistent-id", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_skill_not_found(test_client: AsyncClient):
    response = await test_client.delete("/skills/nonexistent-id")
    assert response.status_code == 404
