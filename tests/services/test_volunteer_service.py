import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.db.models import Volunteer
from app.services import VolunteerService

os.environ["OPENAI_API_KEY"] = "test_key"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Volunteer.metadata.create)

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
async def volunteer_service(db_session: AsyncSession, mock_chroma, mock_embeddings):
    return VolunteerService(db_session, mock_chroma, mock_embeddings)


@pytest.mark.asyncio
async def test_volunteer_service_create(volunteer_service: VolunteerService):
    from app.models import Volunteer as VolunteerItem

    volunteer_data = VolunteerItem(
        organization="Red Cross",
        position="Volunteer",
        summary="Helped with community events",
        highlights=["Organized events", "Helped people"],
    )

    created_volunteer = await volunteer_service.create_volunteer(volunteer_data)

    assert created_volunteer is not None
    assert created_volunteer.organization == "Red Cross"
    assert created_volunteer.position == "Volunteer"


@pytest.mark.asyncio
async def test_volunteer_service_get(volunteer_service: VolunteerService):
    from app.models import Volunteer as VolunteerItem

    volunteer_data = VolunteerItem(organization="Red Cross", position="Volunteer")
    created_volunteer = await volunteer_service.create_volunteer(volunteer_data)

    retrieved_volunteer = await volunteer_service.get_volunteer(created_volunteer.id)

    assert retrieved_volunteer is not None
    assert retrieved_volunteer.id == created_volunteer.id
    assert retrieved_volunteer.organization == "Red Cross"


@pytest.mark.asyncio
async def test_volunteer_service_get_all(volunteer_service: VolunteerService):
    from app.models import Volunteer as VolunteerItem

    await volunteer_service.create_volunteer(VolunteerItem(organization="Red Cross", position="Volunteer"))
    await volunteer_service.create_volunteer(VolunteerItem(organization="Green Peace", position="Activist"))

    all_volunteers = await volunteer_service.get_all_volunteer()

    assert len(all_volunteers) == 2


@pytest.mark.asyncio
async def test_volunteer_service_update(volunteer_service: VolunteerService):
    from app.models import Volunteer as VolunteerItem

    volunteer_data = VolunteerItem(organization="Red Cross", position="Volunteer")
    created_volunteer = await volunteer_service.create_volunteer(volunteer_data)

    update_data = VolunteerItem(
        organization="Red Cross",
        position="Senior Volunteer",
        summary="Led volunteer team",
    )

    updated_volunteer = await volunteer_service.update_volunteer(created_volunteer.id, update_data)

    assert updated_volunteer is not None
    assert updated_volunteer.position == "Senior Volunteer"
    assert updated_volunteer.summary == "Led volunteer team"


@pytest.mark.asyncio
async def test_volunteer_service_delete(volunteer_service: VolunteerService):
    from app.models import Volunteer as VolunteerItem

    volunteer_data = VolunteerItem(organization="Red Cross", position="Volunteer")
    created_volunteer = await volunteer_service.create_volunteer(volunteer_data)

    deleted = await volunteer_service.delete_volunteer(created_volunteer.id)

    assert deleted is True

    retrieved_volunteer = await volunteer_service.get_volunteer(created_volunteer.id)
    assert retrieved_volunteer is None


@pytest.mark.asyncio
async def test_volunteer_service_indexing(volunteer_service: VolunteerService, mock_chroma):
    from app.models import Volunteer as VolunteerItem

    volunteer_data = VolunteerItem(organization="Red Cross", position="Volunteer")
    created_volunteer = await volunteer_service.create_volunteer(volunteer_data)

    assert mock_chroma.aadd_texts.called
    call_args = mock_chroma.aadd_texts.call_args
    assert len(call_args[0][0]) == 1
    assert "Red Cross" in call_args[0][0][0]


@pytest.mark.asyncio
async def test_volunteer_service_delete_indexing(volunteer_service: VolunteerService, mock_chroma):
    from app.models import Volunteer as VolunteerItem

    volunteer_data = VolunteerItem(organization="Red Cross", position="Volunteer")
    created_volunteer = await volunteer_service.create_volunteer(volunteer_data)

    await volunteer_service.delete_volunteer(created_volunteer.id)

    assert mock_chroma.adelete.called
    call_args = mock_chroma.adelete.call_args
    assert f"volunteer_{created_volunteer.id}" in call_args[0][0]
