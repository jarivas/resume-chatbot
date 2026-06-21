"""
Tests for Certificates MCP Server
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.certificate import Certificate


@pytest.mark.asyncio
async def test_certificates_server_list_tools():
    """Test that certificates server lists correct tools"""
    with patch('mcp_servers.certificates_server.app') as mock_app:
        from mcp_servers.certificates_server import list_tools
        
        tools = await list_tools()
        
        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "get_certificate_by_id" in tool_names
        assert "get_all_certificates" in tool_names
        assert "search_certificates" in tool_names


@pytest.mark.asyncio
async def test_certificates_server_get_by_id():
    """Test getting certificate by ID"""
    with patch('mcp_servers.certificates_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_cert = Certificate(
            id=1,
            name="AWS Certified Developer",
            date="2023-06",
            issuer="Amazon Web Services",
            url="https://aws.amazon.com/certification"
        )
        mock_result.scalar_one_or_none.return_value = mock_cert
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.certificates_server import call_tool
        
        result = await call_tool("get_certificate_by_id", {"id": 1})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["name"] == "AWS Certified Developer"
        assert data["issuer"] == "Amazon Web Services"


@pytest.mark.asyncio
async def test_certificates_server_get_by_id_not_found():
    """Test getting non-existent certificate"""
    with patch('mcp_servers.certificates_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.certificates_server import call_tool
        
        result = await call_tool("get_certificate_by_id", {"id": 999})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "not found" in data["error"].lower()


@pytest.mark.asyncio
async def test_certificates_server_get_all():
    """Test getting all certificates"""
    with patch('mcp_servers.certificates_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_cert1 = Certificate(
            id=1,
            name="AWS Certified Developer",
            date="2023-06",
            issuer="Amazon Web Services",
            url="https://aws.amazon.com/certification"
        )
        mock_cert2 = Certificate(
            id=2,
            name="Google Cloud Professional",
            date="2023-08",
            issuer="Google Cloud",
            url="https://cloud.google.com/certification"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_cert1, mock_cert2]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.certificates_server import call_tool
        
        result = await call_tool("get_all_certificates", {})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "certificates" in data
        assert len(data["certificates"]) == 2
        assert data["certificates"][0]["name"] == "AWS Certified Developer"
        assert data["certificates"][1]["name"] == "Google Cloud Professional"


@pytest.mark.asyncio
async def test_certificates_server_search():
    """Test searching certificates"""
    with patch('mcp_servers.certificates_server.get_async_session') as mock_session_gen:
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_gen.return_value = [mock_session]
        
        mock_cert = Certificate(
            id=1,
            name="AWS Certified Developer",
            date="2023-06",
            issuer="Amazon Web Services",
            url="https://aws.amazon.com/certification"
        )
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_cert]
        mock_session.execute.return_value = mock_result
        
        from mcp_servers.certificates_server import call_tool
        
        result = await call_tool("search_certificates", {"query": "aws"})
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "certificates" in data
        assert len(data["certificates"]) == 1
        assert data["certificates"][0]["name"] == "AWS Certified Developer"


@pytest.mark.asyncio
async def test_certificates_server_unknown_toolkit():
    """Test calling unknown tool"""
    from mcp_servers.certificates_server import call_tool
    
    result = await call_tool("unknown_tool", {})
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "error" in data
    assert "unknown" in data["error"].lower()
