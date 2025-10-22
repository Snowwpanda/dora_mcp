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

### Local Installation

```bash
pip install -e .
```

### Docker Installation

Build the Docker image:

```bash
docker build -t dora-mcp .
```

## Usage

### Running Locally

```bash
python -m dora_mcp.server
```

### Running with Docker

```bash
docker run -i dora-mcp
```

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
- Dependencies listed in `pyproject.toml`

### Testing

```bash
pip install -e ".[dev]"
pytest
```

## License

See LICENSE file for details.
