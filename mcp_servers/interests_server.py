"""
MCP Server for Interests model - Read-only operations
"""
from typing import Any, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.interest import Interest
from app.db.session import get_async_session

app = Server("resume-interests-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_interest_by_id",
            description="Get interest by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Interest ID"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="get_all_interests",
            description="Get all interests",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_interests",
            description="Search interests by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (interest name)"
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
            if name == "get_interest_by_id":
                interest_id = arguments["id"]
                result = await session.execute(select(Interest).where(Interest.id == interest_id))
                interest = result.scalar_one_or_none()
                
                if interest:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "id": interest.id,
                            "name": interest.name,
                            "keywords": interest.keywords.split("|") if interest.keywords else []
                        }, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "Interest not found"}, indent=2)
                    )]
            
            elif name == "get_all_interests":
                result = await session.execute(select(Interest))
                interests = result.scalars().all()
                
                interest_list = []
                for interest in interests:
                    interest_list.append({
                        "id": interest.id,
                        "name": interest.name,
                        "keywords": interest.keywords.split("|") if interest.keywords else []
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"interests": interest_list}, indent=2)
                )]
            
            elif name == "search_interests":
                query = arguments["query"].lower()
                result = await session.execute(
                    select(Interest).where(Interest.name.ilike(f"%{query}%"))
                )
                interests = result.scalars().all()
                
                interest_list = []
                for interest in interests:
                    interest_list.append({
                        "id": interest.id,
                        "name": interest.name,
                        "keywords": interest.keywords.split("|") if interest.keywords else []
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"interests": interest_list}, indent=2)
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

if __name__ == "__main__":    asyncio.run(main())
