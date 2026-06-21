"""
MCP Server for Volunteer model - Read-only operations
"""
from typing import Any, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.volunteer import Volunteer
from app.db.session import get_async_session

app = Server("resume-volunteer-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_volunteer_by_id",
            description="Get volunteer experience by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Volunteer experience ID"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="get_all_volunteer",
            description="Get all volunteer experiences",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_volunteer",
            description="Search volunteer experiences by organization",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (organization name)"
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
            if name == "get_volunteer_by_id":
                vol_id = arguments["id"]
                result = await session.execute(select(Volunteer).where(Volunteer.id == vol_id))
                vol = result.scalar_one_or_none()
                
                if vol:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "id": vol.id,
                            "organization": vol.organization,
                            "position": vol.position,
                            "summary": vol.summary,
                            "highlights": vol.highlights.split("|") if vol.highlights else [],
                            "start_date": vol.start_date,
                            "end_date": vol.end_date,
                            "url": vol.url
                        }, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "Volunteer experience not found"}, indent=2)
                    )]
            
            elif name == "get_all_volunteer":
                result = await session.execute(select(Volunteer))
                volunteers = result.scalars().all()
                
                vol_list = []
                for vol in volunteers:
                    vol_list.append({
                        "id": vol.id,
                        "organization": vol.organization,
                        "position": vol.position,
                        "summary": vol.summary,
                        "highlights": vol.highlights.split("|") if vol.highlights else [],
                        "start_date": vol.start_date,
                        "end_date": vol.end_date,
                        "url": vol.url
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"volunteer_experiences": vol_list}, indent=2)
                )]
            
            elif name == "search_volunteer":
                query = arguments["query"].lower()
                result = await session.execute(
                    select(Volunteer).where(Volunteer.organization.ilike(f"%{query}%"))
                )
                volunteers = result.scalars().all()
                
                vol_list = []
                for vol in volunteers:
                    vol_list.append({
                        "id": vol.id,
                        "organization": vol.organization,
                        "position": vol.position,
                        "summary": vol.summary,
                        "highlights": vol.highlights.split("|") if vol.highlights else [],
                        "start_date": vol.start_date,
                        "end_date": vol.end_date,
                        "url": vol.url
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"volunteer_experiences": vol_list}, indent=2)
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
