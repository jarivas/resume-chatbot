import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.api.interests import router, get_db_session, get_resume_service
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
        from app.services import InterestService

        mock_chroma = MagicMock()
        mock_chroma.aadd_texts = AsyncMock()
        mock_chroma.adelete = AsyncMock()
        mock_embeddings = MagicMock()

        return InterestService(db_session, mock_chroma, mock_embeddings)

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_resume_service] = override_get_resume_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_interests_post_endpoint(test_client: AsyncClient):
    interests_data = {
        "name": "Machine Learning",
        "keywords": ["AI", "Deep Learning", "Neural Networks"],
    }

    response = await test_client.post("/interests", json=interests_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Machine Learning"
    assert "AI" in data["keywords"]


@pytest.mark.asyncio
async def test_interests_get_by_id_endpoint(test_client: AsyncClient):
    interests_data = {
        "name": "Web Development",
        "keywords": ["JavaScript", "React"],
    }

    create_response = await test_client.post("/interests", json=interests_data)
    interest_id = create_response.json()["id"]

    response = await test_client.get(f"/interests/{interest_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == interest_id
    assert data["name"] == "Web Development"


@pytest.mark.asyncio
async def test_interests_get_all_endpoint(test_client: AsyncClient):
    interests_data1 = {"name": "AI", "keywords": ["Machine Learning"]}
    interests_data2 = {"name": "Web", "keywords": ["Frontend"]}

    await test_client.post("/interests", json=interests_data1)
    await test_client.post("/interests", json=interests_data2)

    response = await test_client.get("/interests")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_interests_patch_endpoint(test_client: AsyncClient):
    interests_data = {
        "name": "Programming",
        "keywords": ["Python"],
    }

    create_response = await test_client.post("/interests", json=interests_data)
    interest_id = create_response.json()["id"]

    update_data = {
        "keywords": ["Python", "JavaScript", "Go"],
    }

    response = await test_client.patch(f"/interests/{interest_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert "Python" in data["keywords"]
    assert "JavaScript" in data["keywords"]


@pytest.mark.asyncio
async def test_interests_delete_endpoint(test_client: AsyncClient):
    interests_data = {
        "name": "Test Interest",
        "keywords": ["Test"],
    }

    create_response = await test_client.post("/interests", json=interests_data)
    interest_id = create_response.json()["id"]

    response = await test_client.delete(f"/interests/{interest_id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_interests_get_not_found_endpoint(test_client: AsyncClient):
    response = await test_client.get("/interests/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_interests_patch_not_found_endpoint(test_client: AsyncClient):
    update_data = {"keywords": ["Test"]}
    response = await test_client.patch("/interests/nonexistent-id", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_interests_delete_not_found_endpoint(test_client: AsyncClient):
    response = await test_client.delete("/interests/nonexistent-id")
    assert response.status_code == 404
