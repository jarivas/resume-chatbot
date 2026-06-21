import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.api.awards import router, get_db_session, get_resume_service
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
        from app.services import AwardService

        mock_chroma = MagicMock()
        mock_chroma.aadd_texts = AsyncMock()
        mock_chroma.adelete = AsyncMock()
        mock_embeddings = MagicMock()

        return AwardService(db_session, mock_chroma, mock_embeddings)

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_resume_service] = override_get_resume_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_awards_post_endpoint(test_client: AsyncClient):
    awards_data = {
        "title": "Best Developer Award",
        "date": "2023-12",
        "awarder": "Tech Corp",
        "summary": "Recognized for outstanding contributions",
    }

    response = await test_client.post("/awards", json=awards_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Best Developer Award"
    assert data["awarder"] == "Tech Corp"


@pytest.mark.asyncio
async def test_awards_get_by_id_endpoint(test_client: AsyncClient):
    awards_data = {
        "title": "Innovation Award",
        "awarder": "Startup Inc",
    }

    create_response = await test_client.post("/awards", json=awards_data)
    award_id = create_response.json()["id"]

    response = await test_client.get(f"/awards/{award_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == award_id
    assert data["title"] == "Innovation Award"


@pytest.mark.asyncio
async def test_awards_get_all_endpoint(test_client: AsyncClient):
    awards_data1 = {"title": "Award 1", "awarder": "Org 1"}
    awards_data2 = {"title": "Award 2", "awarder": "Org 2"}

    await test_client.post("/awards", json=awards_data1)
    await test_client.post("/awards", json=awards_data2)

    response = await test_client.get("/awards")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_awards_patch_endpoint(test_client: AsyncClient):
    awards_data = {
        "title": "Original Award",
        "awarder": "Original Org",
    }

    create_response = await test_client.post("/awards", json=awards_data)
    award_id = create_response.json()["id"]

    update_data = {
        "summary": "Updated summary",
    }

    response = await test_client.patch(f"/awards/{award_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Updated summary"


@pytest.mark.asyncio
async def test_awards_delete_endpoint(test_client: AsyncClient):
    awards_data = {
        "title": "Award to Delete",
        "awarder": "Test Org",
    }

    create_response = await test_client.post("/awards", json=awards_data)
    award_id = create_response.json()["id"]

    response = await test_client.delete(f"/awards/{award_id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_awards_get_not_found_endpoint(test_client: AsyncClient):
    response = await test_client.get("/awards/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_awards_patch_not_found_endpoint(test_client: AsyncClient):
    update_data = {"summary": "Test summary"}
    response = await test_client.patch("/awards/nonexistent-id", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_awards_delete_not_found_endpoint(test_client: AsyncClient):
    response = await test_client.delete("/awards/nonexistent-id")
    assert response.status_code == 404
