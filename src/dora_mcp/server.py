"""MCP server for DORA (Digital Object Repository for Academia) publications."""

import logging
import os
from typing import Any
from urllib.parse import quote

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DORA API base URL
DORA_BASE_URL = "https://www.dora.lib4ri.ch/empa"
DORA_SEARCH_ENDPOINT = f"{DORA_BASE_URL}/islandora/search/json_cit_a"

# MCP Server instance
app = Server("dora-mcp")


def build_search_query(search_string: str) -> str:
    """Build the DORA search query string.
    
    Args:
        search_string: The search term to query
        
    Returns:
        URL-encoded query string for DORA API
    """
    # Build the query parts - searching across multiple fields with different weights
    query_parts = [
        f"mods_titleInfo_title_mt:({search_string})^5",
        f"mods_abstract_ms:({search_string})^2",
        f"dc.creator:({search_string})^2",
        f"mods_extension_originalAuthorList_mt:({search_string})^2",
        f"dc.contributor:({search_string})^1",
        f"dc.type:({search_string})^1",
        f"catch_all_MODS_mt:({search_string})^1",
    ]
    
    return "%20OR%20".join([quote(part) for part in query_parts])


async def search_dora_publications(search_string: str) -> dict[str, Any]:
    """Search DORA for publications.
    
    Args:
        search_string: The search term to query
        
    Returns:
        JSON response from DORA API containing publication results
    """
    query = build_search_query(search_string)
    
    # Build the full URL
    url = f"{DORA_SEARCH_ENDPOINT}/{query}"
    params = {
        "search_string": search_string,
        "extension": "false"
    }
    
    logger.info(f"Searching DORA for: {search_string}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_publications",
            description=(
                "Search the DORA (Digital Object Repository for Academia) database "
                "for scientific publications. Searches across titles, abstracts, "
                "authors, and other metadata fields. Returns a list of publications "
                "matching the search criteria."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "search_string": {
                        "type": "string",
                        "description": (
                            "The search term to query. Can be an author name, "
                            "title keyword, or any search term. Example: 'manfred heuberger'"
                        ),
                    },
                },
                "required": ["search_string"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    if name != "search_publications":
        raise ValueError(f"Unknown tool: {name}")
    
    search_string = arguments.get("search_string")
    if not search_string:
        raise ValueError("search_string is required")
    
    try:
        results = await search_dora_publications(search_string)
        
        # Format the results
        if isinstance(results, dict):
            # Extract relevant information if available
            response_text = f"Search results for '{search_string}':\n\n"
            response_text += f"Raw JSON response:\n{results}"
        else:
            response_text = f"Search results for '{search_string}':\n{results}"
        
        return [
            TextContent(
                type="text",
                text=response_text,
            )
        ]
    except Exception as e:
        error_msg = f"Error searching DORA: {str(e)}"
        logger.error(error_msg)
        return [
            TextContent(
                type="text",
                text=error_msg,
            )
        ]


async def main():
    """Run the MCP server."""
    # Check if we should run in HTTP mode or stdio mode
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    
    if transport == "http":
        # HTTP/SSE mode
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8000"))
        
        logger.info(f"Starting DORA MCP server in HTTP mode on {host}:{port}")
        
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route
        from starlette.responses import Response
        
        sse = SseServerTransport("/messages")
        
        #  Create raw ASGI apps that can be mounted
        class SSEApp:
            """ASGI app for SSE endpoint."""
            async def __call__(self, scope, receive, send):
                async with sse.connect_sse(scope, receive, send) as streams:
                    await app.run(
                        streams[0], streams[1], app.create_initialization_options()
                    )
        
        class MessagesApp:
            """ASGI app for messages endpoint."""
            async def __call__(self, scope, receive, send):
                await sse.handle_post_message(scope, receive, send)
        
        from starlette.routing import Mount, Route
        from starlette.responses import JSONResponse
        
        # Simple REST endpoints for convenience
        async def root_endpoint(request):
            """Root endpoint with API documentation."""
            return JSONResponse({
                "service": "DORA MCP Server",
                "version": "1.0.0",
                "description": "Model Context Protocol server for DORA (Digital Object Repository for Academia)",
                "transport": "http",
                "endpoints": {
                    "/": "API documentation (this page)",
                    "/health": "Health check",
                    "/tools": "List available MCP tools",
                    "/sse": "Server-Sent Events endpoint for MCP client connections",
                    "/messages": "POST endpoint for MCP JSON-RPC messages"
                },
                "mcp_protocol": "2024-11-05",
                "documentation": "https://github.com/Snowwpanda/dora_mcp"
            })
        
        async def health_endpoint(request):
            """Health check endpoint."""
            return JSONResponse({
                "status": "healthy",
                "service": "dora-mcp",
                "transport": "http",
                "endpoints": {
                    "sse": "/sse",
                    "messages": "/messages",
                    "health": "/health",
                    "tools": "/tools"
                }
            })
        
        async def tools_endpoint(request):
            """List available tools as JSON."""
            tools = await list_tools()
            tools_data = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ]
            return JSONResponse({
                "tools": tools_data
            })
        
        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/", endpoint=root_endpoint),
                Route("/health", endpoint=health_endpoint),
                Route("/tools", endpoint=tools_endpoint),
                Mount("/sse", app=SSEApp()),
                Mount("/messages", app=MessagesApp()),
            ],
        )
        
        import uvicorn
        logger.info(f"DORA MCP server is ready at http://{host}:{port}")
        logger.info(f"SSE endpoint: http://{host}:{port}/sse")
        logger.info(f"Messages endpoint: http://{host}:{port}/messages")
        
        config = uvicorn.Config(starlette_app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    else:
        # stdio mode (default)
        logger.info("Starting DORA MCP server in stdio mode...")
        async with stdio_server() as (read_stream, write_stream):
            logger.info("DORA MCP server is ready and listening for requests")
            await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
