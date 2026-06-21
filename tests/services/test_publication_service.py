import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.db.models import Publication
from app.services import PublicationService

os.environ["OPENAI_API_KEY"] = ".


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Publication.metadata.create_all)

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
async def publication_service(db_session: AsyncSession, mock_chroma, mock_embeddings):
    return PublicationService(db_session, mock_chroma, mock_embeddings)


@pytest.mark.asyncio
async def test_publication_service_create(publication_service: PublicationService):
    from app.models import Publication as PublicationItem

    publication_data = PublicationItem(
        name="AI Research Paper",
        publisher="IEEE",
        release_date="2023-10",
        summary="Research on machine learning algorithms",
    )

    created_publication = await publication_service.create_publication(publication_data)

    assert created_publication is not None
    assert created_publication.name == "AI Research Paper"
    assert created_publication.publisher == "IEEE"


@pytest.mark.asyncio
async def test_publication_service_get(publication_service: PublicationService):
    from app.models import Publication as PublicationItem

    publication_data = PublicationItem(name="Research Article", publisher="Nature")
    created_publication = await publication_service.create_publication(publication_data)

    retrieved_publication = await publication_service.get_publication(created_publication.id)

    assert retrieved_publication is not None
    assert retrieved_publication.id == created_publication.id
    assert retrieved_publication.name == "Research Article"


@pytest.mark.asyncio
async def test_publication_service_get_all(publication_service: PublicationService):
    from app.models import Publication as PublicationItem

    await publication_service.create_publication(PublicationItem(name="Pub 1", publisher="Pub 1"))
    await publication_service.create_publication(PublicationItem(name="Pub 2", publisher="Pub 2"))

    all_publications = await publication_service.get_all_publications()

    assert len(all_publications) == 2


@pytest.mark.asyncio
async def test_publication_service_update(publication_service: PublicationService):
    from app.models import Publication as PublicationItem

    publication_data = PublicationItem(name="Original Publication", publisher="Original Publisher")
    created_publication = await publication_service.create_publication(publication_data)

    update_data = PublicationItem(
        name="Original Publication",
        publisher="Original Publisher",
        summary="Updated summary",
    )

    updated_publication = await publication_service.update_publication(created_publication.id, update_data)

    assert updated_publication is not None
    assert updated_publication.summary == "Updated summary"


@pytest.mark.asyncio
async def test_publication_service_delete(publication_service: PublicationService):
    from app.models import Publication as PublicationItem

    publication_data = PublicationItem(name="Publication to Delete", publisher="Test Publisher")
    created_publication = await publication_service.create_publication(publication_data)

    deleted = await publication_service.delete_publication(created_publication.id)

    assert deleted is True

    retrieved_publication = await publication_service.get_publication(created_publication.id)
    assert retrieved_publication is None


@pytest.mark.asyncio
async def test_publication_service_indexing(publication_service: PublicationService, mock_chroma):
    from app.models import Publication as PublicationItem

    publication_data = PublicationItem(name="Test Publication", publisher="Test Publisher")
    created_publication = await publication_service.create_publication(publication_data)

    assert mock_chroma.aadd_texts.called
    call_args = mock_chroma.aadd_texts.call_args
    assert len(call_args[0][0]) == 1
    assert "Test Publication" in call_args[0][0][0]


@pytest.mark.asyncio
async def test_publication_service_delete_indexing(publication_service: PublicationService, mock_chroma):
    from app.models import Publication as PublicationItem

    publication_data = PublicationItem(name="Test Publication", publisher="Test Publisher")
    created_publication = await publication_service.create_publication(publication_data)

    await publication_service.delete_publication(created_publication.id)

    assert mock_chroma.adelete.called
    call_args = mock_chroma.adelete.call_args
    assert f"publication_{created_publication.id}" in call_args[0][0]
