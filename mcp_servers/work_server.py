"""
MCP Server for Work model - Read-only operations
"""
from typing import Any, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.work import Work
from app.db.session import get_async_session

app = Server("resume-work-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_work_by_id",
            description="Get work experience by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Work experience ID"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="get_all_work",
            description="Get all work experiences",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_work",
            description="Search work experiences by company or position",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (company name or position)"
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
            if name == "get_work_by_id":
                work_id = arguments["id"]
                result = await session.execute(select(Work).where(Work.id == work_id))
                work = result.scalar_one_or_none()
                
                if work:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "id": work.id,
                            "company": work.name,
                            "position": work.position,
                            "summary": work.summary,
                            "highlights": work.highlights.split("|") if work.highlights else [],
                            "start_date": work.start_date,
                            "end_date": work.end_date,
                            "url": work.url,
                            "location": work.location
                        }, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "Work experience not found"}, indent=2)
                    )]
            
            elif name == "get_all_work":
                result = await session.execute(select(Work))
                works = result.scalars().all()
                
                work_list = []
                for work in works:
                    work_list.append({
                        "id": work.id,
                        "company": work.name,
                        "position": work.position,
                        "summary": work.summary,
                        "highlights": work.highlights.split("|") if work.highlights else [],
                        "start_date": work.start_date,
                        "end_date": work.end_date,
                        "url": work.url,
                        "location": work.location
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"work_experiences": work_list}, indent=2)
                )]
            
            elif name == "search_work":
                query = arguments["query"].lower()
                result = await session.execute(
                    select(Work).where(
                        (Work.name.ilike(f"%{query}%")) | 
                        (Work.position.ilike(f"%{query}%"))
                    )
                )
                works = result.scalars().all()
                
                work_list = []
                for work in works:
                    work_list.append({
                        "id": work.id,
                        "company": work.name,
                        "position": work.position,
                        "summary": work.summary,
                        "highlights": work.highlights.split("|") if work.highlights else [],
                        "start_date": work.start_date,
                        "end_date": work.end_date,
                        "url": work.url,
                        "location": work.location
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"work_experiences": work_list}, indent=2)
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
