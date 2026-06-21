"""
Tests for Work MCP Server
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.work import Work


@pytest.mark.asyncio
async def test_work_server_list_tools():
    """Test that work server lists correct tools"""
    from mcp_servers.work_server import list_tools
    
    tools = await list_tools()
    
    assert len(tools) == 3
    tool_names = [tool.name for tool in tools]
    assert "get_work_by_id" in tool_names
    assert "get_all_work" in tool_names
    assert "search_work" in tool_names


@pytest.mark.asyncio
async def test_work_server_get_by_id():
    """Test getting work experience by ID"""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_work = Work(
        id=1,
        name="Tech Corp",
        position="Software Engineer",
        summary="Developed software",
        highlights="highlight1|highlight2",
        start_date="2020-01",
        end_date="2023-12",
        url="https://example.com",
        location="Remote"
    )
    mock_result.scalar_one_or_none.return_value = mock_work
    mock_session.execute.return_value = mock_result
    
    async def mock_get_async_session():
        yield mock_session
    
    with patch('mcp_servers.work_server.get_async_session', side_effect=mock_get_async_session):
        from mcp_servers.work_server import call_tool
        
        result = await call_tool("get_work_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["company"] == "Tech Corp"
        assert data["position"] == "Software Engineer"
        assert isinstance(data["highlights"], list)
        assert len(data["highlights"]) == 2


@pytest.mark.asyncio
async def test_work_server_get_by_id_not_found():
    """Test getting non-existent work experience"""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    async def mock_get_async_session():
        yield mock_session
    
    with patch('mcp_servers.work_server.get_async_session', side_effect=mock_get_async_session):
        from mcp_servers.work_server import call_tool
        
        result = await call_tool("get_work_by_id", {"id": 999})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "not found" in data["error"].lower()


@pytest.mark.asyncio
async def test_work_server_get_all():
    """Test getting all work experiences"""
    mock_session = AsyncMock(spec=AsyncSession)
    
    mock_work1 = Work(
        id=1,
        name="Tech Corp",
        position="Software Engineer",
        summary="Developed software",
        highlights="highlight1|highlight2",
        start_date="2020-01",
        end_date="2023-12",
        url="https://example.com",
        location="Remote"
    )
    mock_work2 = Work(
        id=2,
        name="Startup Inc",
        position="Senior Developer",
        summary="Built scalable systems",
        highlights="highlight3",
        start_date="2018-01",
        end_date="2020-01",
        url="https://startup.com",
        location="San Francisco"
    )
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_work1, mock_work2]
    mock_session.execute.return_value = mock_result
    
    async def mock_get_async_session():
        yield mock_session
    
    with patch('mcp_servers.work_server.get_async_session', side_effect=mock_get_async_session):
        from mcp_servers.work_server import call_tool
        
        result = await call_tool("get_all_work", {})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "work_experiences" in data
        assert len(data["work_experiences"]) == 2
        assert data["work_experiences"][0]["company"] == "Tech Corp"
        assert data["work_experiences"][1]["company"] == "Startup Inc"


@pytest.mark.asyncio
async def test_work_server_search():
    """Test searching work experiences"""
    mock_session = AsyncMock(spec=AsyncSession)
    
    mock_work = Work(
        id=1,
        name="Tech Corp",
        position="Software Engineer",
        summary="Developed software",
        highlights="highlight1|highlight2",
        start_date="2020-01",
        end_date="2023-12",
        url="https://example.com",
        location="Remote"
    )
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_work]
    mock_session.execute.return_value = mock_result
    
    async def mock_get_async_session():
        yield mock_session
    
    with patch('mcp_servers.work_server.get_async_session', side_effect=mock_get_async_session):
        from mcp_servers.work_server import call_tool
        
        result = await call_tool("search_work", {"query": "tech"})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "work_experiences" in data
        assert len(data["work_experiences"]) == 1
        assert data["work_experiences"][0]["company"] == "Tech Corp"


@pytest.mark.asyncio
async def test_work_server_unknown_tool():
    """Test calling unknown tool"""
    from mcp_servers.work_server import call_tool
    
    result = await call_tool("unknown_tool", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "error" in data
    assert "unknown" in data["error"].lower()


@pytest.mark.asyncio
async def test_work_server_empty_highlights():
    """Test work experience with empty highlights"""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_work = Work(
        id=1,
        name="Tech Corp",
        position="Software Engineer",
        summary="Developed software",
        highlights=None,
        start_date="2020-01",
        end_date="2023-12",
        url="https://example.com",
        location="Remote"
    )
    mock_result.scalar_one_or_none.return_value = mock_work
    mock_session.execute.return_value = mock_result
    
    async def mock_get_async_session():
        yield mock_session
    
    with patch('mcp_servers.work_server.get_async_session', side_effect=mock_get_async_session):
        from mcp_servers.work_server import call_tool
        
        result = await call_tool("get_work_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["highlights"] == []
