"""MCP Server for DORA publication repository."""

import asyncio
import logging
from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DORA base URL
DORA_BASE_URL = "https://www.dora.lib4ri.ch/empa/islandora/search/json_cit_a"


class DoraClient:
    """Client for interacting with DORA API."""

    def __init__(self, base_url: str = DORA_BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def search_publications(
        self,
        query: str = "*:*",
        filters: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Search for publications in DORA.

        Args:
            query: Search query (default: "*:*" for all)
            filters: List of filter strings

        Returns:
            JSON response from DORA API
        """
        # Encode the query
        encoded_query = quote(query, safe=":")

        # Build URL
        url = f"{self.base_url}/{encoded_query}"

        # Add filters if provided
        params = {}
        if filters:
            for i, filter_str in enumerate(filters):
                params[f"f[{i}]"] = filter_str

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise
        except Exception as e:
            logger.error(f"Error searching publications: {e}")
            raise

    async def search_by_year(self, year: int) -> dict[str, Any]:
        """
        Search for publications by year.

        Args:
            year: Year to search for (e.g., 2018)

        Returns:
            JSON response from DORA API
        """
        # Build date filter
        start_date = f"{year}-01-01T00:00:00Z"
        end_date = f"{year}-12-31T23:59:59Z"
        date_filter = (
            f"mods_originInfo_encoding_w3cdtf_keyDate_yes_dateIssued_dt:"
            f"[{start_date} TO {end_date}]"
        )

        return await self.search_publications(filters=[date_filter])

    async def search_by_date_range(
        self, start_date: str, end_date: str
    ) -> dict[str, Any]:
        """
        Search for publications by date range.

        Args:
            start_date: Start date in ISO format (e.g., "2018-01-01")
            end_date: End date in ISO format (e.g., "2018-12-31")

        Returns:
            JSON response from DORA API
        """
        # Convert dates to ISO format with time
        start_iso = f"{start_date}T00:00:00Z"
        end_iso = f"{end_date}T23:59:59Z"

        date_filter = (
            f"mods_originInfo_encoding_w3cdtf_keyDate_yes_dateIssued_dt:"
            f"[{start_iso} TO {end_iso}]"
        )

        return await self.search_publications(filters=[date_filter])


# Create the MCP server
app = Server("dora-mcp")
dora_client = DoraClient()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_publications",
            description=(
                "Search for publications in the DORA repository. "
                "Supports custom queries and filters."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (default: '*:*' for all publications)",
                        "default": "*:*",
                    },
                    "filters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of filter strings",
                    },
                },
            },
        ),
        Tool(
            name="search_by_year",
            description="Search for publications by a specific year.",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer",
                        "description": "Year to search for (e.g., 2018)",
                    },
                },
                "required": ["year"],
            },
        ),
        Tool(
            name="search_by_date_range",
            description="Search for publications within a date range.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in ISO format (e.g., '2018-01-01')",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in ISO format (e.g., '2018-12-31')",
                    },
                },
                "required": ["start_date", "end_date"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "search_publications":
            query = arguments.get("query", "*:*")
            filters = arguments.get("filters")
            result = await dora_client.search_publications(query, filters)
            return [
                TextContent(
                    type="text",
                    text=f"Search results:\n{result}",
                )
            ]

        elif name == "search_by_year":
            year = arguments["year"]
            result = await dora_client.search_by_year(year)
            return [
                TextContent(
                    type="text",
                    text=f"Publications from {year}:\n{result}",
                )
            ]

        elif name == "search_by_date_range":
            start_date = arguments["start_date"]
            end_date = arguments["end_date"]
            result = await dora_client.search_by_date_range(start_date, end_date)
            return [
                TextContent(
                    type="text",
                    text=f"Publications from {start_date} to {end_date}:\n{result}",
                )
            ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [
            TextContent(
                type="text",
                text=f"Error: {str(e)}",
            )
        ]


async def main():
    """Run the MCP server."""
    logger.info("Starting DORA MCP server...")
    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options(),
            )
    finally:
        await dora_client.close()


if __name__ == "__main__":
    asyncio.run(main())
