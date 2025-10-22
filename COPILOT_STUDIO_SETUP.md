# Copilot Studio MCP Server Setup Guide

This guide explains how to connect your DORA MCP Server to Microsoft Copilot Studio.

## Quick Start

### Step 1: Deploy Your Server

Deploy your MCP server to a publicly accessible URL (e.g., Fly.io):

```bash
fly deploy
```

Your server will be available at: `https://your-app-name.fly.dev`

### Step 2: Verify the MCP Endpoint

Test the `/mcp` endpoint to ensure it's working:

```bash
curl -X POST https://your-app-name.fly.dev/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
  }'
```

Expected response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "dora-mcp",
      "version": "1.0.0"
    }
  }
}
```

### Step 3: Add to Copilot Studio

#### Option 1: Using the MCP Onboarding Wizard (Recommended)

1. Go to your Copilot Studio agent
2. Navigate to the **Tools** page
3. Click **Add a tool**
4. Select **New tool**
5. Select **Model Context Protocol**
6. Fill in the details:
   - **Server name**: `DORA Publications`
   - **Server description**: `Search the DORA repository for scientific publications by author, title, or keywords`
   - **Server URL**: `https://your-app-name.fly.dev/mcp`
   - **Authentication**: Select `None` (or configure API key if you add authentication)
7. Click **Create**
8. Create a new connection or use an existing one
9. Click **Add to agent**

#### Option 2: Using Custom Connector in Power Apps

1. Go to your Copilot Studio agent
2. Navigate to the **Tools** page
3. Click **Add a tool**
4. Select **New tool**
5. Select **Custom connector**
6. You'll be taken to Power Apps
7. Select **New custom connector**
8. Select **Import OpenAPI file**
9. Upload the `openapi-minimal.yaml` file from this repository
10. Click **Import**
11. Click **Continue** to complete the setup

## Available Files

This repository includes three OpenAPI specification files:

1. **`openapi-minimal.yaml`** - Minimal spec for Copilot Studio MCP (RECOMMENDED for Copilot Studio)
   - Only includes the `/mcp` endpoint
   - Follows Microsoft's example exactly
   - Use this for the MCP onboarding wizard or custom connector

2. **`openapi-copilot.json`** - Full spec for Copilot Studio (served at `/openapi-copilot.json`)
   - Includes detailed schemas
   - Dynamically served with correct host/scheme

3. **`openapi-connector.json`** - Spec for Power Automate (served at `/openapi-connector.json`)
   - REST API endpoint for Power Automate custom connectors
   - Use `/connector` endpoint instead of `/mcp`

## Important Notes

### Transport Type

- **Copilot Studio requires Streamable transport** (`mcp-streamable-1.0`)
- SSE transport is deprecated after August 2025
- Your server correctly implements Streamable transport at `/mcp`

### OpenAPI Specification Requirements

The OpenAPI spec MUST include:
- `x-ms-agentic-protocol: mcp-streamable-1.0` on the `/mcp` endpoint
- This tells Copilot Studio to use MCP protocol instead of treating it as a regular REST API

### Endpoint Format

Your MCP endpoint must:
- Accept JSON-RPC 2.0 requests
- Support these methods:
  - `initialize` - Initialize the MCP session
  - `tools/list` - List available tools
  - `tools/call` - Call a specific tool
- Return JSON-RPC 2.0 responses

### Testing the Connection

After adding the MCP server to your agent, test it by asking:
- "Search DORA for publications by Manfred Heuberger"
- "Find research papers about climate change in DORA"
- "Show me publications by [author name]"

## Common Issues and Solutions

### Issue: Copilot Studio doesn't recognize it as an MCP server

**Solution**: Ensure the OpenAPI spec includes `x-ms-agentic-protocol: mcp-streamable-1.0`

### Issue: Connection fails

**Solution**: 
1. Verify the server URL is publicly accessible
2. Test the `/mcp` endpoint with curl
3. Check server logs for errors

### Issue: Tools not showing up

**Solution**:
1. Test the `tools/list` method:
   ```bash
   curl -X POST https://your-app-name.fly.dev/mcp \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc": "2.0",
       "id": 1,
       "method": "tools/list",
       "params": {}
     }'
   ```
2. Verify the response includes the `search_publications` tool

### Issue: Tool execution fails

**Solution**:
1. Test the `tools/call` method:
   ```bash
   curl -X POST https://your-app-name.fly.dev/mcp \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc": "2.0",
       "id": 1,
       "method": "tools/call",
       "params": {
         "name": "search_publications",
         "arguments": {
           "search_string": "manfred heuberger"
         }
       }
     }'
   ```
2. Check the response for errors

## Architecture

```
Copilot Studio Agent
    ↓
    └─→ /mcp endpoint (JSON-RPC 2.0 over HTTP)
          ├─→ initialize
          ├─→ tools/list
          └─→ tools/call
                └─→ search_publications tool
                      └─→ DORA API
```

## Server Endpoints Summary

- `/mcp` - MCP Streamable endpoint (for Copilot Studio)
- `/connector` - REST API endpoint (for Power Automate)
- `/health` - Health check
- `/` - API documentation
- `/openapi-minimal.yaml` - Minimal OpenAPI spec (static file)
- `/openapi-copilot.json` - Dynamic OpenAPI spec for Copilot Studio
- `/openapi-connector.json` - Dynamic OpenAPI spec for Power Automate

## References

- [Microsoft Documentation: Add MCP Server to Agent](https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent)
- [MCP Specification](https://modelcontextprotocol.io/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
