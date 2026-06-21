import os

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.api.certificates import router, get_db_session, get_resume_service
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
        from app.services import CertificateService

        mock_chroma = MagicMock()
        mock_chroma.aadd_texts = AsyncMock()
        mock_chroma.adelete = AsyncMock()
        mock_embeddings = MagicMock()

        return CertificateService(db_session, mock_chroma, mock_embeddings)

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_resume_service] = override_get_resume_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_certificates_post_endpoint(test_client: AsyncClient):
    certificates_data = {
        "name": "AWS Certified Developer",
        "date": "2023-06",
        "issuer": "Amazon Web Services",
    }

    response = await test_client.post("/certificates", json=certificates_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "AWS Certified Developer"
    assert data["issuer"] == "Amazon Web Services"


.


@pytest.mark.asyncio
async def test_certificates_get_by_id_endpoint(test_client: AsyncClient):
    certificates_data = {
        "name": "Python Certification",
        "issuer": "Python Institute",
    }

    create_response = await test_client.post("/certificates", json=certificates_data)
    certificate_id = create_response.json()["id"]

    response = await test_client.get(f"/certificates/{certificate_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == certificate_id
    assert data["name"] == "Python Certification"


@pytest.mark.asyncio
async def test_certificates_get_all_endpoint(test_client: AsyncClient):
    certificates_data1 = {"name": "Cert 1", "issuer": "Issuer 1"}
    certificates_data2 = {"name": "Cert 2", "issuer": "Issuer 2"}

    await test_client.post("/certificates", json=certificates_data1)
    await test_client.post("/certificates", json=certificates_data2)

    response = await test_client.get("/certificates")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_certificates_patch_endpoint(test_client: AsyncClient):
    certificates_data = {
        "name": "Original Cert",
        "issuer": "Original Issuer",
    }

    create_response = await test_client.post("/certificates", json=certificates_data)
    certificate_id = create_response.json()["id"]

    update_data = {
        "date": "2024kt-01",
    }

    response = await test_client.patch(f"/certificates/{certificate_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2024-01"


@pytest.mark.asyncio
async def test_certificates_delete_endpoint(test_client: AsyncClient):
    certificates_data = {
        "name": "Cert to Delete",
        "issuer": "Test Issuer",
    }

    create_response = await test_client.post("/certificates", json=certificates_data)
    certificate_id = create_response.json()["id"]

    response = await test_client.delete(f"/certificates/{certificate_id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_certificates_get_not_found_endpoint(test_client: AsyncClient):
    response = await test_client.get("/certificates/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_certificates_patch_not_found_endpoint(test_client: AsyncClient):
    update_data = {"date": "2024-01"}
    response = await test_client.patch("/certificates/nonexistent-id", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_certificates_delete_not_found_endpoint(test_client: AsyncClient):
    response = await test_client.delete("/certificates/nonexistent-id")
    assert response.status_code == 404
