"""
Pytest fixtures for MCP server tests
"""
import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


@pytest.fixture
def mock_mcp_app():
    """Mock MCP app fixture"""
    from unittest.mock import MagicMock
    return MagicMock()


@pytest.fixture
def mock_async_session():
    """Mock async session fixture"""
    from unittest.mock import AsyncMock, MagicMock
    from sqlalchemy.ext.asyncio import AsyncSession
    
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def mock_db_result():
    """Mock database result fixture"""
    from unittest.mock import MagicMock
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    return mock_result
