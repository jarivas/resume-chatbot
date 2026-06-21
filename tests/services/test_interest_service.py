import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.db.models import Interest
from app.services import InterestService

os.environ["OPENAI_API_KEY"] = "test_key"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Interest.metadata.create_all)

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
async def interest_service(db_session: AsyncSession, mock_chroma, mock_embeddings):
    return InterestService(db_session, mock_chroma, mock_embeddings)


@pytest.mark.asyncio
async def test_interest_service_create(interest_service: InterestService):
    from app.models import Interest as InterestItem

    interest_data = InterestItem(
        name="Machine Learning",
        keywords=["AI", "Deep Learning", "Neural Networks"],
    )

    created_interest = await interest_service.create_interest(interest_data)

    assert created_interest is not None
    assert created_interest.name == "Machine Learning"


@pytest.mark.asyncio
async def test_interest_service_get(interest_service: InterestService):
    from app.models import Interest as InterestItem

    interest_data = InterestItem(name="Web Development", keywords=["JavaScript", "React"])
    created_interest = await interest_service.create_interest(interest_data)

    retrieved_interest = await interest_service.get_interest(created_interest.id)

    assert retrieved_interest is not None
    assert retrieved_interest.id == created_interest.id
    assert retrieved_interest.name == "Web Development"


@pytest.mark.asyncio
async def test_interest_service_get_all(interest_service: InterestService):
    from app.models import Interest as InterestItem

    await interest_service.create_interest(InterestItem(name="AI", keywords=["Machine Learning"]))
    await interest_service.create_interest(InterestItem(name="Web", keywords=["Frontend"]))

    all_interests = await interest_service.get_all_interests()

    assert len(all_interests) == 2


@pytest.mark.asyncio
async def test_interest_service_update(interest_service: InterestService):
    from app.models import Interest as InterestItem

    interest_data = InterestItem(name="Programming", keywords=["Python"])
    created_interest = await interest_service.create_interest(interest_data)

    update_data = InterestItem(
        name="Programming",
        keywords=["Python", "JavaScript", "Go"],
    )

    updated_interest = await interest_service.update_interest(created_interest.id, update_data)

    assert updated_interest is not None
    assert "Python" in updated_interest.keywords.split("|")
    assert "JavaScript" in updated_interest.keywords.split("|")


@pytest.mark.asyncio
async def test_interest_service_delete(interest_service: InterestService):
    from app.models import Interest as InterestItem

    interest_data = InterestItem(name="Test Interest", keywords=["Test"])
    created_interest = await interest_service.create_interest(interest_data)

    deleted = await interest_service.delete_interest(created_interest.id)

    assert deleted is True

    retrieved_interest = await interest_service.get_interest(created_interest.id)
    assert retrieved_interest is None


@pytest.mark.asyncio
async def test_interest_service_indexing(interest_service: InterestService, mock_chroma):
    from app.models import Interest as InterestItem

    interest_data = InterestItem(name="Machine Learning", keywords=["AI", "ML"])
    created_interest = await interest_service.create_interest(interest_data)

    assert mock_chroma.aadd_texts.called


@pytest.mark.asyncio
async def test_interest_service_delete_indexing(interest_service: InterestService, mock_chroma):
    from app.models import Interest as InterestItem

    interest_data = InterestItem(name="Test Interest", keywords=["Test"])
    created_interest = await interest_service.create_interest(interest_data)

    await interest_service.delete_interest(created_interest.id)

    assert mock_chroma.adelete.called
