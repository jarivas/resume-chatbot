"""
MCP Server for Education model - Read-only operations
"""
from typing import Any, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.education import Education
from app.db.session import get_async_session

app = Server("resume-education-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_education_by_id",
            description="Get education by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Education ID"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="get_all_education",
            description="Get all education entries",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_education",
            description="Search education by institution or area",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (institution or area of study)"
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
            if name == "get_education_by_id":
                edu_id = arguments["id"]
                result = await session.execute(select(Education).where(Education.id == edu_id))
                edu = result.scalar_one_or_none()
                
                if edu:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "id": edu.id,
                            "institution": edu.institution,
                            "area": edu.area,
                            "study_type": edu.study_type,
                            "start_date": edu.start_date,
                            "end_date": edu.end_date,
                            "score": edu.score,
                            "courses": edu.courses.split("|") if edu.courses else [],
                            "url": edu.url
                        }, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "Education not found"}, indent=2)
                    )]
            
            elif name == "get_all_education":
                result = await session.execute(select(Education))
                educations = result.scalars().all()
                
                edu_list = []
                for edu in educations:
                    edu_list.append({
                        "id": edu.id,
                        "institution": edu.institution,
                        "area": edu.area,
                        "study_type": edu.study_type,
                        "start_date": edu.start_date,
                        "end_date": edu.end_date,
                        "score": edu.score,
                        "courses": edu.courses.split("|") if edu.courses else [],
                        "url": edu.url
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"education": edu_list}, indent=2)
                )]
            
            elif name == "search_education":
                query = arguments["query"].lower()
                result = await session.execute(
                    select(Education).where(
                        (Education.institution.ilike(f"%{query}%")) | 
                        (Education.area.ilike(f"%{query}%"))
                    )
                )
                educations = result.scalars().all()
                
                edu_list = []
                for edu in educations:
                    edu_list.append({
                        "id": edu.id,
                        "institution": edu.institution,
                        "area": edu.area,
                        "study_type": edu.study_type,
                        "start_date": edu.start_date,
                        "end_date": edu.end_date,
                        "score": edu.score,
                        "courses": edu.courses.split("|") if edu.courses else [],
                        "url": edu.url
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"education": edu_list}, indent=2)
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
