# DORA MCP Server

A Model Context Protocol (MCP) server for connecting to the DORA (Digital Object Repository and Archive) publication repository at lib4ri.ch.

## Overview

This MCP server provides tools to search and retrieve publication citations from the DORA repository in JSON format. It supports searching by year, date range, and custom queries with filters.

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Install from source

```bash
# Clone the repository
git clone https://github.com/Snowwpanda/dora_mcp.git
cd dora_mcp

# Install the package
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## Usage

### As a standalone MCP server

Run the server directly:

```bash
python -m dora_mcp.server
```

Or use the installed command:

```bash
dora-mcp
```

### Configuration for MCP clients

Add the following to your MCP client configuration (e.g., Claude Desktop, Cline):

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

Or if installed globally:

```json
{
  "mcpServers": {
    "dora": {
      "command": "dora-mcp"
    }
  }
}
```

## Available Tools

### 1. search_publications

Search for publications in the DORA repository with custom queries and filters.

**Parameters:**
- `query` (string, optional): Search query. Default is `"*:*"` for all publications.
- `filters` (array of strings, optional): List of filter strings to apply.

**Example:**
```json
{
  "query": "*:*",
  "filters": ["mods_originInfo_encoding_w3cdtf_keyDate_yes_dateIssued_dt:[2020-01-01T00:00:00Z TO 2020-12-31T23:59:59Z]"]
}
```

### 2. search_by_year

Search for publications by a specific year.

**Parameters:**
- `year` (integer, required): Year to search for (e.g., 2018).

**Example:**
```json
{
  "year": 2018
}
```

### 3. search_by_date_range

Search for publications within a date range.

**Parameters:**
- `start_date` (string, required): Start date in ISO format (e.g., "2018-01-01").
- `end_date` (string, required): End date in ISO format (e.g., "2018-12-31").

**Example:**
```json
{
  "start_date": "2018-01-01",
  "end_date": "2018-12-31"
}
```

## DORA API Format

The DORA repository uses the following URL format for JSON citations:

```
https://www.dora.lib4ri.ch/empa/islandora/search/json_cit_a/<query>?f[0]=<filter>
```

**Example URL:**
```
https://www.dora.lib4ri.ch/empa/islandora/search/json_cit_a/%2A%3A%2A?f%5B0%5D=mods_originInfo_encoding_w3cdtf_keyDate_yes_dateIssued_dt%3A%5B2018-01-01T00%3A00%3A00Z%20TO%202018-12-31T23%3A59%3A59Z%5D
```

This translates to:
- Query: `*:*` (all publications)
- Filter: Publications issued in 2018

## Development

### Running tests

```bash
pytest
```

### Project structure

```
dora_mcp/
├── dora_mcp/
│   ├── __init__.py
│   └── server.py        # Main MCP server implementation
├── tests/
│   └── test_server.py   # Test suite
├── pyproject.toml       # Project configuration
└── README.md           # This file
```

## License

See the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
