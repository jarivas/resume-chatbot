import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.db.models import Award
from app.services import AwardService

os.environ["OPENAI_API_KEY"] = "test_key"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Award.metadata.create_all)

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
async def award_service(db_session: AsyncSession, mock_chroma, mock_embeddings):
    return AwardService(db_session, mock_chroma, mock_embeddings)


@pytest.mark.asyncio
async def test_award_service_create(award_service: AwardService):
    from app.models import Award as AwardItem

    award_data = AwardItem(
        title="Best Developer Award",
        date="2023-12",
        awarder="Tech Corp",
        summary="Recognized for outstanding contributions",
    )

    created_award = await award_service.create_award(award_data)

    assert created_award is not None
    assert created_award.title == "Best Developer Award"
    assert created_award.awarder == "Tech Corp"


@pytest.mark.asyncio
async def test_award_service_get(award_service: AwardService):
    from app.models import Award as AwardItem

    award_data = AwardItem(title="Innovation Award", awarder="Startup Inc")
    created_award = await award_service.create_award(award_data)

    retrieved_award = await award_service.get_award(created_award.id)

    assert retrieved_award is not None
    assert retrieved_award.id == created_award.id
    assert retrieved_award.title == "Innovation Award"


@pytest.mark.asyncio
async def test_award_service_get_all(award_service: AwardService):
    from app.models import Award as AwardItem

    await award_service.create_award(AwardItem(title="Award 1", awarder="Org 1"))
    await award_service.create_award(AwardItem(title="Award 2", awarder="Org 2"))

    all_awards = await award_service.get_all_awards()

    assert len(all_awards) == 2


@pytest.mark.asyncio
async def test_award_service_update(award_service: AwardService):
    from app.models import Award as AwardItem

    award_data = AwardItem(title="Original Award", awarder="Original Org")
    created_award = await award_service.create_award(award_data)

    update_data = AwardItem(
        title="Original Award",
        awarder="Original Org",
        summary="Updated summary",
    )

    updated_award = await award_service.update_award(created_award.id, update_data)

    assert updated_award is not None
    assert updated_award.summary == "Updated summary"


@pytest.mark.asyncio
async def test_award_service_delete(award_service: AwardService):
    from app.models import Award as AwardItem

    award_data = AwardItem(title="Award to Delete", awarder="Test Org")
    created_award = await award_service.create_award(award_data)

    deleted = await award_service.delete_award(created_award.id)

    assert deleted is True

    retrieved_award = await award_service.get_award(created_award.id)
    assert retriev_ed_award is None


@pytest.mark.asyncio
async def test_award_service_indexing(award_service: AwardService, mock_chroma):
    from app.models import Award as AwardItem

    award_data = AwardItem(title="Test Award", awarder="Test Org")
    created_award = await award_service.create_award(award_data)

    assert mock_chroma.aadd_texts.called
    call_args = mock_chroma.aadd_texts.call_args
    assert len(call_args[0][0]) == 1
    assert "Test Award" in call_args[0][0][0]


@pytest.mark.asyncio
async def test_award_service_delete_indexing(award_service: AwardService, mock_chroma):
    from app.models import Award as AwardItem

    award_data = AwardItem(title="Test Award", awarder="Test Org")
    created_award = await award_service.create_award(award_data)

    await award_service.delete_award(created_award.id)

    assert mock_chroma.adelete.called
    call_args = mock_chroma.adelete.call_args
    assert f"award_{created_award.id}" in call_args[0][0]
