"""
MCP Server for Certificates model - Read-only operations
"""
from typing import Any, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.certificate import Certificate
from app.db.session import get_async_session

app = Server("resume-certificates-server")

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_certificate_by_id",
            description="Get certificate by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "Certificate ID"
                    }
                },
                "required": ["id"]
            }
        ),
        Tool(
            name="get_all_certificates",
            description="Get all certificates",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_certificates",
            description="Search certificates by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (certificate name)"
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
            if name == "get_certificate_by_id":
                cert_id = arguments["id"]
                result = await session.execute(select(Certificate).where(Certificate.id == cert_id))
                cert = result.scalar_one_or_none()
                
                if cert:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "id": cert.id,
                            "name": cert.name,
                            "date": cert.date,
                            "issuer": cert.issuer,
                            "url": cert.url
                        }, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "Certificate not found"}, indent=2)
                    )]
            
            elif name == "get_all_certificates":
                result = await session.execute(select(Certificate))
                certificates = result.scalars().all()
                
                cert_list = []
                for cert in certificates:
                    cert_list.append({
                        "id": cert.id,
                        "name": cert.name,
                        "date": cert.date,
                        "issuer": cert.issuer,
                        "url": cert.url
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"certificates": cert_list}, indent=2)
                )]
            
            elif name == "search_certificates":
                query = arguments["query"].lower()
                result = await session.execute(
                    select(Certificate).where(Certificate.name.ilike(f"%{query}%"))
                )
                certificates = result.scalars().all()
                
                cert_list = []
                for cert in certificates:
                    cert_list.append({
                        "id": cert.id,
                        "name": cert.name,
                        "date": cert.date,
                        "issuer": cert.issuer,
                        "url": cert.url
                    })
                
                return [TextContent(
                    type="text",
                    text=json.dumps({"certificates": cert_list}, indent=2)
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
