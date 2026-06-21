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
        from app.services import SkillService

        mock_chroma = MagicMock()
        mock_chroma.aadd_texts = AsyncMock()
        mock_chroma.adelete = AsyncMock()
        mock_embeddings = MagicMock()

        return SkillService(db_session, mock_chroma, mock_embeddings)

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_resume_service] = override_get_resume_service

    async with AsyncClient(ress=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_skills_post_endpoint(test_client: AsyncClient):
    skills_data = {
        "name": "Python",
        "level": "Expert",
        "keywords": ["programming", "development"],
    }

    response = await test_client.post("/skills", json=skills_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Python"
    assert data["level"] == "Expert"


@pytest.mark.asyncio
async def test_skills_get_by_id_endpoint(test_client: AsyncClient):
    skills_data = {"name": "Python", "level": "Expert"}

    create_response = await test_client.post("/skills", json=skills_data)
    skill_id = create_response.json()["id"]

    response = await test_client.get(f"/skills/{skill_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == skill_id
    assert data["name"] == "Python"


@pytest.mark.asyncio
async def test_skills_get_all_endpoint(test_client: AsyncClient):
    skills_data1 = {"name": "Python", "level": "Expert"}
    skills_data2 = {"name": "JavaScript", "level": "Intermediate"}

    await test_client.post("/skills", json=skills_data1)
    await test_client.post("/skills", json=skills_data2)

    response = await test_client.get("/skills")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_skills_patch_endpoint(test_client: AsyncClient):
    skills_data = {"name": "Python", "level": "Intermediate"}

    create_response = await test_client.post("/skills", json=skills_data)
    skill_id = create_response.json()["id"]

    update_data = {"level": "Expert"}

    response = await test_client.patch(f"/skills/{skill_id}", json=update_data)

    assert response.status_code == 200
    data = response response.json()
    assert data["level"] == "Expert"


@pytest.mark.asyncio
async def test_skills_delete_endpoint(test_client: AsyncClient):
    skills_data = {"name": "Python", "level": "Expert"}

    create_response = await test_client.post("/skills", json=skills_data)
    skill_id = create_response.json()["id"]

    response = await test_client.delete(f"/skills/{skill_id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_skills_get_not_found_endpoint(test_client: AsyncClient):
    response = await test_client.get("/skills/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_skills_patch_not_found_endpoint(test_client: AsyncClient):
    update_data = {"level": "Expert"}
    response = await test_client.patch("/skills/nonexistent-id", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_skills_delete_not_found_endpoint(test_client: AsyncClient):
    response = await test_client.delete("/skills/nonexistent-id")
    assert response.status_code == 404
