import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.api.references import router, get_db_session, get_resume_service
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
        from app.services import ReferenceService

        mock_chroma = MagicMock()
        mock_chroma.aadd_texts = AsyncMock()
        mock_chroma.adelete = AsyncMock()
        mock_embeddings = MagicMock()

        return ReferenceService(db_session, mock_chroma, mock_embeddings)

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_resume_service] = override_get_resume_service

    async with (transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_create_reference(test_client: AsyncClient):
    reference_data = {
        "name": "John Doe",
        "reference": "Excellent developer with strong problem-solving skills",
    }

    response = await test_client.post("/references", json=reference_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert "developer" in data["reference"].lower()


@pytest.mark.asyncio
async def test_get_reference(test_client: AsyncClient):
    reference_data = {
        "name": "Jane Smith",
        "reference": "Great team player",
    }

    create_response = await test_client.post("/references", json=reference_data)
    reference_id = create_response.json()["id"]

    response = await test_client.get(f"/references/{reference_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == reference_id
    assert data["name"] == "Jane Smith"


@pytest.mark.asyncio
async def test_get_all_references(test_client: AsyncClient):
    reference_data1 = {"name": "Ref 1", "reference": "Text 1"}
    reference_data2 = {"name": "Ref 2", "reference": "Text 2"}

    await test_client.post("/references", json=reference_data1)
    await test_client.post("/references", json=reference_data2)

    response = await test_client.get("/references")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(ref["name"] == "Ref 1" for ref in data)


@pytest.mark.asyncio
async def test_update_reference(test_client: AsyncClient):
    reference_data = {
        "name": "Original Reference",
        "reference": "Original text",
    }

    create_response = await test_client.post("/references", json=reference_data)
    reference_id = create_response.json()["id"]

    update_data = {
        "reference": "Updated reference text",
    }

    response = await test_client.patch(f"/references/{reference_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert "Updated" in data["reference"]


@pytest.mark.asyncio
async def test_delete_reference(test_client: AsyncClient):
    reference_data = {
        "name": "Reference to Delete",
        "reference": "Test reference",
    }

    create_response = await test_client.post("/references", json=reference_data)
    reference_id = create_response.json()["id"]

    response = await test_client.delete(f"/references/{reference_id}")

    assert response.status_code == 204

    get_response = await test_client.get(f"/references/{reference_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_reference_not_found(test_client: AsyncClient):
    response = await test_client.get("/references/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_reference_not_found(test_client: AsyncClient):
    update_data = {"reference": "Test"}
    response = await test_client.patch("/references/nonexistent-id", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_reference_not_found(test_client: AsyncClient):
    response = await test_client.delete("/references/nonexistent-id")
    assert response.status_code == 404
