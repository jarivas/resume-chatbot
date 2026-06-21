"""
Tests for Interests MCP Server
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.interest import Interest


@pytest.mark.asyncio
async def test_interests_server_list_tools():
    """Test that interests server lists correct tools"""
    with patch('mcp_servers.interests_server.app') as mock_app:
        from mcp_servers.interests_server import list_tools
        
        tools = await list_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "get_interest_by_id" in tool_names
        assert "get_all_interests" in tool_names
        assert "search_interests" in tool_names


@pytest.mark.asyncio
async def test_interests_server_get_by_id():
    """Test getting interest by ID"""
    with patch('mcp_servers.interests_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_interest = Interest(
            id=1,
            name="Open Source",
            keywords="GitHub|Contributions|Community"
        )
        mock_result.scalar_one_or_none.return_value = mock_interest
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.interests_server import call_tool
        
        result = await call_tool("get_interest_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["name"] == "Open Source"
        assert isinstance(data["keywords"], list)
        assert len(data["keywords"]) == 3


@pytest.mark.asyncio
async def test_interests_server_get_by_id_not_found():
    """Test getting non-existent interest"""
    with patch('mcp_servers.interests_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.interests_server import call_tool
        
        result = await call_tool("get_interest_by_id", {"id": 999})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "not found" in data["error"].lower()


@pytest.mark.asyncio
async def test_interests_server_get_all():
    """Test getting all interests"""
    with patch('mcp_servers.interests_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_interest1 = Interest(
            id=1,
            name="Open Source",
            keywords="GitHub|Contributions|Community"
        )
        mock_interest2 = Interest(
            id=2,
            name="Machine Learning",
            keywords="AI|Research|Algorithms"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_interest1, mock_interest2]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.interests_server import call_tool
        
        result = await call_tool("get_all_interests", {})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "interests" in data
        assert len(data["interests"]) == 2
        assert data["interests"][0]["name"] == "Open Source"
        assert data["interests"][1]["name"] == "Machine Learning"


@pytest.mark.asyncio
async def test_interests_server_search():
    """Test searching interests"""
    with patch('mcp_servers.interests_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_interest = Interest(
            id=1,
            name="Open Source",
            keywords="GitHub|Contributions|Community"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_interest]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.interests_server import call_tool
        
        result = await call_tool("search_interests", {"query": "open"})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "interests" in data
        assert len(data["interests"]) == 1
        assert data["interests"][0]["name"] == "Open Source"


@pytest.mark.asyncio
async def test_interests_server_unknown_tool():
    """Test calling unknown tool"""
    from mcp_servers.interests_server import call_tool
    
    result = await call_tool("unknown_tool", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "error" in data
    assert "unknown" in data["error"].lower()


@pytest.mark.asyncio
async def test_interests_server_empty_keywords():
    """Test interest with empty keywords"""
    with patch('mcp_servers.interests_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_interest = Interest(
            id=1,
            name="Open Source",
            keywords=None
        )
        mock_result.scalar_one_or_none.return_value = mock_interest
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.interests_server import call_tool
        
        result = await call_tool("get_interest_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["keywords"] == []
