"""
MCP Server for References model - Read-only operations
"""
from typing import Any, List
from mcp.server import Server
from mcp.server.stdio import
 stdio_server
from mcp.types import Tool, TextContent
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.reference import Reference
from app.db.session import get_async_session

app = Server("resume-references-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_reference_by_id",
            description="Get reference by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Reference ID"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="get_all_references",
            description="Get all references",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_references",
            description="Search references by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (reference name)"
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
            if name == "get_reference_by_id":
                ref_id = arguments["id"]
                result = await session.execute(select(Reference).where(Reference.id == ref_id))
                ref = result.scalar_one_or_none()
                
                if ref:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "id": ref.id,
                            "name": ref.name,
                            "reference": ref.reference,
                            "relationship": ref.relationship,
                            "email": ref.email,
                            "phone": ref.phone,
                            "location": ref.location
                        }, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "Reference not found"}, indent=2)
                    )]
            
            elif name == "get_all_references":
                result = await session.execute(select(Reference))
                references = result.scalars().all()
                
                ref_list = []
                for ref in references:
                    ref_list.append({
                        "id": ref.id,
                        "name": ref.name,
                        "reference": ref.reference,
                        "relationship": ref.relationship,
                        "email": ref.email,
                        "phone": ref.phone,
                        "location": ref.location
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"references": ref_list}, indent=2)
                )]
            
            elif name == "search_references":
                query = arguments["query"].lower()
                result = await session.execute(
                    select(Reference).where(Reference.name.ilike(f"%{query}%"))
                )
                references = result.scalars().all()
                
                ref_list = []
                for ref in references:
                    ref_list.append({
                        "id": ref.id,
                        "name": ref.name,
                        "reference": ref.reference,
                        "relationship": ref.relationship,
                        "email": ref.email,
                        "phone": ref.phone,
                        "location": ref.location
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"references": ref_list}, indent=2)
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
