import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.api.volunteer import router, get_db_session, get_resume_service
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
        from app.services import VolunteerService

        mock_chroma = MagicMock()
        mock_chroma.aadd_texts = AsyncMock()
        mock_chroma.adelete = AsyncMock()
        mock_embeddings = MagicMock()

        return VolunteerService(db_session, mock_chroma, mock_embeddings)

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_resume_service] = override_get_resume_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_volunteer_post_endpoint(test_client: AsyncClient):
    volunteer_data = {
        "organization": "Red Cross",
        "position": "Volunteer",
        "summary": "Helped with community events",
        "highlights": ["Organized events", "Helped people"],
    }

    response = await test_client.post("/volunteer", json=volunteer_data)

    assert response.status_code == 201
    data = response.json()
    assert data["organization"] == "Red Cross"
    assert data["position"] == "Volunteer"


@pytest.mark.asyncio
async def test_volunteer_get_by_id_endpoint(test_client: AsyncClient):
    volunteer_data = {"organization": "Red Cross", "position": "Volunteer"}

    create_response = await test_client.post("/volunteer", json=volunteer_data)
    volunteer_id = create_response.json()["id"]

    response = await test_client.get(f"/volunteer/{volunteer_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == volunteer_id
    assert data["organization"] == "Red Cross"


@pytest.mark.asyncio
async def test_volunteer_get_all_endpoint(test_client: AsyncClient):
    volunteer_data1 = {"organization": "Red Cross", "position": "Volunteer"}
    volunteer_data2 = {"organization": "Green Peace", "position": "Activist"}

    await test_client.post("/volunteer", json=volunteer_data1)
    await test_client.post("/volunteer", json=volunteer_data2)

    response = await test_client.get("/volunteer")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_volunteer_patch_endpoint(test_client: AsyncClient):
    volunteer_data = {"organization": "Red Cross", "position": "Volunteer"}

    create_response = await test_client.post("/volunteer", json=volunteer_data)
    volunteer_id = create_response.json()["id"]

    update_data = {"position": "Senior Volunteer"}

    response = await test_client.patch(f"/volunteer/{volunteer_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["position"] == "Senior Volunteer"


@pytest.mark.asyncio
async def test_volunteer_delete_endpoint(test_client: AsyncClient):
    volunteer_data = {"organizationvolunteer": "Red Cross", "position": "Volunteer"}

    create_response = await test_client.post("/volunteer", json=volunteer_data)
    volunteer_id = create_response.json()["id"]

    response = await test_client.delete(f"/volunteer/{volunteer_id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_volunteer_get_not_found_endpoint(test_client: AsyncClient):
    response = await test_client.get("/volunteer/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_volunteer_patch_not_found_endpoint(test_client: AsyncClient):
    update_data = {"position": "Senior Volunteer"}
    response = await test_client.patch("/volunteer/nonexistent-id", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_volunteer_delete_not_found_endpoint(test_client: AsyncClient):
    response = await test_client.delete("/volunteer/nonexistent-id")
    assert response.status_code == 404
