# dora_mcp

MCP (Model Context Protocol) server for accessing DORA (Digital Object Repository for Academia) publications from the lib4ri Empa repository.

## Overview

This MCP server provides access to scientific publications in the DORA database at https://www.dora.lib4ri.ch/empa. It allows you to search for publications by author name, title, abstract, and other metadata fields.

## Features

- Search DORA publications database
- Query across multiple fields (title, abstract, authors, contributors)
- Returns JSON-formatted publication data
- Runnable in Docker container

## Installation

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager (recommended, somehow pip causes errors)

Install uv:
```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Local Installation

```bash
# Install dependencies using uv
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate     # On Windows
```

### Docker Installation

Build and start with Docker Compose:

```bash
# Build and start
./docker.sh build
./docker.sh start

# Or manually
docker-compose up -d
```

## Usage

### Running Locally (stdio mode)

For use with Claude Desktop or other MCP clients:

```bash
# Using uv
uv run python -m dora_mcp

# Or with activated venv
python -m dora_mcp
```

### Running with Docker (HTTP mode)

The Docker deployment runs in HTTP/SSE mode for web access:

```bash
# Start the server
./docker.sh start

# Access at http://localhost:8000
# SSE endpoint: http://localhost:8000/sse
# Messages endpoint: http://localhost:8000/messages

# View logs
./docker.sh logs

# Run tests
./docker.sh test

# Stop the server
./docker.sh stop
```

See [DOCKER.md](DOCKER.md) for detailed Docker deployment guide.

### MCP Tools

The server provides the following tool:

#### `search_publications`

Search the DORA database for scientific publications.

**Parameters:**
- `search_string` (required): The search term to query. Can be an author name, title keyword, or any search term.

**Example:**
```json
{
  "search_string": "manfred heuberger"
}
```

## API Details

The server queries the DORA API with the following endpoint pattern:

```
https://www.dora.lib4ri.ch/empa/islandora/search/json_cit_a/[query]?search_string=[term]&extension=false
```

The search query includes weighted searches across multiple fields:
- Title (weight: 5)
- Abstract (weight: 2)
- Creator (weight: 2)
- Original Author List (weight: 2)
- Contributor (weight: 1)
- Type (weight: 1)
- Catch-all MODS fields (weight: 1)

## Development

### Requirements

- Python 3.10+
- uv package manager
- Dependencies listed in `pyproject.toml`

### Testing

```bash
# Install dev dependencies
uv sync --all-extras

# Run all tests
uv run python -m pytest tests/ -v

# Run specific test suites
uv run python -m pytest tests/test_server.py -v          # Unit tests
uv run python -m pytest tests/test_with_metrics.py -v   # Metrics tests
uv run python -m pytest tests/test_docker.py -v         # Docker tests

# Run manual tests
uv run python examples/test_search.py
```

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

## Transport Modes

The server supports two transport modes:

- **stdio** (default): For local MCP clients like Claude Desktop
- **http**: For web deployment with SSE (Server-Sent Events)

Set mode via environment variable:
```bash
# stdio mode (default)
uv run python -m dora_mcp

# HTTP mode
MCP_TRANSPORT=http MCP_PORT=8000 uv run python -m dora_mcp
```

## License

See LICENSE file for details.
