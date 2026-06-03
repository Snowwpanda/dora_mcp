"""MCP server for DORA (Digital Object Repository for Academia) publications.

Exposes tools for searching publications and retrieving abstracts.
Supports both stdio and HTTP (Streamable) transports.
"""

import logging
import os
import re
from typing import Any
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DORA API base URL
DORA_BASE_URL = "https://www.dora.lib4ri.ch/empa"
DORA_SEARCH_ENDPOINT = f"{DORA_BASE_URL}/islandora/search/json_cit_a"

# DORA admin backend — serves classic server-rendered Islandora HTML (stable, no JS required)
DORA_ADMIN_BASE_URL = "https://admin.dora.lib4ri.ch"

# DORA GraphQL API — fallback for abstract fetching if admin HTML scraping fails
DORA_GRAPHQL_URL = "https://apollo-prod.lib4ri.ch"
DORA_GET_ITEM_QUERY = """
query GetItem($subsite: Subsite!, $pid: ID!) {
  item(subsite: $subsite, pid: $pid) {
    ... on Item {
      info {
        pid
        title
        abstract
        url
      }
    }
  }
}
"""


def build_admin_url(publication_id: str) -> str:
    """Build the admin-backend URL for a publication (server-rendered HTML)."""
    subsite = publication_id.split(':')[0] if ':' in publication_id else 'empa'
    return f"{DORA_ADMIN_BASE_URL}/{subsite}/islandora/object/{publication_id}"

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


def extract_publication_id(identifier_or_url: str) -> str:
    """Extract publication ID from URL or identifier.
    
    Args:
        identifier_or_url: Either a full URL like
                          'https://www.dora.lib4ri.ch/empa/item/empa:27842' or
                          'https://www.dora.lib4ri.ch/empa/item/empa:27842'
                          or just an identifier like 'empa:27842'
    
    Returns:
        Publication ID (e.g., 'empa:27842')
    """
    if identifier_or_url.startswith("http"):
        # New URL format: /item/empa:27842
        match = re.search(r'/item/([^/\s?#]+)', identifier_or_url)
        if match:
            return match.group(1)
        # Legacy URL format: /object/empa:27842
        match = re.search(r'/object/([^/\s?#]+)', identifier_or_url)
        if match:
            return match.group(1)
        raise ValueError(f"Could not extract publication ID from URL: {identifier_or_url}")
    
    # If it already looks like an ID (contains ':'), return as-is
    if ':' in identifier_or_url:
        return identifier_or_url
    
    raise ValueError(f"Invalid identifier or URL format: {identifier_or_url}")


def build_publication_url(publication_id: str) -> str:
    """Build the full DORA URL for a publication.
    
    Args:
        publication_id: Publication identifier (e.g., 'empa:27842')
    
    Returns:
        Full URL to the publication page
    """
    # Extract the subsite prefix (e.g. 'empa' from 'empa:27842')
    subsite = publication_id.split(':')[0] if ':' in publication_id else 'empa'
    return f"https://www.dora.lib4ri.ch/{subsite}/item/{publication_id}"


async def search_dora_publications(search_string: str, limit: int = 20) -> dict[str, Any]:
    """Search DORA for publications.
    
    Args:
        search_string: The search term to query
        limit: Maximum number of results to return (default 20)
        
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
    
    logger.info(f"Searching DORA for: {search_string} (limit: {limit})")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            results = response.json()
            
            # Apply limit if results is a list or contains a list
            if isinstance(results, list):
                return results[:limit]
            elif isinstance(results, dict) and "results" in results:
                # Some API versions might return a dict with a results list
                if isinstance(results["results"], list):
                    results["results"] = results["results"][:limit]
                return results
            
            return results
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise


async def get_publication_page(identifier_or_url: str) -> str:
    """Fetch the HTML content of a publication page.
    
    Args:
        identifier_or_url: Either a full URL or publication identifier
    
    Returns:
        HTML content of the publication page
    """
    publication_id = extract_publication_id(identifier_or_url)
    url = build_publication_url(publication_id)
    
    logger.info(f"Fetching publication page: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise


async def get_publication_abstract(identifier_or_url: str) -> dict[str, Any]:
    """Get the abstract of a publication.

    Primary: scrapes the admin backend (server-rendered Islandora HTML).
    Fallback: DORA GraphQL API.

    Args:
        identifier_or_url: Either a full URL or publication identifier

    Returns:
        Dictionary with publication_id, url, abstract_text, and abstract_html
    """
    publication_id = extract_publication_id(identifier_or_url)
    public_url = build_publication_url(publication_id)
    admin_url = build_admin_url(publication_id)

    # --- Primary: scrape admin Islandora HTML ---
    try:
        logger.info(f"Fetching abstract for {publication_id} from admin HTML")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(admin_url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        abstract_elem = soup.find('p', property='description')
        if abstract_elem:
            return {
                "publication_id": publication_id,
                "url": public_url,
                "abstract_text": abstract_elem.get_text(strip=True),
                "abstract_html": str(abstract_elem),
            }
        logger.warning(f"Abstract element not found in admin HTML for {publication_id}, trying GraphQL")
    except Exception as e:
        logger.warning(f"Admin HTML fetch failed for {publication_id}: {e}, trying GraphQL")

    # --- Fallback: GraphQL API ---
    subsite = publication_id.split(':')[0] if ':' in publication_id else 'empa'
    logger.info(f"Fetching abstract for {publication_id} via GraphQL fallback")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                DORA_GRAPHQL_URL,
                json={
                    'operationName': 'GetItem',
                    'query': DORA_GET_ITEM_QUERY,
                    'variables': {'subsite': subsite, 'pid': publication_id}
                },
                headers={'apollo-require-preflight': 'true'}
            )
            response.raise_for_status()
            data = response.json()

        if 'errors' not in data:
            info = (data.get('data', {}).get('item') or {}).get('info')
            if info and info.get('abstract'):
                return {
                    "publication_id": publication_id,
                    "url": info.get('url') or public_url,
                    "abstract_text": info['abstract'],
                    "abstract_html": None,
                }
    except Exception as e:
        logger.error(f"GraphQL fallback also failed for {publication_id}: {e}")

    return {
        "publication_id": publication_id,
        "url": public_url,
        "abstract_text": None,
        "abstract_html": None,
        "error": "Abstract not found via admin HTML or GraphQL"
    }


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
                "matching the search criteria. "
                "IMPORTANT: Use SHORT KEYWORDS or AUTHOR NAMES, not long phrases. "
                "Examples: 'climate change', 'machine learning', 'John Smith'. "
                "Avoid using full sentences or questions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "search_string": {
                        "type": "string",
                        "description": (
                            "SHORT search keywords or author name. "
                            "Use 1-3 keywords maximum, NOT full sentences. "
                            "Good examples: 'manfred heuberger', 'polymer coating', 'tribology'. "
                            "Bad examples: 'find papers about machine learning applications', "
                            "'what are the latest studies on climate change'."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default 20).",
                        "default": 20,
                    },
                },
                "required": ["search_string"],
            },
        ),
        Tool(
            name="get_publication_abstract",
            description=(
                "Retrieve the abstract of a specific publication from DORA. "
                "Requires either the full publication URL (e.g., "
                "'https://www.dora.lib4ri.ch/empa/item/empa:27842') "
                "or just the publication identifier (e.g., 'empa:27842'). "
                "Returns both HTML-formatted and plain text versions of the abstract."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "identifier_or_url": {
                        "type": "string",
                        "description": (
                            "Either the full DORA publication URL "
                            "(e.g., 'https://www.dora.lib4ri.ch/empa/item/empa:27842') "
                            "or just the publication identifier (e.g., 'empa:27842')."
                        ),
                    },
                },
                "required": ["identifier_or_url"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "search_publications":
            search_string = arguments.get("search_string")
            limit = arguments.get("limit", 20)
            if not search_string:
                raise ValueError("search_string is required")
            
            results = await search_dora_publications(search_string, limit=limit)
            
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
        
        elif name == "get_publication_abstract":
            identifier_or_url = arguments.get("identifier_or_url")
            if not identifier_or_url:
                raise ValueError("identifier_or_url is required")
            
            result = await get_publication_abstract(identifier_or_url)
            
            # Format the response
            if result.get("error"):
                response_text = f"Error retrieving abstract:\n{result['error']}\n\n"
                response_text += f"Publication URL: {result['url']}"
            else:
                response_text = f"Abstract for {result['publication_id']}:\n\n"
                response_text += f"URL: {result['url']}\n\n"
                response_text += f"Abstract (plain text):\n{result['abstract_text']}\n\n"
                response_text += f"Abstract (HTML):\n{result['abstract_html']}"
            
            return [
                TextContent(
                    type="text",
                    text=response_text,
                )
            ]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        error_msg = f"Error executing tool '{name}': {str(e)}"
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
    # Default is now 'http'
    transport = os.getenv("MCP_TRANSPORT", "http").lower()
    
    if transport == "stdio":
        logger.info("Starting DORA MCP server in stdio mode...")
        async with stdio_server() as (read_stream, write_stream):
            logger.info("DORA MCP server is ready and listening for requests")
            await app.run(read_stream, write_stream, app.create_initialization_options())
        return

    # HTTP mode (default) with Streamable transport
    host = os.getenv("MCP_HOST", "localhost")
    port = int(os.getenv("MCP_PORT", "8000"))
    
    logger.info(f"Starting DORA MCP server in HTTP mode on {host}:{port}")
    
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse
    from starlette.middleware.cors import CORSMiddleware
    
    # Simple REST endpoints for convenience
    async def root_endpoint(request):
        """Root endpoint — human-friendly landing page."""
        import pathlib
        from starlette.responses import HTMLResponse
        base = str(request.base_url).rstrip("/")
        template = (
            pathlib.Path(__file__).parent / "templates" / "index.html"
        ).read_text(encoding="utf-8")
        html = template.replace("__BASE_URL__", base)
        return HTMLResponse(html)
    
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
            limit = body.get("limit", 20)
            
            if not search_string:
                return JSONResponse(
                    {"error": "search_string is required"},
                    status_code=400
                )
            
            # Perform the search
            results = await search_dora_publications(search_string, limit=limit)
            
            # Calculate total count correctly
            total_count = 0
            if isinstance(results, list):
                total_count = len(results)
            elif isinstance(results, dict) and "results" in results:
                total_count = len(results["results"])
            
            return JSONResponse({
                "search_string": search_string,
                "results": results,
                "total": total_count
            })
            
        except Exception as e:
            logger.error(f"Error in search API: {e}")
            return JSONResponse(
                {"error": str(e)},
                status_code=500
            )
    
    async def abstract_api_endpoint(request):
        """REST API endpoint for retrieving a publication abstract."""
        try:
            body = await request.json()
            identifier_or_url = body.get("identifier_or_url")

            if not identifier_or_url:
                return JSONResponse(
                    {"error": "identifier_or_url is required"},
                    status_code=400
                )

            result = await get_publication_abstract(identifier_or_url)
            return JSONResponse(result)

        except Exception as e:
            logger.error(f"Error in abstract API: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

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
            
            logger.info(f"Received MCP request: method={body.get('method')}, id={body.get('id')}")
            
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
                logger.info(f"Returning {len(tools)} tools")
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
                logger.info("Handling initialize request")
                tools = await list_tools()
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
                        },
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
                logger.info("Initialize successful")
                return JSONResponse(response)
            
            # Handle notifications/initialized (client acknowledgment, no response needed)
            elif body.get("method") == "notifications/initialized":
                logger.info("Received initialized notification")
                # Notifications don't require a response
                return JSONResponse({"jsonrpc": "2.0"}, status_code=200)
            
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
    
    async def swagger_ui_endpoint(request):
        """Serve Swagger UI for interactive API documentation."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DORA Publications API - Swagger UI</title>
            <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
            <style>
                body { margin: 0; padding: 0; }
            </style>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
            <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
            <script>
                window.onload = function() {
                    // Use a relative path to the openapi.yaml
                    const specUrl = window.location.origin + "/api/openapi.yaml?v=" + Date.now();
                    SwaggerUIBundle({
                        url: specUrl,
                        dom_id: '#swagger-ui',
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIStandalonePreset
                        ],
                        layout: "BaseLayout",
                        deepLinking: true,
                        showExtensions: true,
                        showCommonExtensions: true
                    });
                };
            </script>
        </body>
        </html>
        """
        from starlette.responses import HTMLResponse
        return HTMLResponse(html)
    
    async def serve_yaml_file(request):
        """Serve YAML files from the api/ directory."""
        from starlette.responses import Response, FileResponse, JSONResponse
        import pathlib
        import re

        # Get filename from path params
        filename = request.path_params.get("filename", "")
        if not filename:
            return JSONResponse({"error": "No filename provided"}, status_code=400)

        # Ensure it ends with .yaml
        if not filename.endswith(".yaml"):
            filename = f"{filename}.yaml"
        
        # Extract just the filename to look in the api/ directory
        bare_filename = pathlib.Path(filename).name
        
        # This file is at /app/src/dora_mcp/server.py or ./src/dora_mcp/server.py
        current_file = pathlib.Path(__file__).resolve()
        
        # Possible locations for 'api' folder
        search_paths = [
            current_file.parent.parent.parent / "api", # src/../.. -> project root
            current_file.parent.parent / "api",        # dora_mcp/.. -> src/
            pathlib.Path.cwd() / "api",                # current dir
            pathlib.Path.cwd(),                        # current dir itself
        ]
        
        file_path = None
        for path in search_paths:
            candidate = path / bare_filename
            if candidate.exists():
                file_path = candidate
                break

        if not file_path:
            logger.error(f"YAML file not found. Searched: {[str(p/bare_filename) for p in search_paths]}")
            return JSONResponse(
                {"error": f"File not found: {bare_filename}", "searched_paths": [str(p/bare_filename) for p in search_paths]},
                status_code=404
            )

        # For openapi.yaml, we remove 'host' and 'schemes' so that Swagger UI
        # automatically uses the current host/scheme it's being accessed from.
        # This is more robust for Docker, Fly.io, and local dev.
        if bare_filename == "openapi.yaml":
            content = file_path.read_text(encoding="utf-8")
            # Remove host line
            content = re.sub(r"^host:.*$\n?", "", content, flags=re.MULTILINE)
            # Remove schemes block
            content = re.sub(r"^schemes:.*?(?=^\S)", "", content, flags=re.MULTILINE | re.DOTALL)
            
            return Response(
                content=content,
                media_type="application/x-yaml",
                headers={"Content-Disposition": f'inline; filename="{bare_filename}"'},
            )

        return FileResponse(
            file_path,
            media_type="application/x-yaml",
            filename=bare_filename,
        )
    
    starlette_app = Starlette(
        debug=os.getenv("MCP_DEBUG", "false").lower() == "true",
        routes=[
            Route("/", endpoint=root_endpoint),
            Route("/docs", endpoint=swagger_ui_endpoint),
            Route("/health", endpoint=health_endpoint),
            Route("/tools", endpoint=tools_endpoint),
            Route("/api/search", endpoint=search_api_endpoint, methods=["POST"]),
            Route("/api/abstract", endpoint=abstract_api_endpoint, methods=["POST"]),
            Route("/mcp", endpoint=mcp_streamable_endpoint, methods=["GET", "POST"]),
            Route("/api/{filename:path}", endpoint=serve_yaml_file),
            Route("/{filename:path}.yaml", endpoint=serve_yaml_file),
        ],
    )
    
    # Add CORS middleware for Copilot Studio compatibility
    starlette_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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


def run():
    """Synchronous entry point for the MCP server."""
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
