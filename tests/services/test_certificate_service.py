import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.db.models import Certificate
from app.services import CertificateService

os.environ["OPENAI_API_KEY"] = "test_key"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Certificate.metadata.create_all)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def mock_chroma():
    mock_chroma = MagicMock()
    mock_chroma.aadd_texts = AsyncMock()
    mock_chroma.adelete = AsyncMock()
    return mock_chroma


@pytest_asyncio.fixture
async def mock_embeddings():
    return MagicMock()


@pytest_asyncio.fixture
async def certificate_service(db_session: AsyncSession, mock_chroma, mock_embeddings):
    return CertificateService(db_session, mock_chroma, mock_embeddings)


@pytest.mark.asyncio
async def test_certificate_service_create(certificate_service: CertificateService):
    from app.models import Certificate as CertificateItem

    certificate_data = CertificateItem(
        name="AWS Certified Developer",
        date="2023-06",
        issuer="Amazon Web Services",
    )

    created_certificate = await certificate_service.create_certificate(certificate_data)

    assert created_certificate is not None
    assert created_certificate.name == "AWS Certified Developer"
    assert created_certificate.issuer == "Amazon Web Services"


@pytest.mark.asyncio
async def test_certificate_service_get(certificate_service: CertificateService):
    from app.models import Certificate as CertificateItem

    certificate_data = CertificateItem(name="Python Certification", issuer="Python Institute")
    created_certificate = await certificate_service.create_certificate(certificate_data)

    retrieved_certificate = await certificate_service.get_certificate(created_certificate.id)

    assert retrieved_certificate is not None
    assert retrieved_certificate.id == created_certificate.id
    assert retrieved_certificate.name == "Python Certification"


@pytest.mark.asyncio
async def test_certificate_service_get_all(certificate_service: CertificateService):
    from app.models import Certificate as CertificateItem

    await certificate_service.create_certificate(CertificateItem(name="Cert 1", issuer="Issuer 1"))
    await certificate_service.create_certificate(CertificateItem(name="Cert 2", issuer="Issuer 2"))

    all_certificates = await certificate_service.get_all_certificates()

    assert len(all_certificates) == 2


@pytest.mark.asyncio
async def test_certificate_service_update(certificate_service: CertificateService):
    from app.models import Certificate as CertificateItem

    certificate_data = CertificateItem(name="Original Cert", issuer="Original Issuer")
    created_certificate = await certificate_service.create_certificate(certificate_data)

    update_data = CertificateItem(
        name="Original Cert",
        issuer="Original Issuer",
        date="2024-01",
    )

    updated_certificate = await certificate_service.update_certificate(created_certificate.id, update_data)

    assert updated_certificate is not None
    assert updated_certificate.date == "2024-01"


@pytest.mark.asyncio
async def test_certificate_service_delete(certificate_service: CertificateService):
    from app.models import Certificate as CertificateItem

    certificate_data = CertificateItem(name="Cert to Delete", issuer="Test Issuer")
    created_certificate = await certificate_service.create_certificate(certificate_data)

    deleted = await certificate_service.delete_certificate(created_certificate.id)

    assert deleted is True

    retrieved_certificate = await certificate_service.get_certificate(created_certificate.id)
    assert retrieved_certificate is None


@pytest.mark.asyncio
async def test_certificate_service_indexing(certificate_service: CertificateService, mock_chroma):
    from app.models import Certificate as CertificateItem

    certificate_data = CertificateItem(name="Test Cert", issuer="Test Issuer")
    created_certificate = await certificate_service.create_certificate(certificate_data)

    assert mock_chroma.aadd_texts.called
    call_args = mock_chroma.aadd_texts.call_args
    assert len(call_args[0][0]) == 1
    assert "Test Cert" in call_args[0][0][0]


@pytest.mark.asyncio
async def test_certificate_service_delete_indexing(certificate_service: CertificateService, mock_chroma):
    from app.models import Certificate as CertificateItem

    certificate_data = CertificateItem(name="Test Cert", issuer="Test Issuer")
    created_certificate = await certificate_service.create_certificate(certificate_data)

    await certificate_service.delete_certificate(created_certificate.id)

    assert mock_chroma.adelete.called
    call_args = mock_chroma.adelete.call_args
    assert f"certificate_{created_certificate.id}" in call_args[0][0]
