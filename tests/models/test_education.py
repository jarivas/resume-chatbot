import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.api.education import router, get_db_session, get_resume_service
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
async def test_create_education(test_client: AsyncClient):
    education_data = {
        "institution": "MIT",
        "area": "Computer Science",
        "study_type": "Bachelor",
        "start_date": "2018-09",
        "end_date": "2022-05",
        "score": "3.8",
        "courses": ["Data Structures", "Algorithms", "Machine Learning"],
    }

    response = await test_client.post("/education", json=education_data)

    assert response.status_code == 201
    data = response.json()
    assert data["institution"] == "MIT"
    assert data["area"] == "Computer Science"
    assert data["study_type"] == "Bachelor"
    assert "Data Structures" in data["courses"]


@pytest.mark.asyncio
async def test_get_education(test_client: AsyncClient):
    education_data = {
        "institution": "Stanford",
        "area": "AI",
        "study_type": "Master",
    }

    create_response = await test_client.post("/education", json=education_data)
    education_id = create_response.json()["id"]

    response = await test_client.get(f"/education/{education_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == education_id
    assert data["institution"] == "Stanford"


@pytest.mark.asyncio
async def test_get_all_education(test_client: AsyncClient):
    education_data1 = {"institution": "MIT", "area": "CS"}
    education_data2 = {"institution": "Stanford", "area": "AI"}

    await test_client.post("/education", json=education_data1)
    await test_client.post("/education", json=education_data2)

    response = await test_client.get("/education")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert any(edu["institution"] == "MIT" for edu in data)
    assert any(edu["institution"] == "Stanford" for edu in data)


@pytest.mark.asyncio
async def test_update_education(test_client: AsyncClient):
    education_data = {
        "institution": "MIT",
        "area": "CS",
    }

    create_response = await test_client.post("/education", json=education_data)
    education_id = create_response.json()["id"]

    update_data = {
        "area": "Computer Science",
        "score": "3.9",
    }

    response = await test_client.patch(f"/education/{education_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["area"] == "Computer Science"
    assert data["score"] == "3.9"


@pytest.mark.asyncio
async def test_delete_education(test_client: AsyncClient):
    education_data = {
        "institution": "MIT",
        "area": "CS",
    }

    create_response = await test_client.post("/education", json=education_data)
    education_id = create_response.json()["id"]

    response = await test_client.delete(f"/education/{education_id}")

    assert response.status_code == 204

    get_response = await test_client.get(f"/education/{education_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_education_not_found(test_client: AsyncClient):
    response = await test_client.get("/education/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_education_not_found(test_client: AsyncClient):
    update_data = {"area": "Computer Science"}
    response = await test_client.patch("/education/nonexistent-id", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_education_not_found(test_client: AsyncClient):
    response = await test_client.delete("/education/nonexistent-id")
    assert response.status_code == 404
