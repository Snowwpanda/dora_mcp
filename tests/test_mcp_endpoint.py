#!/usr/bin/env python3
"""Test script for MCP endpoint compatibility with Copilot Studio."""

import json
import sys
import httpx
import asyncio


async def test_mcp_endpoint(base_url: str = "http://localhost:8000"):
    """Test the MCP endpoint with all required methods."""
    
    print(f"Testing MCP endpoint at {base_url}/mcp\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Initialize
        print("=" * 60)
        print("Test 1: Initialize")
        print("=" * 60)
        
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        print(f"Request: {json.dumps(init_request, indent=2)}")
        
        try:
            response = await client.post(
                f"{base_url}/mcp",
                json=init_request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Verify response structure
            assert result.get("jsonrpc") == "2.0", "Invalid JSON-RPC version"
            assert result.get("id") == 1, "Invalid response ID"
            assert "result" in result, "Missing result field"
            assert result["result"].get("protocolVersion"), "Missing protocolVersion"
            assert result["result"].get("serverInfo"), "Missing serverInfo"
            print("✓ Initialize test PASSED\n")
            
        except Exception as e:
            print(f"✗ Initialize test FAILED: {e}\n")
            return False
        
        # Test 2: List Tools
        print("=" * 60)
        print("Test 2: List Tools")
        print("=" * 60)
        
        list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        print(f"Request: {json.dumps(list_request, indent=2)}")
        
        try:
            response = await client.post(
                f"{base_url}/mcp",
                json=list_request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Verify response structure
            assert result.get("jsonrpc") == "2.0", "Invalid JSON-RPC version"
            assert result.get("id") == 2, "Invalid response ID"
            assert "result" in result, "Missing result field"
            assert "tools" in result["result"], "Missing tools array"
            assert len(result["result"]["tools"]) > 0, "No tools found"
            
            # Verify tool structure
            tool = result["result"]["tools"][0]
            assert "name" in tool, "Tool missing name"
            assert "description" in tool, "Tool missing description"
            assert "inputSchema" in tool, "Tool missing inputSchema"
            
            print(f"✓ List Tools test PASSED - Found {len(result['result']['tools'])} tool(s)\n")
            
        except Exception as e:
            print(f"✗ List Tools test FAILED: {e}\n")
            return False
        
        # Test 3: Call Tool
        print("=" * 60)
        print("Test 3: Call Tool")
        print("=" * 60)
        
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_publications",
                "arguments": {
                    "search_string": "test"
                }
            }
        }
        
        print(f"Request: {json.dumps(call_request, indent=2)}")
        
        try:
            response = await client.post(
                f"{base_url}/mcp",
                json=call_request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            print(f"Response (truncated): {json.dumps(result, indent=2)[:500]}...")
            
            # Verify response structure
            assert result.get("jsonrpc") == "2.0", "Invalid JSON-RPC version"
            assert result.get("id") == 3, "Invalid response ID"
            assert "result" in result, "Missing result field"
            assert "content" in result["result"], "Missing content array"
            
            print("✓ Call Tool test PASSED\n")
            
        except Exception as e:
            print(f"✗ Call Tool test FAILED: {e}\n")
            return False
        
        # Test 4: Check OpenAPI specs
        print("=" * 60)
        print("Test 4: Check OpenAPI Specifications")
        print("=" * 60)
        
        specs = [
            "/openapi-minimal.json",
            "/openapi-copilot.json",
            "/openapi-connector.json"
        ]
        
        for spec_path in specs:
            try:
                response = await client.get(f"{base_url}{spec_path}")
                response.raise_for_status()
                spec = response.json()
                
                print(f"\n{spec_path}:")
                print(f"  Title: {spec.get('info', {}).get('title')}")
                print(f"  Version: {spec.get('info', {}).get('version')}")
                
                if "/mcp" in spec.get("paths", {}):
                    mcp_endpoint = spec["paths"]["/mcp"]["post"]
                    protocol = mcp_endpoint.get("x-ms-agentic-protocol")
                    print(f"  MCP Protocol: {protocol}")
                    
                    if protocol != "mcp-streamable-1.0":
                        print(f"  ⚠ WARNING: Protocol should be 'mcp-streamable-1.0'")
                
                print(f"  ✓ {spec_path} is valid")
                
            except Exception as e:
                print(f"  ✗ {spec_path} FAILED: {e}")
                return False
        
        print("\n" + "=" * 60)
        print("All tests PASSED! ✓")
        print("=" * 60)
        print("\nYour MCP server is ready for Copilot Studio!")
        print(f"\nNext steps:")
        print(f"1. Deploy your server to a public URL")
        print(f"2. Use {base_url}/openapi-minimal.json for the OpenAPI spec")
        print(f"3. Set the MCP endpoint URL to {base_url}/mcp")
        print(f"4. Add to Copilot Studio using the MCP onboarding wizard")
        
        return True


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    success = asyncio.run(test_mcp_endpoint(base_url))
    sys.exit(0 if success else 1)
