import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.db.models import Work
from app.services import WorkService

os.environ["OPENAI_API_KEY"] = "test_key"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Work.metadata.create_all)

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
async def work_service(db_session: AsyncSession, mock_chroma, mock_embeddings):
    return WorkService(db_session, mock_chroma, mock_embeddings)


@pytest.mark.asyncio
async def test_work_service_create(work_service: WorkService):
    from app.models import Work as WorkItem

    work_data = WorkItem(
        name="Tech Corp",
        position="Software Engineer",
        summary="Developed amazing software",
        highlights=["Increased efficiency by 50%", "Led team of 5"],
    )

    created_work = await work_service.create_work(work_data)

    assert created_work is not None
    assert created_work.name == "Tech Corp"
    assert created_work.position == "Software Engineer"
    assert created_work.summary == "Developed amazing software"


@pytest.mark.asyncio
async def test_work_service_get(work_service: WorkService):
    from app.models import Work as WorkItem

    work_data = WorkItem(name="Tech Corp", position="Software Engineer")
    created_work = await work_service.create_work(work_data)

    retrieved_work = await work_service.get_work(created_work.id)

    assert retrieved_work is not None
    assert retrieved_work.id == created_work.id
    assert retrieved_work.name == "Tech Corp"


@pytest.mark.asyncio
async def test_work_service_get_all(work_service: WorkService):
    from app.models import Work as WorkItem

    await work_service.create_work(WorkItem(name="Company 1", position="Position 1"))
    await work_service.create_work(WorkItem(name="Company 2", position="Position 2"))

    all_works = await work_service.get_all_work()

    assert len(all_works) == 2
    assert any(work.name == "Company 1" for work in all_works)


@pytest.mark.asyncio
async def test_work_service_update(work_service: WorkService):
    from app.models import Work as WorkItem

    work_data = WorkItem(name="Tech Corp", position="Software Engineer")
    created_work = await work_service.create_work(work_data)

    update_data = WorkItem(
        name="Tech Corp",
        position="Senior Software Engineer",
        summary="Promoted to senior role",
    )

    updated_work = await work_service.update_work(created_work.id, update_data)

    assert updated_work is not None
    assert updated_work.position == "Senior Software Engineer"
    assert updated_work.summary == "Promoted to senior role"


@pytest.mark.asyncio
async def test_work_service_delete(work_service: WorkService):
    from app.models import Work as WorkItem

    work_data = WorkItem(name="Tech Corp", position="Software Engineer")
    created_work = await work_service.create_work(work_data)

    deleted = await work_service.delete_work(created_work.id)

    assert deleted is True

    retrieved_work = await work_service.get_work(created_work.id)
    assert retrieved_work is None


@pytest.mark.asyncio
async def test_work_service_get_indexing(work_service: WorkService, mock_chroma):
    from app.models import Work as WorkItem

    work_data = WorkItem(name="Tech Corp", position="Software Engineer")
    created_work = await work_service.create_work(work_data)

    assert mock_chroma.aadd_texts.called
    call_args = mock_chroma.aadd_texts.call_args
    assert len(call_args[0][0]) == 1
    assert "Tech Corp" in call_args[0][0][0]


@pytest.mark.asyncio
async def test_work_service_delete_indexing(work_service: WorkService, mock_chroma):
    from app.models import Work as WorkItem

    work_data = WorkItem(name="Tech Corp", position="Software Engineer")
    created_work = await work_service.create_work(work_data)

    await work_service.delete_work(created_work.id)

    assert mock_chroma.adelete.called
    call_args = mock_chroma.adelete.call_args
    assert f"work_{created_work.id}" in call_args[0][0]
