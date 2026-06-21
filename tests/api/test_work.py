import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.api.work import router, get_db_session, get_resume_service
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
        from app.services import WorkService

        mock_chroma = MagicMock()
        mock_chroma.aadd_texts = AsyncMock()
        mock_chroma.adelete = AsyncMock()
        mock_embeddings = MagicMock()

        return WorkService(db_session, mock_chroma, mock_embeddings)

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_resume_service] = override_get_resume_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_work_post_endpoint(test_client: AsyncClient):
    work_data = {
        "name": "Tech Corp",
        "position": "Software Engineer",
        "summary": "Developed amazing software",
        "highlights": ["Increased efficiency by 50%", "Led team of 5"],
    }

    response = await test_client.post("/work", json=work_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tech Corp"
    assert data["position"] == "Software Engineer"


@pytest.mark.asyncio
async def test_work_get_by_id_endpoint(test_client: AsyncClient):
    work_data = {"name": "Tech Corp", "position": "Software Engineer"}

    create_response = await test_client.post("/work", json=work_data)
    work_id = create_response.json()["id"]

    response = await test_client.get(f"/work/{work_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == work_id
    assert data["name"] == "Tech Corp"


@pytest.mark.asyncio
async def test_work_get_all_endpoint(test_client: AsyncClient):
    work_data1 = {"name": "Tech Corp", "position": "Software Engineer"}
    work_data2 = {"name": "Startup Inc", "position": "CTO"}

    await test_client.post("/work", json=work_data1)
    await test_client.post("/work", json=work_data2)

    response = await test_client.get("/work")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_work_patch_endpoint(test_client: AsyncClient):
    work_data = {"name": "Tech Corp", "position": "Software Engineer"}

    create_response = await test_client.post("/work", json=work_data)
    work_id = create_response.json()["id"]

    update_data = {"position": "Senior Software Engineer"}

    response = await test_client.patch(f"/work/{work_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["position"] == "Senior Software Engineer"


@pytest.mark.asyncio
async def test_work_delete_endpoint(test_client: AsyncClient):
    work_data = {"name": "Tech Corp", "position": "Software Engineer"}

    create_response = await test_client.post("/work", json=work_data)
    work_id = create_response.json()["id"]

    response = await test_client.delete(f"/work/{work_id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_work_get_not_found_endpoint(test_client: AsyncClient):
    response = await test_client.get("/work/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_work_patch_not_found_endpoint(test_client: AsyncClient):
    update_data = {"position": "Senior Software Engineer"}
    response = await test_client.patch("/work/nonexistent-id", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_work_delete_not_found_endpoint(test_client: AsyncClient):
    response = await test_client.delete("/work/nonexistent-id")
    assert response.status_code == 404
