"""
MCP Server for Languages model - Read-only operations
"""
from typing import Any, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.language import Language
from app.db.session import get_async_session

app = Server("resume-languages-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_language_by_id",
            description="Get language by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Language ID"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="get_all_languages",
            description="Get all languages",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_languages",
            description="Search languages by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (language name)"
                    }
                },
                "required": ["query"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    async for session in get_async_session():
        try:
            if name == "get_language_by_id":
                lang_id = arguments["id"]
                result = await session.execute(select(Language).where(Language.id == lang_id))
                lang = result.scalar_one_or_none()
                
                if lang:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "id": lang.id,
                            "language": lang.language,
                            "fluency": lang.fluency
                        }, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "Language not found"}, indent=2)
                    )]
            
            elif name == "get_all_languages":
                result = await session.execute(select(Language))
                languages = result.scalars().all()
                
                lang_list = []
                for lang in languages:
                    lang_list.append({
                        "id": lang.id,
                        "language": lang.language,
                        "fluency": lang.fluency
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"languages": lang_list}, indent=2)
                )]
            
            elif name == "search_languages":
                query = arguments["query"].lower()
                result = await session.execute(
                    select(Language).where(Language.language.ilike(f"%{query}%"))
                )
               
