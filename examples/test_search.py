#!/usr/bin/env python3
"""Example script to test DORA search functionality."""

import asyncio
import sys
from dora_mcp.server import search_dora_publications, build_search_query, call_tool


async def test_search(search_term: str):
    """Test a search query."""
    print(f"\n{'='*70}")
    print(f"Testing search: '{search_term}'")
    print(f"{'='*70}\n")
    
    try:
        # Show the constructed query
        query = build_search_query(search_term)
        print(f"1. Query constructed: {query[:100]}...")
        
        # Test direct API call
        print(f"\n2. Testing direct API call...")
        result = await search_dora_publications(search_term)
        
        if isinstance(result, dict):
            print(f"   ✓ Got dict response with {len(result)} keys")
            print(f"   Keys: {list(result.keys())}")
            
            # Try to extract some useful information
            if 'response' in result:
                response = result['response']
                if 'docs' in response:
                    docs = response['docs']
                    print(f"   ✓ Found {len(docs)} documents")
                    
                    # Show first few results
                    for i, doc in enumerate(docs[:2], 1):
                        print(f"\n   --- Publication {i} ---")
                        if 'title' in doc:
                            print(f"   Title: {doc.get('title', 'N/A')}")
                        if 'dc.creator' in doc:
                            print(f"   Author: {doc.get('dc.creator', 'N/A')}")
                        if 'dc.date' in doc:
                            print(f"   Date: {doc.get('dc.date', 'N/A')}")
        else:
            print(f"   ✓ Got response of type: {type(result)}")
            print(f"   Preview: {str(result)[:200]}...")
        
        # Test MCP tool call
        print(f"\n3. Testing MCP tool call...")
        mcp_result = await call_tool(
            "search_publications",
            {"search_string": search_term}
        )
        
        print(f"   ✓ Got {len(mcp_result)} TextContent objects")
        if mcp_result:
            text = mcp_result[0].text
            print(f"   ✓ Response has {len(text)} characters")
            
            # Show a preview
            preview = text[:300]
            if len(text) > 300:
                preview += "..."
            print(f"\n   Preview:\n   {'-'*60}")
            for line in preview.split('\n')[:10]:
                print(f"   {line}")
            print(f"   {'-'*60}")
        
        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run test searches."""
    # Get search term from command line or use defaults
    if len(sys.argv) > 1:
        test_cases = [" ".join(sys.argv[1:])]
    else:
        test_cases = [
            "manfred heuberger",  # Known author - should return results
            "polymer tribology",  # Topic search
        ]
    
    print("\n" + "="*70)
    print("DORA MCP Server Test Suite")
    print("="*70)
    
    results = []
    for search_term in test_cases:
        success = await test_search(search_term)
        results.append((search_term, success))
        if len(test_cases) > 1:
            await asyncio.sleep(1)  # Be nice to the API
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    
    for search_term, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: '{search_term}'")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
