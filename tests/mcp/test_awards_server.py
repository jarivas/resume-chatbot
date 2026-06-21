"""
Tests for Awards MCP Server
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.award import Award


@pytest.mark.asyncio
async def test_awards_server_list_tools():
    """Test that awards server lists correct tools"""
    with patch('mcp_servers.awards_server.app') as mock_app:
        from mcp_servers.awards_server import list_tools
        
        tools = await list_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "get_award_by_id" in tool_names
        assert "get_all_awards" in tool_names
        assert "search_awards" in tool_names


@pytest.mark.asyncio
async def test_awards_server_get_by_id():
    """Test getting award by ID"""
    with patch('mcp_servers.awards_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_award = Award(
            id=1,
            title="Best Developer",
            date="2023-12",
            awarder="Tech Awards",
            summary="Recognized for excellence",
            url="https://techawards.com"
        )
        mock_result.scalar_one_or_none.return_value = mock_award
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.awards_server import call_tool
        
        result = await call_tool("get_award_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["title"] == "Best Developer"
        assert data["awarder"] == "Tech Awards"


@pytest.mark.asyncio
async def test_awards_server_get_by_id_not_found():
    """Test getting non-existent award"""
    with patch('mcp_servers.awards_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.awards_server import call_tool
        
        result = await call_tool("get_award_by_id", {"id": 999})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "not found" in data["error"].lower()


@pytest.mark.asyncio
async def test_awards_server_get_all():
    """Test getting all awards"""
    with patch('mcp_servers.awards_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_award1 = Award(
            id=1,
            title="Best Developer",
            date="2023-12",
            awarder="Tech Awards",
            summary="Recognized for excellence",
            url="https://techawards.com"
        )
        mock_award2 = Award(
            id=2,
            title="Innovation Prize",
            date="2022-11",
            awarder="Innovation Summit",
            summary="Best project",
            url="https://innovation.com"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_award1, mock_award2]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.awards_server import call_tool
        
        result = await call_tool("get_all_awards", {})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "awards" in data
        assert len(data["awards"]) == 2
        assert data["awards"][0]["title"] == "Best Developer"
        assert data["awards"][1]["title"] == "Innovation Prize"


@pytest.mark.asyncio
async def test_awards_server_search():
    """Test searching awards"""
    with patch('mcp_servers.awards_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_award = Award(
            id=1,
            title="Best Developer",
            date="2023-12",
            awarder="Tech Awards",
            summary="Recognized for excellence",
            url="https://techawards.com"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_award]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.awards_server import call_tool
        
        result = await call_tool("search_awards", {"query": "developer"})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "awards" in data
        assert len(data["awards"]) == 1
        assert data["awards"][0]["title"] == "Best Developer"


@pytest.mark.asyncio
async def test_awards_server_unknown_tool():
    """Test calling unknown tool"""
    from mcp_servers.awards_server import call_tool
    
    result = await call_tool("unknown_tool", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "error" in data
    assert "unknown" in data["error"].lower()
