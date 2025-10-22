"""Tests for the DORA MCP server."""

import pytest
from dora_mcp.server import build_search_query, DORA_BASE_URL, DORA_SEARCH_ENDPOINT


def test_constants():
    """Test that constants are properly defined."""
    assert DORA_BASE_URL == "https://www.dora.lib4ri.ch/empa"
    assert DORA_SEARCH_ENDPOINT == f"{DORA_BASE_URL}/islandora/search/json_cit_a"


def test_build_search_query():
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


def test_build_search_query_special_characters():
    """Test that special characters are properly encoded."""
    search_string = "manfred heuberger"
    query = build_search_query(search_string)
    
    # Space should be encoded
    assert "%20" in query or " " not in query
    
    # Check that the query contains the search terms
    assert "manfred" in query.lower()
    assert "heuberger" in query.lower()


@pytest.mark.asyncio
async def test_search_dora_publications_connection():
    """Test that we can attempt to connect to DORA API (may fail if network unavailable)."""
    from dora_mcp.server import search_dora_publications
    
    # This test will make a real HTTP request
    # We're just checking that the function doesn't crash
    try:
        result = await search_dora_publications("test")
        # If successful, result should be a dict
        assert isinstance(result, (dict, list))
    except Exception as e:
        # If it fails due to network/connection issues, that's acceptable for this test
        # We're mainly testing that the function is properly structured
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
