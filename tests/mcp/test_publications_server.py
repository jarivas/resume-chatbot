"""
Tests for Publications MCP Server
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.publication import Publication


@pytest.mark.asyncio
async def test_publications_server_list_tools():
    """Test that publications server lists correct tools"""
    with patch('mcp_servers.publications_server.app') as mock_app:
        from mcp_servers.publications_server import list_tools
        
        tools = await list_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "get_publication_by_id" in tool_names
        assert "get_all_publications" in tool_names
        assert "search_publications" in tool_names


@pytest.mark.asyncio
async def test_publications_server_get_by_id():
    """Test getting publication by ID"""
    with patch('mcp_servers.publications_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_pub = Publication(
            id=1,
            name="Advanced AI Techniques",
            publisher="Tech Journal",
            release_date="2023-10",
            url="https://techjournal.com/article/123",
            summary="Research on AI"
        )
        mock_result.scalar_one_or_none.return_value = mock_pub
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.publications_server import call_tool
        
        result = await call_tool("get_publication_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["name"] == "Advanced AI Techniques"
        assert data["publisher"] == "Tech Journal"


@pytest.mark.asyncio
async def test_publications_server_get_by_id_not_found():
    """Test getting non-existent publication"""
    with patch('mcp_servers.publications_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.publications_server import call_tool
        
        result = await call_tool("get_publication_by_id", {"id": 999})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "not found" in data["error"].lower()


@pytest.mark.asyncio
async def test_publications_server_get_all():
    """Test getting all publications"""
    with patch('mcp_servers.publications_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_pub1 = Publication(
            id=1,
            name="Advanced AI Techniques",
            publisher="Tech Journal",
            release_date="2023-10",
            url="https://techjournal.com/article/123",
            summary="Research on AI"
        )
        mock_pub2 = Publication(
            id=2,
            name="Machine Learning Best Practices",
            publisher="AI Magazine",
            release_date="2023-11",
            url="https://aimagazine.com/article/456",
            summary="ML research"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_pub1, mock_pub2]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.publications_server import call_tool
        
        result = await call_tool("get_all_publications", {})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "publications" in data
        assert len(data["publications"]) == 2
        assert data["publications"][0]["name"] == "Advanced AI Techniques"
        assert data["publications"][1]["name"] == "Machine Learning Best Practices"


@pytest.mark.asyncio
async def test_publications_server_search():
    """Test searching publications"""
    with patch('mcp_servers.publications_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_pub = Publication(
            id=1,
            name="Advanced AI Techniques",
            publisher="Tech Journal",
            release_date="2023-10",
            url="https://techjournal.com/article/123",
            summary="Research on AI"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_pub]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.publications_server import call_tool
        
        result = await call_tool("search_publications", {"query": "ai"})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "publications" in data
        assert len(data["publications"]) == 1
        assert data["publications"][0]["name"] == "Advanced AI Techniques"


@pytest.mark.asyncio
async def test_publications_server_unknown_tool():
    """Test calling unknown tool"""
    from mcp_servers.publications_server import call_tool
    
    result = await call_tool("unknown_tool", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "error" in data
    assert "unknown" in data["error"].lower()
