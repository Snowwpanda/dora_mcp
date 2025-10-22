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
        from starlette.responses import Response, StreamingResponse
        import json
        
        sse = SseServerTransport("/messages")
        
        # Check if streamable transport is available
        try:
            from mcp.server.streamable import StreamableServerTransport
            streamable_available = True
        except ImportError:
            streamable_available = False
            logger.warning("Streamable transport not available in current MCP SDK version")
        
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
                    "/mcp": "POST - MCP Streamable endpoint (for Microsoft Copilot Studio)",
                    "/api/search": "POST - Search DORA publications (REST API)",
                    "/sse": "Server-Sent Events endpoint (deprecated for Copilot Studio)",
                    "/messages": "POST endpoint for MCP JSON-RPC messages"
                },
                "mcp_protocol": "2024-11-05",
                "copilot_studio": {
                    "endpoint": "/mcp",
                    "protocol": "mcp-streamable-1.0",
                    "openapi_spec": "/openapi.json"
                },
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
        
        async def search_api_endpoint(request):
            """REST API endpoint for searching publications (for Copilot Studio)."""
            if request.method != "POST":
                return JSONResponse(
                    {"error": "Method not allowed. Use POST."},
                    status_code=405
                )
            
            try:
                body = await request.json()
                search_string = body.get("search_string")
                
                if not search_string:
                    return JSONResponse(
                        {"error": "search_string is required"},
                        status_code=400
                    )
                
                # Perform the search
                results = await search_dora_publications(search_string)
                
                return JSONResponse({
                    "search_string": search_string,
                    "results": results,
                    "total": len(results) if isinstance(results, list) else 0
                })
                
            except Exception as e:
                logger.error(f"Error in search API: {e}")
                return JSONResponse(
                    {"error": str(e)},
                    status_code=500
                )
        
        async def openapi_endpoint(request):
            """Serve OpenAPI specification in Swagger 2.0 format.
            
            Includes both:
            - /mcp endpoint for Copilot Studio (MCP Streamable)
            - /api/search endpoint for Power Automate (REST API)
            """
            # Determine host and scheme from request
            host = request.url.hostname or "localhost"
            if request.url.port and request.url.port not in (80, 443):
                host = f"{host}:{request.url.port}"
            scheme = "https" if request.url.scheme == "https" else "http"
            
            return JSONResponse({
                "swagger": "2.0",
                "info": {
                    "title": "DORA Publications API",
                    "version": "1.0.0",
                    "description": "Search the DORA (Digital Open Research Archive) for academic publications and research papers. Supports both MCP protocol (Copilot Studio) and REST API (Power Automate)."
                },
                "host": host,
                "basePath": "/",
                "schemes": [scheme],
                "consumes": ["application/json"],
                "produces": ["application/json"],
                "paths": {
                    "/api/search": {
                        "post": {
                            "summary": "Search publications",
                            "description": "Search DORA for academic publications by author name, title, keywords, or other criteria. Returns formatted citations with DOI and object URLs.",
                            "operationId": "SearchPublications",
                            "consumes": ["application/json"],
                            "produces": ["application/json"],
                            "parameters": [{
                                "name": "body",
                                "in": "body",
                                "description": "Search parameters",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "required": ["search_string"],
                                    "properties": {
                                        "search_string": {
                                            "type": "string",
                                            "description": "Search query for publications (author name, title keywords, research topics, etc.)",
                                            "x-ms-summary": "Search Query"
                                        }
                                    }
                                }
                            }],
                            "responses": {
                                "200": {
                                    "description": "Successful search",
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "search_string": {
                                                "type": "string",
                                                "description": "The search query that was executed"
                                            },
                                            "total": {
                                                "type": "integer",
                                                "description": "Total number of publications found"
                                            },
                                            "results": {
                                                "type": "array",
                                                "description": "List of publications matching the search criteria",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "citation": {
                                                            "type": "string",
                                                            "description": "Formatted citation in ACS style"
                                                        },
                                                        "doi": {
                                                            "type": "string",
                                                            "description": "DOI URL for the publication"
                                                        },
                                                        "object_url": {
                                                            "type": "string",
                                                            "description": "Direct link to the publication in DORA repository"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                "400": {
                                    "description": "Bad request - missing or invalid search_string"
                                },
                                "500": {
                                    "description": "Internal server error"
                                }
                            }
                        }
                    },
                    "/mcp": {
                        "post": {
                            "summary": "MCP Streamable endpoint (Copilot Studio)",
                            "description": "Model Context Protocol endpoint for Microsoft Copilot Studio integration using JSON-RPC 2.0 protocol",
                            "x-ms-agentic-protocol": "mcp-streamable-1.0",
                            "operationId": "InvokeMCP",
                            "consumes": ["application/json"],
                            "produces": ["application/json"],
                            "parameters": [{
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "jsonrpc": {
                                            "type": "string",
                                            "enum": ["2.0"]
                                        },
                                        "id": {
                                            "type": "integer"
                                        },
                                        "method": {
                                            "type": "string",
                                            "enum": ["initialize", "tools/list", "tools/call"]
                                        },
                                        "params": {
                                            "type": "object"
                                        }
                                    }
                                }
                            }],
                            "responses": {
                                "200": {
                                    "description": "JSON-RPC 2.0 response",
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    },
                    "/health": {
                        "get": {
                            "summary": "Health check",
                            "description": "Check if the server is running and healthy",
                            "operationId": "HealthCheck",
                            "produces": ["application/json"],
                            "responses": {
                                "200": {
                                    "description": "Server is healthy",
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {
                                                "type": "string",
                                                "enum": ["healthy"]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            })
        
        async def mcp_streamable_endpoint(request):
            """MCP Streamable HTTP endpoint for Copilot Studio."""
            if request.method != "POST":
                return JSONResponse(
                    {"error": "Method not allowed. Use POST."},
                    status_code=405
                )
            
            try:
                # Read the JSON-RPC request
                body = await request.json()
                
                # Handle MCP protocol messages
                if body.get("method") == "tools/list":
                    tools = await list_tools()
                    response = {
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "result": {
                            "tools": [
                                {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "inputSchema": tool.inputSchema
                                }
                                for tool in tools
                            ]
                        }
                    }
                    return JSONResponse(response)
                
                elif body.get("method") == "tools/call":
                    params = body.get("params", {})
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    result = await call_tool(tool_name, arguments)
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": content.type,
                                    "text": content.text
                                }
                                for content in result
                            ]
                        }
                    }
                    return JSONResponse(response)
                
                elif body.get("method") == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "dora-mcp",
                                "version": "1.0.0"
                            }
                        }
                    }
                    return JSONResponse(response)
                
                else:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {body.get('method')}"
                        }
                    })
                    
            except Exception as e:
                logger.error(f"Error in MCP streamable endpoint: {e}")
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": body.get("id") if "body" in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }, status_code=500)
        
        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/", endpoint=root_endpoint),
                Route("/health", endpoint=health_endpoint),
                Route("/tools", endpoint=tools_endpoint),
                Route("/api/search", endpoint=search_api_endpoint, methods=["POST"]),
                Route("/openapi.json", endpoint=openapi_endpoint),
                Route("/mcp", endpoint=mcp_streamable_endpoint, methods=["POST"]),  # Copilot Studio MCP endpoint
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
