"""
MCP Server for Publications model - Read-only operations
"""
from typing import Any, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.publication import Publication
from app.db.session import get_async_session

app = Server("resume-publications-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_publication_by_id",
            description="Get publication by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Publication ID"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="get_all_publications",
            description="Get all publications",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_publications",
            description="Search publications by title",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (publication title)"
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
            if name == "get_publication_by_id":
                pub_id = arguments["id"]
                result = await session.execute(select(Publication).where(Publication.id == pub_id))
                pub = result.scalar_one_or_none()
                
                if pub:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "id": pub.id,
                            "name": pub.name,
                            "publisher": pub.publisher,
                            "release_date": pub.release_date,
                            "url": pub.url,
                            "summary": pub.summary
                        }, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "Publication not found"}, indent=2)
                    )]
            
            elif name == "get_all_publications":
                result = await session.execute(select(Publication))
                publications = result.scalars().all()
                
                pub_list = []
                for pub in publications:
                    pub_list.append({
                        "id": pub.id,
                        "name": pub.name,
                        "publisher": pub.publisher,
                        "release_date": pub.release_date,
                        "url": pub.url,
                        "summary": pub.summary
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"publications": pub_list}, indent=2)
                )]
            
            elif name == "search_publications":
                query = arguments["query"].lower()
                result = await session.execute(
                    select(Publication).where(Publication.name.ilike(f"%{query}%"))
                )
                publications = result.scalars().all()
                
                pub_list = []
                for pub in publications:
                    pub_list.append({
                        "id": pub.id,
                        "name": pub.name,
                        "publisher": pub.publisher,
                        "release_date": pub.release_date,
                        "url": pub.url,
                        "summary": pub.summary
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"publications": pub_list}, indent=2)
                )]
        
        finally:
            await session.close()
    
    return [TextContent(
        type="text",
        text=json.dumps({"error": "Unknown tool"}, indent=2)
    )]

async def main():
    async with stdio_server() as (r
