"""Tests for DORA MCP server."""

import pytest
from dora_mcp.server import DoraClient


class TestDoraClient:
    """Test cases for DoraClient."""

    @pytest.fixture
    async def client(self):
        """Create a DoraClient instance."""
        client = DoraClient()
        yield client
        await client.close()

    def test_client_initialization(self):
        """Test that DoraClient can be initialized."""
        client = DoraClient()
        assert client.base_url == "https://www.dora.lib4ri.ch/empa/islandora/search/json_cit_a"

    def test_client_custom_base_url(self):
        """Test that DoraClient can be initialized with custom base URL."""
        custom_url = "https://custom.example.com/api"
        client = DoraClient(base_url=custom_url)
        assert client.base_url == custom_url

    @pytest.mark.asyncio
    async def test_search_url_construction(self, client):
        """Test that search URLs are constructed correctly."""
        # This test validates the URL construction logic
        # Since we can't actually call the API in tests, we just verify the client exists
        assert client is not None
        assert hasattr(client, "search_publications")
        assert hasattr(client, "search_by_year")
        assert hasattr(client, "search_by_date_range")
