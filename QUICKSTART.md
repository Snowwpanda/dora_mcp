# Quick Start Guide

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Snowwpanda/dora_mcp.git
   cd dora_mcp
   ```

2. **Install the package:**
   ```bash
   pip install -e .
   ```

## Running the Server

### Standalone Mode

Run the server directly:
```bash
python -m dora_mcp.server
```

Or use the installed command:
```bash
dora-mcp
```

### With MCP Clients

#### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "dora": {
      "command": "python",
      "args": ["-m", "dora_mcp.server"]
    }
  }
}
```

#### Cline (VS Code Extension)

Add to your Cline MCP settings:

```json
{
  "mcpServers": {
    "dora": {
      "command": "python",
      "args": ["-m", "dora_mcp.server"]
    }
  }
}
```

## Using the Tools

Once connected, you can use three tools:

### 1. search_by_year

Search publications from a specific year:
```
Use the search_by_year tool with year: 2018
```

### 2. search_by_date_range

Search publications within a date range:
```
Use the search_by_date_range tool with:
- start_date: "2018-01-01"
- end_date: "2018-12-31"
```

### 3. search_publications

Advanced search with custom queries and filters:
```
Use the search_publications tool with:
- query: "*:*"
- filters: ["your_custom_filter_here"]
```

## Example Usage

Ask your MCP client:
- "Search for publications from 2018 in DORA"
- "Find publications between January 2020 and June 2020"
- "Get all publications from DORA"

## Troubleshooting

### Connection Issues

If you encounter connection issues:
1. Ensure Python 3.10+ is installed
2. Verify all dependencies are installed: `pip install mcp httpx`
3. Check that the server is running: `python -m dora_mcp.server`

### Network Issues

If DORA API is not accessible:
- Check your internet connection
- Verify the DORA URL is accessible: https://www.dora.lib4ri.ch/
- Check firewall settings

## More Information

See [README.md](README.md) for detailed documentation.
