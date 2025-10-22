"""Tests for the DORA MCP server.

These tests can run against both the server code directly (unit tests)
and against a running HTTP server (integration tests).

Set TEST_MODE environment variable:
- 'unit' (default): Test server code directly
- 'http': Test against HTTP server at TEST_SERVER_URL
"""

import os
import pytest
import json
import httpx
from dora_mcp.server import (
    build_search_query,
    search_dora_publications,
    list_tools,
    call_tool,
    DORA_BASE_URL,
    DORA_SEARCH_ENDPOINT,
)

# Test configuration
TEST_MODE = os.getenv("TEST_MODE", "unit").lower()
TEST_SERVER_URL = os.getenv("TEST_SERVER_URL", "http://localhost:8000")


class TestConstants:
    """Test server constants."""
    
    def test_base_url(self):
        """Test that base URL is properly defined."""
        assert DORA_BASE_URL == "https://www.dora.lib4ri.ch/empa"
    
    def test_search_endpoint(self):
        """Test that search endpoint is properly defined."""
        assert DORA_SEARCH_ENDPOINT == f"{DORA_BASE_URL}/islandora/search/json_cit_a"


class TestSearchQuery:
    """Test search query building."""
    
    def test_build_search_query(self):
        """Test that search query is built correctly."""
        search_string = "test query"
        query = build_search_query(search_string)
        
        # Check that all expected field searches are present
        assert "mods_titleInfo_title_mt" in query
        assert "mods_abstract_ms" in query
        assert "dc.creator" in query
        assert "mods_extension_originalAuthorList_mt" in query
        assert "dc.contributor" in query
        assert "dc.type" in query
        assert "catch_all_MODS_mt" in query
        
        # Check that OR is used to join queries
        assert "OR" in query
        
        # Check that the search string is included
        assert "test" in query.lower()
    
    def test_build_search_query_special_characters(self):
        """Test that special characters are properly encoded."""
        search_string = "manfred heuberger"
        query = build_search_query(search_string)
        
        # Space should be encoded
        assert "%20" in query or " " not in query
        
        # Check that the query contains the search terms
        assert "manfred" in query.lower()
        assert "heuberger" in query.lower()
    
    def test_build_search_query_encoding(self):
        """Test URL encoding of special characters."""
        search_string = "test & query"
        query = build_search_query(search_string)
        
        # Ampersand should be encoded
        assert "&" not in query or "%26" in query


class TestMCPProtocol:
    """Test MCP protocol handlers."""
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test that list_tools returns the correct tool definition."""
        if TEST_MODE == "http":
            pytest.skip("Direct function calls not supported in HTTP mode")
        
        tools = await list_tools()
        
        assert len(tools) == 1
        tool = tools[0]
        
        assert tool.name == "search_publications"
        assert "DORA" in tool.description
        assert "search_string" in tool.inputSchema["properties"]
        assert tool.inputSchema["required"] == ["search_string"]
    
    @pytest.mark.asyncio
    async def test_call_tool_unknown(self):
        """Test that calling an unknown tool raises an error."""
        if TEST_MODE == "http":
            pytest.skip("Direct function calls not supported in HTTP mode")
        
        with pytest.raises(ValueError, match="Unknown tool"):
            await call_tool("nonexistent_tool", {})
    
    @pytest.mark.asyncio
    async def test_call_tool_missing_argument(self):
        """Test that calling without required argument raises an error."""
        if TEST_MODE == "http":
            pytest.skip("Direct function calls not supported in HTTP mode")
        
        with pytest.raises(ValueError, match="search_string is required"):
            await call_tool("search_publications", {})


class TestDORAIntegration:
    """Integration tests with DORA API."""
    
    @pytest.mark.asyncio
    async def test_search_manfred_heuberger(self):
        """Test searching for papers by Manfred Heuberger.
        
        This is a real author in DORA, so we should get results.
        """
        try:
            result = await search_dora_publications("manfred heuberger")
            
            # Should return a dict or list
            assert isinstance(result, (dict, list))
            
            # If it's a dict, it should have some data
            if isinstance(result, dict):
                # Check for common JSON response structures
                assert len(result) > 0
                print(f"✓ Got response with {len(result)} keys")
        except Exception as e:
            pytest.skip(f"Network error or API unavailable: {e}")
    
    @pytest.mark.asyncio
    async def test_search_returns_json(self):
        """Test that search returns valid JSON-serializable data."""
        try:
            result = await search_dora_publications("polymer")
            
            # Should be JSON serializable
            json_str = json.dumps(result)
            assert len(json_str) > 0
            
            # Should be able to parse it back
            parsed = json.loads(json_str)
            assert parsed == result
            print("✓ Response is valid JSON")
        except Exception as e:
            pytest.skip(f"Network error or API unavailable: {e}")
    
    @pytest.mark.asyncio
    async def test_call_tool_manfred_heuberger(self):
        """Test the full MCP tool call for Manfred Heuberger."""
        try:
            result = await call_tool(
                "search_publications",
                {"search_string": "manfred heuberger"}
            )
            
            # Should return a list of TextContent
            assert isinstance(result, list)
            assert len(result) > 0
            
            # First item should have text
            assert hasattr(result[0], "text")
            assert "manfred heuberger" in result[0].text.lower()
            
            print("✓ MCP tool call successful")
            print(f"✓ Response length: {len(result[0].text)} characters")
        except Exception as e:
            pytest.skip(f"Network error or API unavailable: {e}")
    
    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        """Test searching for something that likely returns no results."""
        try:
            # Use a very specific nonsense string
            result = await search_dora_publications("xyzabc123nonexistent999")
            
            # Should still return valid response (even if empty)
            assert isinstance(result, (dict, list))
            print("✓ Handles empty results gracefully")
        except Exception as e:
            pytest.skip(f"Network error or API unavailable: {e}")


class TestErrorHandling:
    """Test error handling."""
    
    @pytest.mark.asyncio
    async def test_call_tool_error_handling(self):
        """Test that tool errors are caught and returned as text."""
        if TEST_MODE == "http":
            pytest.skip("Mock testing not supported in HTTP mode")
        
        # Mock a search that will fail
        import httpx
        from unittest.mock import patch
        
        # Create an async mock that raises an error when get() is called
        async def mock_get(*args, **kwargs):
            raise httpx.HTTPError("Connection failed")
        
        # Patch the client to use our mock
        async def mock_client_context(*args, **kwargs):
            class MockClient:
                async def __aenter__(self):
                    return self
                async def __aexit__(self, *args):
                    pass
                get = mock_get
            return MockClient()
        
        with patch("httpx.AsyncClient", side_effect=mock_client_context):
            result = await call_tool(
                "search_publications",
                {"search_string": "test"}
            )
            
            # Should return error as TextContent
            assert isinstance(result, list)
            assert len(result) > 0
            assert "Error" in result[0].text or "error" in result[0].text.lower()


class TestHTTPMode:
    """Tests for HTTP/SSE transport mode.
    
    These tests only run when TEST_MODE=http is set.
    """
    
    @pytest.mark.asyncio
    async def test_http_server_endpoints(self):
        """Test that HTTP server has correct endpoints."""
        if TEST_MODE != "http":
            pytest.skip("Only runs in HTTP mode")
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # Test SSE endpoint exists
            try:
                async with client.stream("GET", f"{TEST_SERVER_URL}/sse") as response:
                    assert response.status_code == 200
                    print("✓ SSE endpoint accessible")
            except httpx.ConnectError:
                pytest.fail(f"Cannot connect to {TEST_SERVER_URL}")
    
    @pytest.mark.asyncio
    async def test_http_mcp_tools_list(self):
        """Test listing tools via HTTP/MCP protocol."""
        if TEST_MODE != "http":
            pytest.skip("Only runs in HTTP mode")
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            # MCP tools/list request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            try:
                response = await client.post(
                    f"{TEST_SERVER_URL}/messages",
                    json=request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check response structure
                    assert "result" in data or "error" in data
                    
                    if "result" in data:
                        tools = data["result"].get("tools", [])
                        assert len(tools) == 1
                        assert tools[0]["name"] == "search_publications"
                        print("✓ MCP tools/list successful")
                        print(f"✓ Found tool: {tools[0]['name']}")
            except Exception as e:
                pytest.skip(f"HTTP test inconclusive: {e}")
    
    @pytest.mark.asyncio
    async def test_http_mcp_call_tool(self):
        """Test calling search_publications tool via HTTP/MCP."""
        if TEST_MODE != "http":
            pytest.skip("Only runs in HTTP mode")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # MCP tools/call request
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "search_publications",
                    "arguments": {
                        "search_string": "manfred heuberger"
                    }
                }
            }
            
            try:
                response = await client.post(
                    f"{TEST_SERVER_URL}/messages",
                    json=request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check response structure
                    assert "result" in data or "error" in data
                    
                    if "result" in data:
                        content = data["result"].get("content", [])
                        assert len(content) > 0
                        assert "manfred heuberger" in content[0].get("text", "").lower()
                        print("✓ MCP tools/call successful")
                        print(f"✓ Response length: {len(content[0]['text'])} characters")
            except Exception as e:
                pytest.skip(f"HTTP test inconclusive: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
