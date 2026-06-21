"""
MCP Server for Awards model - Read-only operations
"""
from typing import Any, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.award import Award
from app.db.session import get_async_session

app = Server("resume-awards-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_award_by_id",
            description="Get award by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Award ID"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="get_all_awards",
            description="Get all awards",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_awards",
            description="Search awards by title",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (award title)"
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
            if name == "get_award_by_id":
                award_id = arguments["id"]
                result = await session.execute(select(Award).where(Award.id == award_id))
                award = result.scalar_one_or_none()
                
                if award:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "id": award.id,
                            "title": award.title,
                            "date": award.date,
                            "awarder": award.awarder,
                            "summary": award.summary,
                            "url": award.url
                        }, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "Award not found"}, indent=2)
                    )]
            
            elif name == "get_all_awards":
                result = await session.execute(select(Award))
                awards = result.scalars().all()
                
                award_list = []
                for award in awards:
                    award_list.append({
                        "id": award.id,
                        "title": award.title,
                        "date": award.date,
                        "awarder": award.awarder,
                        "summary": award.summary,
                        "url": award.url
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"awards": award_list}, indent=2)
                )]
            
            elif name == "search_awards":
                query = arguments["query"].lower()
                result = await session.execute(
                    select(Award).where(Award.title.ilike(f"%{query}%"))
                )
                awards = result.scalars().all()
                
                award_list = []
                for award in awards:
                    award_list.append({
                        "id": award.id,
                        "title": award.title,
                        "date": award.date,
                        "awarder": award.awarder,
                        "summary": award.summary,
                        "url": award.url
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"awards": award_list}, indent=2)
                )]
        
        finally:
            await session.close()
    
    return [TextContent(
        type="text",
            text=json.dumps({"error": "Unknown tool"}, indent=2)
    )]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
