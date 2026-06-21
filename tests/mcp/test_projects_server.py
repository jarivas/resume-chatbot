"""
Tests for Projects MCP Server
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.project import Project


@pytest.mark.asyncio
async def test_projects_projects_server_list_tools():
    """Test that projects server lists correct tools"""
    with patch('mcp_servers.projects_server.app') as mock_app:
        from mcp_servers.projects_server import list_tools
        
        tools = await list_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "get_project_by_id" in tool_names
        assert "get_all_projects" in tool_names
        assert "search_projects" in tool_names


@pytest.mark.asyncio
async def test_projects_server_get_by_id():
    """Test getting project by ID"""
    with patch('mcp_servers.projects_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_project = Project(
            id=1,
            name="Resume Chatbot",
            description="AI-powered resume assistant",
            highlights="FastAPI|ChromaDB|RAG",
            start_date="2023-01",
            end_date="2023-12",
            url="https://github.com/user/resume-chatbot",
            type="web",
            entity="Personal",
            roles="Developer|Architect"
        )
        mock_result.scalar_one_or_none.return_value = mock_project
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.projects_server import call_tool
        
        result = await call_tool("get_project_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["name"] == "Resume Chatbot"
        assert data["type"] == "web"
        assert isinstance(data["highlights"], list)
        assert len(data["highlights"]) == 3


@pytest.mark.asyncio
async def test_projects_server_get_by_id_not_found():
    """Test getting non-existent project"""
    with patch('mcp_servers.projects_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.projects_server import call_tool
        
        result = await call_tool("get_project_by_id", {"id": 999})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "not found" in data["error"].lower()


@pytest.mark.asyncio
async def test_projects_server_get_all():
    """Test getting all projects"""
    with patch('mcp_servers.projects_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_project1 = Project(
            id=1,
            name="Resume Chatbot",
            description="AI-powered resume assistant",
            highlights="FastAPI|ChromaDB|RAG",
            start_date="2023-01",
            end_date="2023-12",
            url="https://github.com/user/resume-chatbot",
            type="web",
            entity="Personal",
            roles="Developer|Architect"
        )
        mock_project2 = Project(
            id=2,
            name="E-commerce Platform",
            description="Online store",
            highlights="React|Node.js|MongoDB",
            start_date="2022-01",
            end_date="2022-12",
            url="https://github.com/user/ecommerce",
            type="web",
            entity="Freelance",
            roles="Full Stack Developer"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_project1, mock_project2]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.projects_server import call_tool
        
        result = await call_tool("get_all_projects", {})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "projects" in data
        assert len(data["projects"]) == 2
        assert data["projects"][0]["name"] == "Resume Chatbot"
        assert data["projects"][1]["name"] == "E-commerce Platform"


@pytest.mark.asyncio
async def test_projects_server_search():
    """Test searching projects"""
    with patch('mcp_servers.projects_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_project = Project(
            id=1,
            name="Resume Chatbot",
            description="AI-powered resume assistant",
            highlights="FastAPI|ChromaDB|RAG",
           
            
start_date="2023-01",
            end_date="2023-12",
            url="https://github.com/user/resume-chatbot",
            type="web",
            entity="Personal",
            roles="Developer|Architect"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_project]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.projects_server import call_tool
        
        result = await call_tool("search_projects", {"query": "resume"})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "projects" in data
        assert len(data["projects"]) == 1
        assert data["projects"][0]["name"] == "Resume Chatbot"


@pytest.mark.asyncio
async def test_projects_server_unknown_tool():
    """Test calling unknown tool"""
    from mcp_servers.projects_server import call_tool
    
    result = await call_tool("unknown_tool", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "error" in data
    assert "unknown" in data["error"].lower()


@pytest.mark.asyncio
async def test_projects_server_empty_highlights():
    """Test project with empty highlights"""
    with patch('mcp_servers.projects_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_project = Project(
            id=1,
            name="Resume Chatbot",
            description="AI-powered resume assistant",
            highlights=None,
            start_date="2023-01",
            end_date="2023-12",
            url="https://github.com/user/resume-chatbot",
            type="web",
            entity="Personal",
            roles=None
        )
        mock_result.scalar_one_or_none.return_value = mock_project
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.projects_server import call_tool
        
        result = await call_tool("get_project_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["highlights"] == []
        assert data["roles"] == []
