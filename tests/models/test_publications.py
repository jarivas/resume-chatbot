import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.api.publications import router, get_db_session, get_resume_service
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
        from app.services import PublicationService

        mock_chroma = MagicMock()
        mock_chroma.aadd_texts = AsyncMock()
        mock_chroma.adelete = AsyncMock()
        mock_embeddings = MagicMock()

        return PublicationService(db_session, mock_chroma, mock_embeddings)

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_resume_service] = override_get_resume_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_publication(test_client: AsyncClient):
    publication_data = {
        "name": "AI Research Paper",
        "publisher": "IEEE",
        "release_date": "2023-10",
        "summary": "Research on machine learning algorithms",
    }

    response = await test_client.post("/publications", json=publication_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "AI Research Paper"
    assert data["publisher"] == "IEEE"


@pytest.mark.asyncio
async def test_get_publication(test_client: AsyncClient):
    publication_data = {
        "name": "Research Article",
        "publisher": "Nature",
    }

    create_response = await test_client.post("/publications", json=publication_data)
    publication_id = create_response.json()["id"]

    response = await test_client.get(f"/publications/{publication_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == publication_id
    assert data["name"] == "Research Article"


@pytest.mark.asyncio
async def test_get_all_publications(test_client: AsyncClient):
    publication_data1 = {"name": "Pub 1", "publisher": "Pub 1"}
    publication_data2 = {"name": "Pub 2", "publisher": "Pub 2"}

    await test_client.post("/publications", json=publication_data1)
    await test_client.post("/publications", json=publication_data2)

    response = await test_client.get("/publications")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(pub["name"] == "Pub 1" for pub in data)


@pytest.mark.asyncio
async def test_update_publication(test_client: AsyncClient):
    publication_data = {
        "name": "Original Publication",
        "publisher": "Original Publisher",
    }

    create_response = await test_client.post("/publications", json=publication_data)
    publication_id = create_response.json()["id"]

    update_data = {
        "summary": "Updated summary",
    }

    response = await test_client.patch(f"/publications/{publication_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Updated summary"


@pytest.mark.asyncio
async def test_delete_publication(test_client: AsyncClient):
    publication_data = {
        "name": "Publication to Delete",
        "publisher": "Test Publisher",
    }

    create_response = await test_client.post("/publications", json=publication_data)
    publication_id = create_response.json()["id"]

    response = await test_client.delete(f"/publications/{publication_id}")

    assert response.status_code == 204

    get_response = await test_client.get(f"/publications/{publication_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_publication_not_found(test_client: AsyncClient):
    response = await test_client.get("/publications/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_publication_not_found(test_client: AsyncClient):
    update_data = {"summary": "Test summary"}
    response = awaitares test_client.patch("/publications/nonexistent-id", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_publication_not_found(test_client: AsyncClient):
    response = await test_client.delete("/publications/nonexistent-id")
    assert response.status_code == 404
