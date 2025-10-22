#!/usr/bin/env python3
"""Example script to test DORA search functionality."""

import asyncio
import sys
from dora_mcp.server import search_dora_publications, build_search_query


async def main():
    """Run a test search against the DORA API."""
    # Get search term from command line or use default
    search_term = sys.argv[1] if len(sys.argv) > 1 else "manfred heuberger"
    
    print(f"Searching DORA for: {search_term}")
    print("-" * 60)
    
    # Show the constructed query
    query = build_search_query(search_term)
    print(f"Query constructed: {query[:100]}...")
    print("-" * 60)
    
    try:
        # Perform the search
        result = await search_dora_publications(search_term)
        
        print(f"\nSuccess! Result type: {type(result)}")
        
        if isinstance(result, dict):
            print(f"Number of keys in result: {len(result)}")
            print(f"Available keys: {list(result.keys())}")
            
            # Try to extract some useful information
            if 'response' in result:
                print(f"\nResponse data available")
            if 'docs' in result.get('response', {}):
                docs = result['response']['docs']
                print(f"Number of documents found: {len(docs)}")
                
                # Show first few results
                for i, doc in enumerate(docs[:3], 1):
                    print(f"\n--- Publication {i} ---")
                    if 'title' in doc:
                        print(f"Title: {doc['title']}")
                    if 'dc.creator' in doc:
                        print(f"Creator: {doc['dc.creator']}")
                    if 'dc.date' in doc:
                        print(f"Date: {doc['dc.date']}")
        else:
            print(f"\nResult preview (first 500 chars):")
            print(str(result)[:500])
            
    except Exception as e:
        print(f"\nError occurred: {type(e).__name__}: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
