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
        # HTTP mode with Streamable transport
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8000"))
        
        logger.info(f"Starting DORA MCP server in HTTP mode on {host}:{port}")
        
        from starlette.applications import Starlette
        from starlette.routing import Route
        from starlette.responses import JSONResponse
        from starlette.middleware.cors import CORSMiddleware
        import json
        
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
                    "/connector": "POST - Power Automate custom connector endpoint (recommended)",
                    "/openapi.json": "OpenAPI spec for general REST API",
                    "/openapi-connector.json": "OpenAPI spec for Power Automate connector (recommended)",
                    "/openapi-copilot.json": "OpenAPI spec for Copilot Studio (MCP protocol)",
                    "/openapi-minimal.json": "Minimal OpenAPI spec for Copilot Studio (following Microsoft example)"
                },
                "mcp_protocol": "2024-11-05",
                "copilot_studio": {
                    "endpoint": "/mcp",
                    "protocol": "mcp-streamable-1.0",
                    "openapi_spec": "/openapi-copilot.json",
                    "documentation": "See COPILOT_STUDIO.md"
                },
                "power_automate": {
                    "endpoint": "/connector",
                    "protocol": "REST API",
                    "openapi_spec": "/openapi-connector.json",
                    "note": "Use /connector endpoint and /openapi-connector.json spec for Power Automate custom connectors"
                },
                "documentation": "https://github.com/Snowwpanda/dora_mcp"
            })
        
        async def health_endpoint(request):
            """Health check endpoint."""
            return JSONResponse({
                "status": "healthy",
                "service": "dora-mcp",
                "transport": "http-streamable"
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
        
        async def connector_endpoint(request):
            """Dedicated connector endpoint for Power Automate.
            
            This is a simple, clean endpoint designed specifically for Power Automate
            custom connectors, with no MCP-related complexity.
            """
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
                        {"error": "search_string parameter is required"},
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
                logger.error(f"Error in connector endpoint: {e}")
                return JSONResponse(
                    {"error": str(e)},
                    status_code=500
                )
        
        async def connector_openapi_endpoint(request):
            """Serve OpenAPI specification for the /connector endpoint.
            
            This is a minimal, focused spec for Power Automate with only
            the connector endpoint - no MCP, no health checks, nothing else.
            """
            # Determine host and scheme from request
            host = request.url.hostname or "localhost"
            if request.url.port and request.url.port not in (80, 443):
                host = f"{host}:{request.url.port}"
            scheme = "https" if request.url.scheme == "https" else "http"
            
            return JSONResponse({
                "swagger": "2.0",
                "info": {
                    "title": "DORA Publications Search",
                    "version": "1.0.0",
                    "description": "Search the DORA (Digital Open Research Archive) for academic publications and research papers."
                },
                "host": host,
                "basePath": "/",
                "schemes": [scheme],
                "consumes": ["application/json"],
                "produces": ["application/json"],
                "paths": {
                    "/connector": {
                        "post": {
                            "summary": "Search DORA publications",
                            "description": "Search for academic publications by author name, title, keywords, or research topics. Returns formatted citations with DOI links and DORA repository URLs.",
                            "operationId": "SearchPublications",
                            "consumes": ["application/json"],
                            "produces": ["application/json"],
                            "parameters": [{
                                "name": "body",
                                "in": "body",
                                "description": "Search request",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "required": ["search_string"],
                                    "properties": {
                                        "search_string": {
                                            "type": "string",
                                            "description": "Search query (author name, title keywords, research topics, etc.)",
                                            "x-ms-summary": "Search Query",
                                            "example": "climate change"
                                        }
                                    }
                                }
                            }],
                            "responses": {
                                "200": {
                                    "description": "Search completed successfully",
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "search_string": {
                                                "type": "string",
                                                "description": "The search query that was executed",
                                                "x-ms-summary": "Search Query"
                                            },
                                            "total": {
                                                "type": "integer",
                                                "description": "Total number of publications found",
                                                "x-ms-summary": "Total Results"
                                            },
                                            "results": {
                                                "type": "array",
                                                "description": "List of publications",
                                                "x-ms-summary": "Publications",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "citation": {
                                                            "type": "string",
                                                            "description": "Formatted citation (ACS style)",
                                                            "x-ms-summary": "Citation"
                                                        },
                                                        "doi": {
                                                            "type": "string",
                                                            "description": "DOI URL",
                                                            "x-ms-summary": "DOI"
                                                        },
                                                        "object_url": {
                                                            "type": "string",
                                                            "description": "DORA repository link",
                                                            "x-ms-summary": "DORA URL"
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
                    }
                }
            })
        
        async def openapi_power_automate_endpoint(request):
            """Serve OpenAPI specification for Power Automate.
            
            Only includes REST API endpoints compatible with Power Automate.
            Does NOT include /mcp endpoint (use /openapi-copilot.json for that).
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
                    "description": "Search the DORA (Digital Open Research Archive) for academic publications and research papers via REST API."
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
        
        async def openapi_copilot_endpoint(request):
            """Serve OpenAPI specification for Copilot Studio.
            
            Includes MCP Streamable endpoint with x-ms-agentic-protocol.
            """
            # Determine host and scheme from request
            host = request.url.hostname or "localhost"
            if request.url.port and request.url.port not in (80, 443):
                host = f"{host}:{request.url.port}"
            scheme = "https" if request.url.scheme == "https" else "http"
            
            return JSONResponse({
                "swagger": "2.0",
                "info": {
                    "title": "DORA MCP Server",
                    "version": "1.0.0",
                    "description": "Model Context Protocol server for DORA publications (Copilot Studio)"
                },
                "host": host,
                "basePath": "/",
                "schemes": [scheme],
                "consumes": ["application/json"],
                "produces": ["application/json"],
                "paths": {
                    "/mcp": {
                        "post": {
                            "summary": "MCP Streamable endpoint",
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
                    }
                }
            })
        
        async def openapi_minimal_endpoint(request):
            """Serve minimal OpenAPI specification for Copilot Studio.
            
            This is the absolute minimal spec following Microsoft's example.
            """
            # Determine host and scheme from request
            host = request.url.hostname or "localhost"
            if request.url.port and request.url.port not in (80, 443):
                host = f"{host}:{request.url.port}"
            scheme = "https" if request.url.scheme == "https" else "http"
            
            return JSONResponse({
                "swagger": "2.0",
                "info": {
                    "title": "DORA Publications MCP Server",
                    "description": "MCP server for searching DORA (Digital Object Repository for Academia) publications",
                    "version": "1.0.0"
                },
                "host": host,
                "basePath": "/",
                "schemes": [scheme],
                "paths": {
                    "/mcp": {
                        "post": {
                            "summary": "DORA Publications Search Server",
                            "x-ms-agentic-protocol": "mcp-streamable-1.0",
                            "operationId": "InvokeMCP",
                            "responses": {
                                "200": {
                                    "description": "Success"
                                }
                            }
                        }
                    }
                }
            })
        
        async def mcp_streamable_endpoint(request):
            """MCP Streamable HTTP endpoint for Copilot Studio."""
            # Handle GET requests - return instructions
            if request.method == "GET":
                tools = await list_tools()
                return JSONResponse({
                    "message": "DORA MCP Server",
                    "version": "1.0.0",
                    "description": "MCP server for searching scientific publications in the DORA (Digital Object Repository for Academia) database",
                    "usage": {
                        "note": "This endpoint uses the MCP (Model Context Protocol) with Streamable transport",
                        "method": "POST",
                        "protocol": "mcp-streamable-1.0",
                        "content_type": "application/json",
                        "instructions": [
                            "Send POST requests with JSON-RPC 2.0 format",
                            "Include method and params in request body",
                            "Supported methods: initialize, tools/list, tools/call"
                        ]
                    },
                    "available_tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in tools
                    ],
                    "documentation": "https://github.com/Snowwpanda/dora_mcp"
                }, status_code=200)
            
            # Only POST is allowed for MCP protocol
            if request.method != "POST":
                return JSONResponse(
                    {"error": "Method not allowed. This endpoint requires POST requests with MCP protocol."},
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
                Route("/connector", endpoint=connector_endpoint, methods=["POST"]),  # Power Automate connector
                Route("/openapi.json", endpoint=openapi_power_automate_endpoint),  # Power Automate (legacy)
                Route("/openapi-connector.json", endpoint=connector_openapi_endpoint),  # Power Automate connector spec
                Route("/openapi-copilot.json", endpoint=openapi_copilot_endpoint),  # Copilot Studio (detailed)
                Route("/openapi-minimal.json", endpoint=openapi_minimal_endpoint),  # Copilot Studio (minimal)
                Route("/mcp", endpoint=mcp_streamable_endpoint, methods=["GET", "POST"]),  # Copilot Studio MCP endpoint
            ],
        )
        
        # Add CORS middleware for Copilot Studio compatibility
        starlette_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, restrict this to Copilot Studio domains
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        import uvicorn
        logger.info(f"DORA MCP server is ready at http://{host}:{port}")
        logger.info(f"MCP Streamable endpoint: http://{host}:{port}/mcp")
        logger.info(f"Health check: http://{host}:{port}/health")
        
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
