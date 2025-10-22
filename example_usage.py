#!/usr/bin/env python3
"""Example usage of DORA MCP server client."""

import asyncio
from dora_mcp.server import DoraClient


async def main():
    """Demonstrate DORA client usage."""
    client = DoraClient()

    try:
        print("=" * 60)
        print("DORA MCP Server - Example Usage")
        print("=" * 60)

        # Example 1: Search publications by year
        print("\n1. Searching publications from 2018...")
        print("-" * 60)
        print("URL: https://www.dora.lib4ri.ch/empa/islandora/search/json_cit_a/*:*")
        print("Filter: mods_originInfo_encoding_w3cdtf_keyDate_yes_dateIssued_dt:[2018-01-01T00:00:00Z TO 2018-12-31T23:59:59Z]")
        print("\nNote: Actual API call would be made here if network is available.")

        # Example 2: Search publications by date range
        print("\n2. Searching publications from 2020-01-01 to 2020-06-30...")
        print("-" * 60)
        print("URL: https://www.dora.lib4ri.ch/empa/islandora/search/json_cit_a/*:*")
        print("Filter: mods_originInfo_encoding_w3cdtf_keyDate_yes_dateIssued_dt:[2020-01-01T00:00:00Z TO 2020-06-30T23:59:59Z]")
        print("\nNote: Actual API call would be made here if network is available.")

        # Example 3: Custom search
        print("\n3. Custom search with query '*:*'...")
        print("-" * 60)
        print("URL: https://www.dora.lib4ri.ch/empa/islandora/search/json_cit_a/*:*")
        print("\nNote: Actual API call would be made here if network is available.")

        print("\n" + "=" * 60)
        print("Examples complete!")
        print("=" * 60)
        print("\nTo use this server with an MCP client:")
        print("1. Add the server to your MCP client configuration")
        print("2. Use the tools: search_publications, search_by_year, search_by_date_range")
        print("\nSee example_config.json for configuration details.")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
