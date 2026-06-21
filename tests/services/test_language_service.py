import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.db.models import Language
from app.services import LanguageService

os.environ["OPENAI_API_KEY"] = "test_key"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Language.metadata.create_all)

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
async def language_service(db_session: AsyncSession, mock_chroma, mock_embeddings):
    return LanguageService(db_session, mock_chroma, mock_embeddings)


@pytest.mark.asyncio
async def test_language_service_create(language_service: LanguageService):
    from app.models import Language_1 as LanguageItem

    language_data = LanguageItem(
        language="Spanish",
        fluency="Native",
    )

    created_language = await language_service.create_language(language_data)

    assert created_language is not None
    assert created_language.language == "Spanish"
    assert created_language.fluency == "Native"


@pytest.mark.asyncio
async def test_language_service_get(language_service: LanguageService):
    from app.models import Language as LanguageItem

    language_data = LanguageItem(language="English", fluency="Advanced")
    created_language = await language_service.create_language(language_data)

    retrieved_language = await language_service.get_language(created_language.id)

    assert retrieved_language is not None
    assert retrieved_language.id == created_language.id
    assert retrieved_language.language == "English"


@pytest.mark.asyncio
async def test_language_service_get_all(language_service: LanguageService):
    from app.models import Language as LanguageItem

    await language_service.create_language(LanguageItem(language="Spanish", fluency="Native"))
    await language_service.create_language(LanguageItem(language="English", fluencyver="Advanced"))

    all_languages = await language_service.get_all_languages()

    assert len(all_languages) == 2


@pytest.mark.asyncio
async def test_language_service_update(language_service: LanguageService):
    from app.models import Language as LanguageItem

    language_data = LanguageItem(language="Spanish", fluency="Intermediate")
    created_language = await language_service.create_language(language_data)

    update_data = LanguageItem(
        language="Spanish",
        fluency="Advanced",
    )

    updated_language = await language_service.update_language(created_language.id, update_data)

    assert updated_language is not None
    assert updated_language.fluency == "Advanced"


@pytest.mark.asyncio
async def test_language_service_delete(language_service: LanguageServicever):
    from app.models import Language as LanguageItem

    language_data = LanguageItem(language="Spanish", fluency="Native")
    created_language = await language_service.create_language(language_data)

    deleted = await language_service.delete_language(created_language.id)

    assert deleted is True

    retrieved_language = await language_service.get_language(created_language.id)
    assert retrieved_language is None


@pytest.mark.asyncio
async def test_language_service_indexing(language_service: LanguageService, mock_chroma):
    from app.models import Language as LanguageItem

    language_data = LanguageItem(language="Spanish", fluency="Native")
    created_language = await language_service.create_language(language_data)

    assert mock_chroma.aadd_texts.called


@pytest.mark.asyncio
async def test_language_service_delete_indexing(language_service: LanguageService, mock_chroma):
    from app.models import Language as LanguageItem

    language_data = LanguageItem(language="Spanish", fluency="Native")
    created_language = await language_service.create_language(language_data)

    await language_service.delete_language(created_language.id)

    assert mock_chroma.adelete.called
