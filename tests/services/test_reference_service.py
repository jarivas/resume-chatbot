import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.db.models import Reference
from app.services import ReferenceService

os.environ["OPENAI_API_KEY"] = "test_key"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Reference.metadata.create_all)

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
async def reference_service(db_session: AsyncSession, mock_chroma, mock_embeddings):
    return ReferenceService(db_session, mock_chroma, mock_embeddings)


@pytest.mark.asyncio
async def test_reference_service_create(reference_service: ReferenceService):
    from app.models import Reference as ReferenceItem

    reference_data = ReferenceItem(
        name="John Doe",
        reference="Excellent developer with strong problem-solving skills",
    )

    created_reference = await reference_service.create_reference(reference_data)

    assert created_reference is not None
    assert created_reference.name == "John Doe"
    assert "developer" in created_reference.reference.lower()


@pytest.mark.asyncio
async def test_reference_service_get(reference_service: ReferenceService):
    from app.models import Reference as ReferenceItem

    reference_data = ReferenceItem(name="Jane Smith", reference="Great team player")
    created_reference = await reference_service.create_reference(reference_data)

    retrieved_reference = await reference_service.get_reference(created_reference.id)

    assert retrieved_reference is not None
    assert retrieved_reference.id == created_reference.id
    assert retrieved_reference.name == "Jane Smith"


@pytest.mark.asyncio
async def test_reference_service_get_all(reference_service: ReferenceService):
    from app.models import Reference as ReferenceItem

    await reference_service.create_reference(ReferenceItem(name="Ref 1", reference="Text 1"))
    await reference_service.create_reference(ReferenceItem(name="Ref 2", reference="Text 2"))

    all_references = await reference_service.get_all_references()

    assert len(all_references) == 2


@pytest.mark.asyncio
async def test_reference_service_update(reference_service: ReferenceService):
    from app.models import Reference as ReferenceItem

    reference_data = ReferenceItem(name="Original Reference", reference="Original text")
    created_reference = = await reference_service.create_reference(reference_data)

    update_data = ReferenceItem(
        name="Original Reference",
        reference="Updated reference text",
    )

    updated_reference = await reference_service.update_reference(created_reference.id, update_data)

    assert updated_reference is not None
    assert "Updated" in updated_reference.reference


@pytest.mark.asyncio
async def test_reference_service_delete(reference_service: ReferenceService):
    from app.models import Reference as ReferenceItem

    reference_data = ReferenceItem(name="Reference to Delete", reference="Test reference")
    created_reference = await reference_service.create_reference(reference_data)

    deleted = await reference_service.delete_reference(created_reference.id)

    assert deleted is True

    retrieved_reference = await reference_service.get_reference(created_reference.id)
    assert retrieved_reference is None


@pytest.mark.asyncio
async def test_reference_service_indexing(reference_service: ReferenceService, mock_chroma):
    from app.models import Reference as ReferenceItem

    reference_data = ReferenceItem(name="Test Reference", reference="Test reference")
    created_reference = await reference_service.create_reference(reference_data)

    assert mock_chroma.aadd_texts.called
    call_args = mock_chroma.aadd_texts.call_args
    assert len(call_args[0][0]) == 1
    assert "Test Reference" in call_args[0][0][0]


@pytest.mark.asyncio
async def test_reference_service_delete_indexing(reference_service: ReferenceService, mock_chroma):
    from app.models import Reference as ReferenceItem

    reference_data = ReferenceItem(name="Test Reference", reference="Test reference")
    created_reference = await reference_service.create_reference(reference_data)

    await reference_service.delete_reference(created_reference.id)

    assert mock_chroma.adelete.called
    call_args = mock_chroma.adelete.call_args
    assert f"reference_{created_reference.id}" in call_args[0][0]
