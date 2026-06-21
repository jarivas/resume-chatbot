"""
Tests for References MCP Server
"""
import pytest
import json
from unittest.mock import AsyncMock,AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.reference import Reference


@pytest.mark.asyncio
async def test_references_server_list_tools():
    """Test that references server lists correct tools"""
    with patch('mcp_servers.references_server.app') as mock_app:
        from mcp_servers.references_server import list_tools
        
        tools = await list_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "get_reference_by_id" in tool_names
        assert "get_all_references" in tool_names
        assert "search_references" in tool_names


@pytest.mark.asyncio
async def test_references_server_get_by_id():
    """Test getting reference by ID"""
    with patch('mcp_servers.references_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_ref = Reference(
            id=1,
            name="John Doe",
            reference="Excellent developer",
            relationship="Former Manager",
            email="john@example.com",
            phone="+1-555-1234",
            location="San Francisco, CA"
        )
        mock_result.scalar_one_or_none.return_value = mock_ref
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.references_server import call_tool
        
        result = await call_tool("get_reference_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["name"] == "John Doe"
        assert data["relationship"] == "Former Manager"


@pytest.mark.asyncio
async def test_references_server_get_by_id_not_found():
    """Test getting non-existent reference"""
    with patch('mcp_servers.references_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.references_server import call_tool
        
        result = await call_tool("get_reference_by_id", {"id": 999})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "not found" in data["error"].lower()


@pytest.mark.asyncio
async def test_references_server_get_all():
    """Test getting all references"""
    with patch('mcp_servers.references_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_ref1 = Reference(
            id=1,
            name="John Doe",
            reference="Excellent developer",
            relationship="Former Manager",
            email="john@example.com",
            phone="+1-555-1234",
            location="San Francisco, CA"
        )
        mock_ref2 = Reference(
            id=2,
            name="Jane Smith",
            reference="Great team player",
            relationship="Colleague",
            email="jane@example.com",
            phone="+1-555-5678",
            location="New York, NY"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_ref1, mock_ref2]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.references_server import call_tool
        
        result = await call_tool("get_all_references", {})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "references" in data
        assert len(data["references"]) == 2
        assert data["references"][0]["name"] == "John Doe"
        assert data["references"][1]["name"] == "Jane Smith"


@pytest.mark.asyncio
async def test_references_server_search():
    """Test searching references"""
    with patch('mcp_servers.references_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_ref = Reference(
            id=1,
            name="John Doe",
            reference="Excellent developer",
            relationship="Former Manager",
            email="john@example.com",
            phone="+1-555-1234",
            location="San Francisco, CA"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_ref]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.references_server import call_tool
        
        result = await call_tool("search_references", {"query": "john"})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "references" in data
        assert len(data["references"]) == 1
        assert data["references"][0]["name"] == "John Doe"


@pytest.mark.asyncio
async def test_references_server_unknown_tool():
    """Test calling unknown tool"""
    from mcp_servers.references_server import call_tool
    
    result = await call_tool("unknown_tool", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "error" in data
    assert "unknown" in data["error"].lower()
