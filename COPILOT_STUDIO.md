# Microsoft Copilot Studio Configuration Guide

This guide shows you how to configure the DORA MCP Server for Microsoft Copilot Studio using the **new Streamable HTTP transport** (mcp-streamable-1.0).

## Overview

The DORA MCP Server now supports Microsoft Copilot Studio's **Model Context Protocol (MCP) Streamable transport**, which is the recommended way to integrate MCP servers with Copilot Studio. 

> **Important**: Microsoft deprecated SSE transport for MCP after August 2025. This server now uses the **Streamable HTTP transport** (`mcp-streamable-1.0`) which is the current standard.

## Available Endpoints

### For Microsoft Copilot Studio (MCP Protocol)
- **`POST /mcp`** - MCP Streamable endpoint (mcp-streamable-1.0) ✅ **Use this for Copilot Studio**
  - Protocol: JSON-RPC 2.0 over HTTP
  - Supports: `initialize`, `tools/list`, `tools/call`
  - Example: `{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}`

### Alternative REST API Endpoint
- **`POST /api/search`** - Simple REST API for direct searches
  - Request: `{"search_string": "your search term"}`
  - Response: `{"search_string": "...", "results": [...], "total": 123}`

### Supporting Endpoints
- **`GET /openapi.json`** - OpenAPI/Swagger specification
- **`GET /health`** - Health check endpoint
- **`GET /tools`** - List available MCP tools (simple format)
- **`/sse`** - SSE endpoint (deprecated for Copilot Studio)

## Configuration Steps

### 1. Deploy Your Server

First, deploy your server to Fly.io or any public URL:

```bash
flyctl deploy
```

Your server will be available at: `https://your-app-name.fly.dev`

### 2. Configure in Copilot Studio

#### Option A: Using MCP Onboarding Wizard (Recommended - Simplest)

1. **Open Copilot Studio**
   - Go to https://copilotstudio.microsoft.com/
   - Navigate to your Copilot agent

2. **Go to Tools Page**
   - Select **Add a tool**
   - Select **New tool**
   - Select **Model Context Protocol**

3. **Configure Basic Server Details**
   - **Server name**: `DORA Publications`
   - **Server description**: `Search scientific publications in the DORA repository by author, title, or keywords`
   - **Server URL**: `https://your-app-name.fly.dev/mcp` ✅
   - **Authentication type**: `None` (or configure API key if you add auth later)

4. **Create the Connection**
   - Click **Create**
   - Click **Add to agent** to enable it

5. **Test the Integration**
   - The tools from your MCP server will automatically appear
   - Test by asking: "search for publications by manfred heuberger"

#### Option B: Using OpenAPI Import (Advanced)

If the OpenAPI import doesn't work:

1. **Create Custom Connector**
   - Name: `DORA Publications`
   - Description: `Search scientific publications in DORA`
   - Host: `your-app-name.fly.dev`
   - Base URL: `/api`

2. **Add Action**
   - Name: `Search Publications`
   - Operation ID: `searchPublications`
   - HTTP Method: `POST`
   - URL Path: `/search`

3. **Configure Request**
   - Content-Type: `application/json`
   - Body schema:
     ```json
     {
       "type": "object",
       "properties": {
         "search_string": {
           "type": "string",
           "description": "Search term (author, title, or keyword)"
         }
       },
       "required": ["search_string"]
     }
     ```

4. **Configure Response**
   - Response schema:
     ```json
     {
       "type": "object",
       "properties": {
         "search_string": {"type": "string"},
         "results": {"type": "array"},
         "total": {"type": "integer"}
       }
     }
     ```

5. **Test and Save**

### 3. Use in Your Copilot

Once configured, you can use the connector in your Copilot's topics/flows:

**Example Topic:**
- **Trigger**: "search for publications by {author}"
- **Action**: Call `DORA Publications` connector
  - search_string: `{author}`
- **Response**: Format and display the results

**Example Flow:**
```yaml
User: "Find publications by manfred heuberger"
├─ Extract: author = "manfred heuberger"
├─ Call: DORA Publications.searchPublications(search_string: author)
├─ Parse: results.total, results.results
└─ Reply: "Found {total} publications by {author}"
```

## Testing the API

### Test with curl

```bash
# Test the search endpoint
curl -X POST https://your-app-name.fly.dev/api/search \
  -H "Content-Type: application/json" \
  -d '{"search_string": "manfred heuberger"}'

# Get OpenAPI spec
curl https://your-app-name.fly.dev/openapi.json

# Health check
curl https://your-app-name.fly.dev/health
```

### Test with Postman

1. Import the OpenAPI spec from: `https://your-app-name.fly.dev/openapi.json`
2. Create a POST request to `/api/search`
3. Set body:
   ```json
   {
     "search_string": "your search term"
   }
   ```
4. Send request

## Troubleshooting

### "Method Not Allowed" Error

**Cause**: The endpoint expects POST requests, but you're sending GET

**Solution**: 
- Ensure you're using `POST` method in Copilot Studio connector configuration
- URL should be: `https://your-app-name.fly.dev/api/search`
- Method: `POST` (not GET)

### "404 Not Found" Error

**Cause**: Wrong URL path

**Solution**:
- Verify the base URL: `https://your-app-name.fly.dev`
- Verify the endpoint path: `/api/search`
- Full URL: `https://your-app-name.fly.dev/api/search`

### "400 Bad Request" Error

**Cause**: Missing or invalid `search_string` parameter

**Solution**:
- Ensure request body contains: `{"search_string": "some value"}`
- Content-Type header must be: `application/json`

### CORS Errors

If you get CORS errors from a browser:

**Solution**: Add CORS middleware to the server (see below)

## Adding CORS Support (Optional)

If you need to call the API from a web browser, add CORS support:

```python
# In server.py, after imports:
from starlette.middleware.cors import CORSMiddleware

# Before starlette_app definition:
starlette_app = Starlette(...)

starlette_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Security Considerations

### Adding Authentication

To secure your API, you can add authentication:

1. **API Key Authentication**
   ```python
   async def search_api_endpoint(request):
       # Check API key
       api_key = request.headers.get("X-API-Key")
       if api_key != os.getenv("API_KEY"):
           return JSONResponse({"error": "Unauthorized"}, status_code=401)
       # ... rest of the code
   ```

2. **In Copilot Studio**
   - Authentication type: **API Key**
   - Key location: **Header**
   - Key name: `X-API-Key`
   - Key value: `your-secret-key`

### Rate Limiting

Consider adding rate limiting to prevent abuse:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("10/minute")
async def search_api_endpoint(request):
    # ... your code
```

## Advanced Configuration

### Custom Response Formatting

You can customize the response format in the `search_api_endpoint` function to match your Copilot's needs:

```python
async def search_api_endpoint(request):
    # ... search logic ...
    
    # Format results for better Copilot integration
    formatted_results = []
    for pub in results:
        formatted_results.append({
            "title": pub.get("title", "N/A"),
            "authors": pub.get("authors", []),
            "year": pub.get("year", "N/A"),
            "url": pub.get("object_url", "")
        })
    
    return JSONResponse({
        "search_string": search_string,
        "results": formatted_results,
        "total": len(formatted_results),
        "status": "success"
    })
```

### Webhook Support

If you want Copilot to call your server asynchronously:

```python
async def webhook_endpoint(request):
    """Webhook endpoint for async processing."""
    body = await request.json()
    callback_url = body.get("callback_url")
    search_string = body.get("search_string")
    
    # Process search asynchronously
    # Then POST results to callback_url
    
    return JSONResponse({"status": "processing"})
```

## Example Copilot Configurations

### Simple Search Bot

**Topic: Search Publications**
- Trigger: "search for {query}"
- Action: DORA Publications.searchPublications
  - Input: search_string = {query}
- Response: "Found {total} publications. Here are the results: {results}"

### Expert Advisor Bot

**Topic: Find Author's Work**
- Trigger: "what has {author} published"
- Action: DORA Publications.searchPublications
  - Input: search_string = {author}
- Condition: 
  - If total > 0: "I found {total} publications by {author}. Their recent work includes..."
  - If total = 0: "I couldn't find any publications by {author} in DORA."

### Research Assistant

**Topic: Research Query**
- Trigger: "find research on {topic}"
- Action: DORA Publications.searchPublications
  - Input: search_string = {topic}
- Parse: Extract top 5 results
- Format: Create formatted list with titles, authors, years
- Response: Present findings with links

## Support

- Server Issues: Check logs with `flyctl logs`
- API Issues: Test with `/health` endpoint
- Copilot Studio: Check connector test results
- Documentation: See `/openapi.json` for full API spec

## Next Steps

1. ✅ Deploy your server to Fly.io
2. ✅ Test the `/api/search` endpoint with curl
3. ✅ Import OpenAPI spec into Copilot Studio
4. ✅ Configure connector authentication (if needed)
5. ✅ Test the connector in Copilot Studio
6. ✅ Create topics/flows using the connector
7. ✅ Deploy your Copilot agent

Your DORA MCP Server is now ready to power AI agents in Microsoft Copilot Studio! 🚀
