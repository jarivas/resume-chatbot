"""
Tests for Languages MCP Server
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.language import Language


@pytest.mark.asyncio
async def test_languages_server_list_tools():
    """Test that languages server lists correct tools"""
    with patch('mcp_servers.languages_server.app') as mock_app:
        from mcp_servers.languages_server import list_tools
        
        tools = await list_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "get_language_by_id" in tool_names
        assert "get_all_languages" in tool_names
        assert "search_languages" in tool_names


@pytest.mark.asyncio
async def test_languages_server_get_by_id():
    """Test getting language by ID"""
    with patch('mcp_servers.languages_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_lang = Language(
            id=1,
            language="Spanish",
            fluency="Native"
        )
        mock_result.scalar_one_or_none.return_value = mock_lang
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.languages_server import call_tool
        
        result = await call_tool("get_language_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["language"] == "Spanish"
        assert data["fluency"] == "Native"


@pytest.mark.asyncio
async def test_languages_server_get_by_id_not_found():
    """Test getting non-existent language"""
    with patch('mcp_servers.languages_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.languages_server import call_tool
        
        result = await call_tool("get_language_by_id", {"id": 999})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "not found" in data["error"].lower()


@pytest.mark.asyncio
async def test_languages_server_get_all():
    """Test getting all languages"""
    with patch('mcp_servers.languages_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_lang1 = Language(
            id=1,
            language="Spanish",
            fluency="Native"
        )
        mock_lang2 = Language(
            id=2,
            language="English",
            fluency="Fluent"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_lang1, mock_lang2]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.languages_server import call_tool
        
        result = await call_tool("get_all_languages", {})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "languages" in data
        assert len(data["languages"]) == 2
        assert data["languages"][0]["language"] == "Spanish"
        assert data["languages"][1]["language"] == "English"


@pytest.mark.asyncio
async def test_languages_server_search():
    """Test searching languages"""
    with patch('mcp_servers.languages_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_lang = Language(
            id=1,
            language="Spanish",
            fluency="Native"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_lang]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.languages_server import call_tool
        
        result = await call_tool("search_languages", {"query": "spanish"})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "languages" in data
        assert len(data["languages"]) == 1
        assert data["languages"][0]["language"] == "Spanish"


@pytest.mark.asyncio
async def test_languages_server_unknown_tool():
    """Test calling unknown tool"""
    from mcp_servers.languages_server import call_tool
    
    result = await call_tool("unknown_tool", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "error" in data
    assert "unknown" in data["error"].lower()
