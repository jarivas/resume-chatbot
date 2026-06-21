"""
MCP Server for Skills model - Read-only operations
"""
from typing import Any, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.skill import Skill
from app.db.session import get_async_session

app = Server("resume-skills-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_skill_by_id",
            description="Get skill by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Skill ID"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="get_all_skills",
            description="Get all skills",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_skills",
            description="Search skills by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (skill name)"
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
            if name == "get_skill_by_id":
                skill_id = arguments["id"]
                result = await session.execute(select(Skill).where(Skill.id == skill_id))
                skill = result.scalar_one_or_none()
                
                if skill:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "id": skill.id,
                            "name": skill.name,
                            "level": skill.level,
                            "keywords": skill.keywords.split("|") if skill.keywords else []
                        }, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "Skill not found"}, indent=2)
                    )]
            
            elif name == "get_all_skills":
                result = await session.execute(select(Skill))
                skills = result.scalars().all()
                
                skill_list = []
                for skill in skills:
                    skill_list.append({
                        "id": skill.id,
                        "name": skill.name,
                        "level": skill.level,
                        "keywords": skill.keywords.split("|") if skill.keywords else []
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"skills": skill_list}, indent=2)
                )]
            
            elif name == "search_skills":
                query = arguments["query"].lower()
                result = await session.execute(
                    select(Skill).where(Skill.name.ilike(f"%{query}%"))
                )
                skills = result.scalars().all()
                
                skill_list = []
                for skill in skills:
                    skill_list.append({
                        "id": skill.id,
                        "name": skill.name,
                        "level": skill.level,
                        "keywords": skill.keywords.split("|") if skill.keywords else []
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"skills": skill_list}, indent=2)
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
