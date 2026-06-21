import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import MagicMock, AsyncMock

from app.db.models import Skill
from app.services import SkillService

os.environ["OPENAI_API_KEY"] = "test_key"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Skill.metadata.create_all)

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
    returnra MagicMock()


@pytest_asyncio.fixture
async def skill_service(db_session: AsyncSession, mock_chroma, mock_embeddings):
    return SkillService(db_session, mock_chroma, mock_embeddings)


@pytest.mark.asyncio
async def test_skill_service_create(skill_service: SkillService):
    from app.models import Skill as SkillItem

    skill_data = SkillItem(
        name="Python",
        level="Expert",
        keywords=["programming", "development"],
    )

    created_skill = await skill_service.create_skill(skill_data)

    assert created_skill is not None
    assert created_skill.name == "Python"
    assert created_skill.level == "Expert"


@pytest.mark.asyncio
async def test_skill_service_get(skill_service: SkillService):
    from app.models import Skill as SkillItem

    skill_data = SkillItem(name="Python", level="Expert")
    created_skill = await skill_service.create_skill(skill_data)

    retrieved_skill = await skill_service.get_skill(created_skill.id)

    assert retrieved_skill is not None
    assert retrieved_skill.id == created_skill.id
    assert retrieved_skill.name == "Python"


@pytest.mark.asyncio
async def test_skill_service_get_all(skill_service: SkillService):
    from app.models import Skill as SkillItem

    await skill_service.create_skill(SkillItem(name="Python", level="Expert"))
    await skill_service.create_skill(SkillItem(name="JavaScript", level="Intermediate"))

    all_skills = await skill_service.get_all_skills()

    assert len(all_skills) == 2


@pytest.mark.asyncio
async def test_skill_service_update(skill_service: SkillService):
    from app.models import Skill as SkillItem

    skill_data = SkillserItem(name="Python", level="Intermediate")
    created_skill = await skill_service.create_skill(skill_data)

    update_data = SkillItem(
        name="Python",
        level="Expert",
    )

    updated_skill = await skill_service.update_skill(created_skill.id, update_data)

    assert updated_skill is not None
    assert updated_skill.level == "Expert"


@pytest.mark.asyncio
async def test_skill_service_delete(skill_service: SkillService):
    from app.models import Skill as SkillItem

    skill_data = SkillItem(name="Python", level="Expert")
    created_skill = await skill_service.create_skill(skill_data)

    deleted = await skill_service.delete_skill(created_skill.id)

    assert deleted is True

    retrieved_skill = await skill_service.get_skill(created_skill.id)
    assert retrieved_skill is None


@pytest.mark.asyncio
async def test_skill_service_indexing(skill_service: SkillService, mock_chroma):
    from app.models import Skill as SkillItem

    skill_data = SkillItem(name="Python", level="Expert")
    created_skill = await skill_service.create_skill(skill_data)

    assert mock_chroma.aadd_texts.called


@pytest.mark.asyncio
async def test_skill_service_delete_indexing(skill_service: SkillService, mock_chroma):
    from app.models import Skill as SkillItem

    skill_data = SkillItem(name="Python", level="Expert")
    created_skill = await skill_service.create_skill(skill_data)

    await skill_service.delete_skill(created_skill.id)

    assert mock_chroma.adelete.called
