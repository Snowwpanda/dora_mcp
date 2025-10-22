# Usage Guide

## Quick Start

### Local Installation

1. Install the package:
```bash
pip install -e .
```

2. Run the server:
```bash
python -m dora_mcp.server
```

### Docker Installation

1. Build the Docker image:
```bash
docker build -t dora-mcp .
```

2. Run the container:
```bash
docker run -i dora-mcp
```

Or use docker-compose:
```bash
docker-compose up
```

## Using the MCP Server

The DORA MCP server implements the Model Context Protocol (MCP) and can be used with any MCP-compatible client.

### Available Tools

#### `search_publications`

Search the DORA database for scientific publications.

**Parameters:**
- `search_string` (required): The search term to query

**Example request:**
```json
{
  "name": "search_publications",
  "arguments": {
    "search_string": "manfred heuberger"
  }
}
```

**Example response:**
The tool returns JSON data containing publication information from the DORA database, including:
- Publication titles
- Authors
- Abstracts
- Publication dates
- And other metadata

### Integration Examples

#### Using with Claude Desktop

Add to your Claude Desktop configuration file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "dora": {
      "command": "python",
      "args": ["-m", "dora_mcp.server"],
      "cwd": "/path/to/dora_mcp"
    }
  }
}
```

#### Using with Docker in Claude Desktop

```json
{
  "mcpServers": {
    "dora": {
      "command": "docker",
      "args": ["run", "-i", "dora-mcp"]
    }
  }
}
```

## API Details

### DORA Search API

The server queries the DORA (Digital Object Repository for Academia) API at:
```
https://www.dora.lib4ri.ch/empa
```

The search endpoint uses weighted field searches:
- **Title** (weight: 5) - Highest priority
- **Abstract** (weight: 2) - High priority
- **Creator** (weight: 2) - High priority
- **Original Author List** (weight: 2) - High priority
- **Contributor** (weight: 1) - Standard priority
- **Type** (weight: 1) - Standard priority
- **Catch-all MODS fields** (weight: 1) - Standard priority

### Search Query Format

The server constructs queries in the following format:
```
mods_titleInfo_title_mt:(search term)^5 OR
mods_abstract_ms:(search term)^2 OR
dc.creator:(search term)^2 OR
mods_extension_originalAuthorList_mt:(search term)^2 OR
dc.contributor:(search term)^1 OR
dc.type:(search term)^1 OR
catch_all_MODS_mt:(search term)^1
```

## Troubleshooting

### Server won't start

**Problem:** Import errors or missing dependencies

**Solution:** Ensure all dependencies are installed:
```bash
pip install -e .
```

### No results from search

**Problem:** Empty or no results returned

**Possible causes:**
- The search term doesn't match any publications
- Network connectivity issues
- The DORA API is unavailable

**Solution:**
- Try a different search term
- Check network connectivity
- Verify the DORA website is accessible: https://www.dora.lib4ri.ch/empa

### Docker build fails

**Problem:** SSL certificate errors during Docker build

**Solution:** The Dockerfile includes ca-certificates installation. If issues persist, try:
1. Update Docker to the latest version
2. Check your network/proxy settings
3. Build with `--network=host` flag:
   ```bash
   docker build --network=host -t dora-mcp .
   ```

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest tests/
```

### Manual Testing

Test the search query builder:
```python
from dora_mcp.server import build_search_query

query = build_search_query("test search")
print(query)
```

Test the API call:
```python
import asyncio
from dora_mcp.server import search_dora_publications

async def test():
    result = await search_dora_publications("manfred heuberger")
    print(result)

asyncio.run(test())
```

## Contributing

When contributing, please:
1. Write tests for new features
2. Update documentation
3. Follow the existing code style
4. Ensure all tests pass before submitting a PR
