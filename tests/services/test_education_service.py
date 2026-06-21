import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.db.models import Education
from app.services import EducationService

os.environ["OPENAI_API_KEY"] = "test_key"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Education.metadata.create_all)

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
async def education_service(db_session: AsyncSession, mock_chroma, mock_embeddings):
    return EducationService(db_session, mock_chroma, mock_embeddings)


@pytest.mark.asyncio
async def test_education_service_create(education_service: EducationService):
    from app.models import Education as EducationItem

    education_data = EducationItem(
        institution="MIT",
        area="Computer Science",
        study_type="Bachelor",
        start_date="2018-09",
        end_date="2022-05",
        score="3.8",
        courses=["Data Structures", "Algorithms"],
    )

    created_education = await education_service.create_education(education_data)

    assert created_education is not None
    assert created_education.institution == "MIT"
    assert created_education.area == "Computer Science"
    assert created_education.study_type == "Bachelor"


@pytest.mark.asyncio
async def test_education_service_get(education_service: EducationService):
    from app.models import Education as EducationItem

    education_data = EducationItem(institution="MIT", area="Computer Science")
    created_education = await education_service.create_education(education_data)

    retrieved_education = await education_service.get_education(created_education.id)

    assert retrieved_education is not None
    assert retrieved_education.id == created_education.id
    assert retrieved_education.institution == "MIT"


@pytest.mark.asyncio
async def test_education_service_get_all(education_service: EducationService):
    from app.models import Education as EducationItem

    await education_service.create_education(EducationItem(institution="MIT", area="CS"))
    await education_service.create_education(EducationItem(institution="Stanford", area="AI"))

    all_educations = await education_service.get_all_education()

    assert len(all_educations) == 2
    assert any(edu.institution == "MIT" for edu in all_educations)


@pytest.mark.asyncio
async def test_education_service_update(education_service: EducationService):
    from app.models import Education as EducationItem

    education_data = EducationItem(institution="MIT", area="CS")
    created_education = await education_service.create_education(education_data)

    update_data = EducationItem(
        institution="MIT",
        area="Computer Science",
        score="4.0",
    )

    updated_education = await education_service.update_education(created_education.id, update_data)

    assert updated_education is not None
    assert updated_education.area == "Computer Science"
    assert updated_education.score == "4.0"


@pytest.mark.asyncio
async def test_education_service_delete(education_service: EducationService):
    from app.models import Education as EducationItem

    education_data = EducationItem(institution="MIT", area="CS")
    created_education = await education_service.create_education(education_data)

    deleted = await education_service.delete_education(created_education.id)

    assert deleted is True

    retrieved_education = await education_service.get_education(created_education.id)
    assert retrieved_education is None


@pytest.mark.asyncio
async def test_education_service_indexing(education_service: EducationService, mock_chroma):
    from app.models import Education as EducationItem

    education_data = EducationItem(institution="MIT", area="Computer Science")
    created_education = await education_service.create_education(education_data)

    assert mock_chroma.aadd_texts.called
    call_args = mock_chroma.aadd_texts.call_args
    assert len(call_args[0][0]) == 1
    assert "MIT" in call_args[0][0][0]


@pytest.mark.asyncio
async def test_education_service_delete_indexing(education_service: EducationService, mock_chroma):
    from app.models import Education as EducationItem

    education_data = EducationItem(institution="MIT", area="CS")
    created_education = await education_service.create_education(education_data)

    await education_service.delete_education(created_education.id)

    assert mock_chroma.adelete.called
    call_args = mock_chroma.adelete.call_args
    assert f"education_{created_education.id}" in call_args[0][0]
