# Examples

This directory contains example scripts demonstrating how to use the DORA MCP server.

## test_search.py

A simple script to test the DORA search functionality.

### Usage

```bash
# Use default search term
python examples/test_search.py

# Search for a specific term
python examples/test_search.py "your search term"

# Example with an author name
python examples/test_search.py "manfred heuberger"
```

### What it does

1. Constructs a search query using the DORA query builder
2. Makes an API call to the DORA endpoint
3. Displays the results in a readable format
4. Shows publication titles, creators, and dates when available

### Expected Output

When successful, you'll see:
- The search term being used
- A preview of the constructed query
- The number of results found
- Details of the first few publications

### Requirements

- The package must be installed: `pip install -e .`
- Internet connectivity to access the DORA API
- Python 3.10 or higher

## Creating Your Own Examples

To create your own example:

```python
import asyncio
from dora_mcp.server import search_dora_publications

async def my_example():
    result = await search_dora_publications("your search term")
    # Process result...
    print(result)

asyncio.run(my_example())
```

You can also import the MCP server components to build custom integrations:

```python
from dora_mcp.server import app, list_tools, call_tool

# Use the MCP server in your own application
```
