"""
Tests for Skills MCP Server
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.skill import Skill


@pytest.mark.asyncio
async def test_skills_server_list_tools():
    """Test that skills server lists correct tools"""
    with patch('mcp_servers.skills_server.app') as mock_app:
        from mcp_servers.skills_server import list_tools
        
        tools = await list_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "get_skill_by_id" in tool_names
        assert "get_all_skills" in tool_names
        assert "search_skills" in tool_names


@pytest.mark.asyncio
async def test_skills_server_get_by_id():
    """Test getting skill by ID"""
    with patch('mcp_servers.skills_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_skill = Skill(
            id=1,
            name="Python",
            level="Expert",
            keywords="programming|development|AI"
        )
        mock_result.scalar_one_or_none.return_value = mock_skill
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.skills_server import call_tool
        
        result = await call_tool("get_skill_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["name"] == "Python"
        assert data["level"] == "Expert"
        assert isinstance(data["keywords"], list)
        assert len(data["keywords"]) == 3


@pytest.mark.asyncio
async def test_skills_server_get_by_id_not_found():
    """Test getting non-existent skill"""
    with patch('mcp_servers.skills_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.skills_server import call_tool
        
        result = await call_tool("get_skill_by_id", {"id": 999})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "not found" in data["error"].lower()


@pytest.mark.asyncio
async def test_skills_server_get_all():
    """Test getting all skills"""
    with patch('mcp_servers.skills_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_skill1 = Skill(
            id=1,
            name="Python",
            level="Expert",
            keywords="programming|development|AI"
        )
        mock_skill2 = Skill(
            id=2,
            name="JavaScript",
            level="Advanced",
            keywords="web|frontend"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_skill1, mock_skill2]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.skills_server import call_tool
        
        result = await call_tool("get_all_skills", {})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "skills" in data
        assert len(data["skills"]) == 2
        assert data["skills"][0]["name"] == "Python"
        assert data["skills"][1]["name"] == "JavaScript"


@pytest.mark.asyncio
async def test_skills_server_search():
    """Test searching skills"""
    with patch('mcp_servers.skills_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_skill = Skill(
            id=1,
            name="Python",
            level="Expert",
            keywords="programming|development|AI"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_skill]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.skills_server import call_tool
        
        result = await call_tool("search_skills", {"query": "python"})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "skills" in data
        assert len(data["skills"]) == 1
        assert data["skills"][0]["name"] == "Python"


@pytest.mark.asyncio
async def test_skills_server_unknown_tool():
    """Test calling unknown tool"""
    from mcp_servers.skills_server import call_tool
    
    result = await call_tool("unknown_tool", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "error" in data
    assert "unknown" in data["error"].lower()


@pytest.mark.asyncio
async def test_skills_server_empty_keywords():
    """Test skill with empty keywords"""
    with patch('mcp_servers.skills_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_skill = Skill(
            id=1,
            name="Python",
            level="Expert",
            keywords=None
        )
        mock_result.scalar_one_or_none.return_value = mock_skill
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.skills_server import call_tool
        
        result = await call_tool("get_skill_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["keywords"] == []
