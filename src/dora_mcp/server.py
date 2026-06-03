"""MCP server for DORA (Digital Object Repository for Academia) publications."""

import logging
import os
import re
# import base64  # Disabled: was only used for get_publication_fulltext
from typing import Any
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

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
        Dictionary with publication_id, url, and abstract
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
                "abstract": abstract_elem.get_text(strip=True),
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
                    "abstract": info['abstract'],
                }
    except Exception as e:
        logger.error(f"GraphQL fallback also failed for {publication_id}: {e}")

    return {
        "publication_id": publication_id,
        "url": public_url,
        "abstract": None,
        "error": "Abstract not found via admin HTML or GraphQL"
    }


# DISABLED: Payload too large for MCP protocol
# async def get_publication_fulltext(identifier_or_url: str) -> dict[str, Any]:
#     """Get the fulltext PDF document of a publication.
#     
#     Args:
#         identifier_or_url: Either a full URL or publication identifier
#     
#     Returns:
#         Dictionary with publication_id, url, pdf_url, and pdf_content (bytes)
#     """
#     publication_id = extract_publication_id(identifier_or_url)
#     html_content = await get_publication_page(identifier_or_url)
#     
#     soup = BeautifulSoup(html_content, 'html.parser')
#     
#     # Find the "Published Version" link
#     pdf_link = None
#     for link in soup.find_all('a'):
#         if link.get_text(strip=True) == "Published Version":
#             pdf_link = link.get('href')
#             break
#     
#     if not pdf_link:
#         return {
#             "publication_id": publication_id,
#             "url": build_publication_url(publication_id),
#             "pdf_url": None,
#             "pdf_content": None,
#             "error": "Published Version link not found on page"
#         }
#     
#     # Make sure the PDF URL is absolute
#     if pdf_link.startswith('/'):
#         pdf_link = f"https://www.dora.lib4ri.ch{pdf_link}"
#     elif not pdf_link.startswith('http'):
#         pdf_link = f"{DORA_BASE_URL}/{pdf_link}"
#     
#     # Download the PDF content
#     logger.info(f"Downloading PDF from: {pdf_link}")
#     try:
#         async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for PDF downloads
#             pdf_response = await client.get(pdf_link)
#             pdf_response.raise_for_status()
#             pdf_content = pdf_response.content
#             
#             logger.info(f"Successfully downloaded PDF ({len(pdf_content)} bytes)")
#             
#             return {
#                 "publication_id": publication_id,
#                 "url": build_publication_url(publication_id),
#                 "pdf_url": pdf_link,
#                 "pdf_content": pdf_content,
#                 "pdf_size_bytes": len(pdf_content)
#             }
#     except httpx.HTTPError as e:
#         logger.error(f"Failed to download PDF: {e}")
#         return {
#             "publication_id": publication_id,
#             "url": build_publication_url(publication_id),
#             "pdf_url": pdf_link,
#             "pdf_content": None,
#             "error": f"Failed to download PDF: {str(e)}"
#         }


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
        # DISABLED: Payload too large for MCP protocol
        # Tool(
        #     name="get_publication_fulltext",
        #     description=(
        #         "Retrieve and download the full text PDF of a specific publication from DORA. "
        #         "Requires either the full publication URL (e.g., "
        #         "'https://www.dora.lib4ri.ch/empa/islandora/object/empa:27842') "
        #         "or just the publication identifier (e.g., 'empa:27842'). "
        #         "Returns the complete PDF document encoded as base64, along with the PDF URL and size. "
        #         "The PDF can be decoded from base64 and saved as a binary file."
        #     ),
        #     inputSchema={
        #         "type": "object",
        #         "properties": {
        #             "identifier_or_url": {
        #                 "type": "string",
        #                 "description": (
        #                     "Either the full DORA publication URL "
        #                     "(e.g., 'https://www.dora.lib4ri.ch/empa/islandora/object/empa:27842') "
        #                     "or just the publication identifier (e.g., 'empa:27842')."
        #                 ),
        #             },
        #         },
        #         "required": ["identifier_or_url"],
        #     },
        # ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "search_publications":
            search_string = arguments.get("search_string")
            if not search_string:
                raise ValueError("search_string is required")
            
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
        
        # DISABLED: Payload too large for MCP protocol
        # elif name == "get_publication_fulltext":
        #     identifier_or_url = arguments.get("identifier_or_url")
        #     if not identifier_or_url:
        #         raise ValueError("identifier_or_url is required")
        #     
        #     result = await get_publication_fulltext(identifier_or_url)
        #     
        #     # Format the response
        #     if result.get("error"):
        #         response_text = f"Error retrieving PDF:\n{result['error']}\n\n"
        #         response_text += f"Publication URL: {result['url']}"
        #         if result.get('pdf_url'):
        #             response_text += f"\nPDF URL: {result['pdf_url']}"
        #     else:
        #         # Encode PDF content as base64 for safe transmission
        #         pdf_base64 = base64.b64encode(result['pdf_content']).decode('utf-8')
        #         
        #         response_text = f"Full text PDF for {result['publication_id']}:\n\n"
        #         response_text += f"Publication URL: {result['url']}\n"
        #         response_text += f"PDF URL: {result['pdf_url']}\n"
        #         response_text += f"PDF Size: {result['pdf_size_bytes']:,} bytes\n\n"
        #         response_text += f"PDF Content (base64 encoded):\n{pdf_base64}\n\n"
        #         response_text += f"Note: The PDF is base64 encoded. To use it, decode the base64 string back to binary."
        #     
        #     return [
        #         TextContent(
        #             type="text",
        #             text=response_text,
        #         )
        #     ]
        
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
                        SwaggerUIBundle({
                            url: "/api/openapi.yaml?v=" + Date.now(),
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
            """Serve YAML files, injecting the current Host into openapi.yaml."""
            from starlette.responses import Response, FileResponse
            import pathlib
            import re

            # Get the requested file path (add .yaml extension)
            filename = request.path_params.get("filename", "openapi")
            if not filename.endswith(".yaml"):
                filename = f"{filename}.yaml"

            # YAML files live in api/ at the project root
            project_root = pathlib.Path(__file__).parent.parent.parent
            # Strip any leading api/ prefix so both /openapi.yaml and /api/openapi.yaml work
            bare_filename = filename.removeprefix("api/").removeprefix("api\\")
            file_path = project_root / "api" / bare_filename

            if not file_path.exists():
                return JSONResponse(
                    {"error": f"File not found: {filename}"},
                    status_code=404
                )

            # For openapi.yaml, replace the host and schemes fields with the actual
            # request values so Swagger UI and any client use the correct server automatically.
            if bare_filename == "openapi.yaml":
                request_host = request.headers.get("host", "localhost")
                request_scheme = request.url.scheme  # "http" or "https"
                content = file_path.read_text(encoding="utf-8")
                content = re.sub(
                    r"^host:.*$",
                    f"host: {request_host}",
                    content,
                    flags=re.MULTILINE,
                )
                content = re.sub(
                    r"^schemes:.*?(?=^\S)",
                    f"schemes:\n  - {request_scheme}\n",
                    content,
                    flags=re.MULTILINE | re.DOTALL,
                )
                return Response(
                    content=content,
                    media_type="application/x-yaml",
                    headers={"Content-Disposition": f'inline; filename="{filename}"'},
                )

            return FileResponse(
                file_path,
                media_type="application/x-yaml",
                filename=filename,
            )
        
        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/", endpoint=root_endpoint),
                Route("/docs", endpoint=swagger_ui_endpoint),
                Route("/health", endpoint=health_endpoint),
                Route("/tools", endpoint=tools_endpoint),
                Route("/api/search", endpoint=search_api_endpoint, methods=["POST"]),
                Route("/api/abstract", endpoint=abstract_api_endpoint, methods=["POST"]),
                Route("/mcp", endpoint=mcp_streamable_endpoint, methods=["GET", "POST"]),
                Route("/{filename:path}.yaml", endpoint=serve_yaml_file),  # Serve YAML files
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
    else:
        # stdio mode (default)
        logger.info("Starting DORA MCP server in stdio mode...")
        async with stdio_server() as (read_stream, write_stream):
            logger.info("DORA MCP server is ready and listening for requests")
            await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
