"""
Tests for Volunteer MCP Server
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.volunteer import Volunteer


@pytest.mark.asyncio
async def test_volunteer_server_list_tools():
    """Test that volunteer server lists correct tools"""
    with patch('mcp_servers.volunteer_server.app') as mock_app:
        from mcp_servers.volunteer_server import list_tools
        
        tools = await list_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "get_volunteer_by_id" in tool_names
        assert "get_all_volunteer" in tool_names
        assert "search_volunteer" in tool_names


@pytest.mark.asyncio
async def test_volunteer_server_get_by_id():
    """Test getting volunteer experience by ID"""
    with patch('mcp_servers.volunteer_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_vol = Volunteer(
            id=1,
            organization="Tech Nonprofit",
            position="Volunteer Developer",
            summary="Helped build website",
            highlights="Web Development|React",
            start_date="2020-01",
            end_date="2021-12",
            url="https://nonprofit.org"
        )
        mock_result.scalar_one_or_none.return_value = mock_vol
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.volunteer_server import call_tool
        
        result = await call_tool("get_volunteer_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["organization"] == "Tech Nonprofit"
        assert data["position"] == "Volunteer Developer"
        assert isinstance(data["highlights"], list)
        assert len(data["highlights"]) == 2


@pytest.mark.asyncio
async def test_volunteer_server_get_by_id_not_found():
    """Test getting non-existent volunteer experience"""
    with patch('mcp_servers.volunteer_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.volunteer_server import call_tool
        
        result = await call_tool("get_volunteer_by_id", {"id": 999})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "not found" in data["error"].lower()


@pytest.mark.asyncio
async def test_volunteer_server_get_all():
    """Test getting all volunteer experiences"""
    with patch('mcp_servers.volunteer_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_vol1 = Volunteer(
            id=1,
            organization="Tech Nonprofit",
            position="Volunteer Developer",
            summary="Helped build website",
            highlights="Web Development|React",
            start_date="2020-01",
            end_date="2021-12",
            url="https://nonprofit.org"
        )
        mock_vol2 = Volunteer(
            id=2,
            organization="Code for America",
            position="Mentor",
            summary="Mentored junior developers",
            highlights="Teaching|Mentorship",
            start_date="2019-01",
            end_date="2020-12",
            url="https://codeforamerica.org"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_vol1, mock_vol2]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.volunteer_server import call_tool
        
        result = await call_tool("get_all_volunteer", {})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "volunteer_experiences" in data
        assert len(data["volunteer_experiences"]) == 2
        assert data["volunteer_experiences"][0]["organization"] == "Tech Nonprofit"
        assert data["volunteer_experiences"][1]["organization"] == "Code for America"


@pytest.mark.asyncio
async def test_volunteer_server_search():
    """Test searching volunteer experiences"""
    with patch('mcp_servers.volunteer_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_vol = Volunteer(
            id=1,
            organization="Tech Nonprofit",
            position="Volunteer Developer",
            summary="Helped build website",
            highlights="Web Development|React",
            start_date="2020-01",
            end_date="2021-12",
            url="https://nonprofit.org"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_vol]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.volunteer_server import call_tool
        
        result = await call_tool("search_volunteer", {"query": "nonprofit"})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "volunteer_experiences" in data
        assert len(data["volunteer_experiences"]) == 1
        assert data["volunteer_experiences"][0]["organization"] == "Tech Nonprofit"


@pytest.mark.asyncio
async def test_volunteer_server_unknown_tool():
    """Test calling unknown tool"""
    from mcp_servers.volunteer_server import call_tool
    
    result = await call_tool("unknown_tool", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "error" in data
    assert "unknown" in data["error"].lower()


@pytest.mark.asyncio
async def test_volunteer_server_empty_highlights():
    """Test volunteer experience with empty highlights"""
    with patch('mcp_servers.volunteer_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_vol = Volunteer(
            id=1,
            organization="Tech Nonprofit",
            position="Volunteer Developer",
            summary="Helped build website",
            highlights=None,
            start_date="2020-01",
            end_date="2021-12",
            url="https://nonprofit.org"
        )
        mock_result.scalar_one_or_none.return_value = mock_vol
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.volunteer_server import call_tool
        
        result = await call_tool("get_volunteer_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["highlights"] == []
