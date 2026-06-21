"""
MCP Servers for Resume Chatbot

This package contains MCP (Model Context Protocol) servers for read-only
access to all database models in the Resume Chatbot application.

Available Servers:
MCP servers provide tools for:
- Getting entities by ID
- Getting all entities
- Searching entities by relevant fields

Usage:
    python -m mcp_servers.work_server
    python -m mcp_servers.education_server
    # ... etc

Each server runs as a standalone MCP server that can be connected to
from MCP-compatible clients.
"""

__version__ = "0.1.0"
