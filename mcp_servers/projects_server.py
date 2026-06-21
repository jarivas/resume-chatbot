"""
MCP Server Server for Projects model - Read-only operations
"""
from typing import Any, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.project import Project
from app.db.session import get_async_session

app = Server("resume-projects-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_project_by_id",
            description="Get project by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Project ID"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="get_all_projects",
            description="Get all projects",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_projects",
            description="Search projects by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (project name)"
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
            if name == "get_project_by_id":
                project_id = arguments["id"]
                result = await session.execute(select(Project).where(Project.id == project_id))
                project = result.scalar_one_or_none()
                
                if project:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "id": project.id,
                            "name": project.name,
                            "description": project.description,
                            "highlights": project.highlights.split("|") if project.highlights else [],
                            "start_date": project.start_date,
                            "end_date": project.end_date,
                            "url": project.url,
                            "type": project.type,
                            "entity": project.entity,
                            "roles": project.roles.split("|") if project.roles else []
                        }, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "Project not found"}, indent=2)
                    )]
            
            elif name == "get_all_projects":
                result = await session.execute(select(Project))
                projects = result.scalars().all()
                
                project_list = []
                for project in projects:
                    project_list.append({
                        "id": project.id,
                        "name": project.name,
                        "description": project.description,
                        "highlights": project.highlights.split("|") if project.highlights else [],
                        "start_date": project.start_date,
                        "end_date": project.end_date,
                        "url": project.url,
                        "type": project.type,
                        "entity": project.entity,
                        "roles": project.roles.split("|") if project.roles else []
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"projects": project_list}, indent=2)
                )]
            
            elif name == "search_projects":
                query = arguments["query"].lower()
                result = await session.execute(
                    select(Project).where(Project.name.ilike(f"%{query}%"))
                )
                projects = result.scalars().all()
                
                project_list = []
                for project in projects:
                    project_list.append({
                        "id": project.id,
                        "name": project.name,
                        "description": project.description,
                        "highlights": project.highlights.split("|") if project.highlights else [],
                        "start_date": project.start_date,
                        "end_date": project.end_date,
                        "url": project.url,
                        "type": project.type,
                        "entity": project.entity,
                        "roles": project.roles.split("|") if project.roles else []
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"projects": project_list}, indent=2)
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
