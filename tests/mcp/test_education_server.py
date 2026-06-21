"""
Tests for Education MCP Server
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.education import Education


@pytest.mark.asyncio
async def test_education_server_list_tools():
    """Test that education server lists correct tools"""
    with patch('mcp_servers.education_server.app') as mock_app:
        from mcp_servers.education_server import list_tools
        
        tools = await list_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "get_education_by_id" in tool_names
        assert "get_all_education" in tool_names
        assert "search_education" in tool_names


@pytest.mark.asyncio
async def test_education_server_get_by_id():
    """Test getting education by ID"""
    with patch('mcp_servers.education_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_edu = Education(
            id=1,
            institution="MIT",
            area="Computer Science",
            study_type="Bachelor",
            start_date="2018-09",
            end_date="2022-05",
            score="3.8",
            courses="Data Structures|Algorithms",
            url="https://mit.edu"
        )
        mock_result.scalar_one_or_none.return_value = mock_edu
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.education_server import call_tool
        
        result = await call_tool("get_education_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["institution"] == "MIT"
        assert data["area"] == "Computer Science"
        assert isinstance(data["courses"], list)
        assert len(data["courses"]) == 2


@pytest.mark.asyncio
async def test_education_server_get_by_id_not_found():
    """Test getting non-existent education"""
    with patch('mcp_servers.education_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.education_server import call_tool
        
        result = await call_tool("get_education_by_id", {"id": 999})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "not found" in data["error"].lower()


@pytest.mark.asyncio
async def test_education_server_get_all():
    """Test getting all education entries"""
    with patch('mcp_servers.education_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_edu1 = Education(
            id=1,
            institution="MIT",
            area="Computer Science",
            study_type="Bachelor",
            start_date="2018-09",
            end_date="2022-05",
            score="3.8",
            courses="Data Structures|Algorithms",
            url="https://mit.edu"
        )
        mock_edu2 = Education(
            id=2,
            institution="Stanford",
            area="Artificial Intelligence",
            study_type="Master",
            start_date="2022-09",
            end_date="2024-05",
            score="4.0",
            courses="Machine Learning|Deep Learning",
            url="https://stanford.edu"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_edu1, mock_edu2]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.education_server import call_tool
        
        result = await call_tool("get_all_education", {})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "education" in data
        assert len(data["education"]) == 2
        assert data["education"][0]["institution"] == "MIT"
        assert data["education"][1]["institution"] == "Stanford"


@pytest.mark.asyncio
async def test_education_server_search():
    """Test searching education"""
    with patch('mcp_servers.education_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_edu = Education(
            id=1,
            institution="MIT",
            area="Computer Science",
            study_type="Bachelor",
            start_date="2018-09",
            end_date="2022-05",
            score="3.8",
            courses="Data Structures|Algorithms",
            url="https://mit.edu"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_edu]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.education_server import call_tool
        
        result = await call_tool("search_education", {"query": "computer"})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "education" in data
        assert len(data["education"]) == 1
        assert data["education"][0]["area"] == "Computer Science"


@pytest.mark.asyncio
async def test_education_server_unknown_tool():
    """Test calling unknown tool"""
    from mcp_servers.education_server import call_tool
    
    result = await call_tool("unknown_tool", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "error" in data
    assert "unknown" in data["error"].lower()


@pytest.mark.asyncio
async def test_education_server_empty_courses():
    """Test education with empty courses"""
    with patch('mcp_servers.education_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_edu = Education(
            id=1,
            institution="MIT",
            area="Computer Science",
            study_type="Bachelor",
            start_date="2018-09",
            end_date="2022-05",
            score="3.8",
            courses=None,
            url="https://mit.edu"
        )
        mock_result.scalar_one_or_none.return_value = mock_edu
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.education_server import call_tool
        
        result = await call_tool("get_education_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["courses"] == []
