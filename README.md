# dora_mcp

MCP (Model Context Protocol) server for the [DORA](https://www.dora.lib4ri.ch/empa) scientific publications repository. Exposes two tools — search and abstract retrieval — over a standard HTTP Streamable transport (for Copilot Studio and other web clients).

## Requirements

- **Python 3.10+**
- **[uv](https://docs.astral.sh/uv/)** package manager

## Quick start

```bash
# Install dependencies
uv sync

# Setup environment
cp .env.example .env

# Run the server (defaults to http mode)
uv run dora_mcp
```

> **Note:** The server also supports an experimental `stdio` mode. Edit the `.env` file to switch to `stdio` or change the port. Open [http://localhost:8000](http://localhost:8000) for the landing page and Swagger UI if running in HTTP mode.

## MCP tools

| Tool | Description |
|---|---|
| `search_publications` | Search DORA by keyword or author name |
| `get_publication_abstract` | Fetch the abstract for a publication by ID or URL |

### `search_publications`

```json
{ 
  "search_string": "manfred heuberger",
  "limit": 10 
}
```

Use short keywords or an author name (1–3 words). Searches title, abstract, authors, and other metadata with weighted relevance. `limit` is optional (default 20).

### `get_publication_abstract`

```json
{ "identifier_or_url": "empa:27842" }
```

Accepts a full URL (`https://www.dora.lib4ri.ch/empa/item/empa:27842`) or just the publication identifier.

## Connecting AI clients

### Microsoft Copilot Studio

1. Enable **Generative orchestration** in your agent settings.
2. **Tools** → **Add a tool** → **New tool** → **Model Context Protocol**
3. Server URL: `https://your-app-name.fly.dev/mcp` — Authentication: None
4. Select **Create**, then **Add to agent**.

Alternatively import `api/openapi-copilot-studio.yaml` as a custom connector
(**Add a tool → New tool → Custom connector → Import OpenAPI file**).

## REST API

| Method | Path | Description |
|---|---|---|
| GET | `/` | Landing page |
| GET | `/docs` | Swagger UI |
| GET | `/health` | Health check |
| GET | `/tools` | List MCP tools (JSON) |
| POST | `/api/search` | Search — body: `{"search_string": "…", "limit": 10}` |
| POST | `/api/abstract` | Abstract — body: `{"identifier_or_url": "empa:…"}` |
| GET/POST | `/mcp` | MCP JSON-RPC endpoint |

OpenAPI specs are served at `/api/openapi.yaml` (REST) and `/api/openapi-copilot-studio.yaml` (Copilot Studio).

## Docker

```bash
./docker.sh build    # build image
./docker.sh start    # start container (http://localhost:8000)
./docker.sh stop     # stop container
./docker.sh logs     # view logs
./docker.sh status   # check status
./docker.sh rebuild  # rebuild + restart
./docker.sh clean    # remove everything
```

Or with docker-compose directly:

```bash
docker-compose up -d
```

Edit `docker-compose.yml` to change the port or environment variables.

## Fly.io deployment

```bash
flyctl launch      # first deploy (detects fly.toml automatically)
flyctl deploy      # redeploy after changes
flyctl logs        # view logs
flyctl status      # check status
```

The deployed app is available at `https://your-app-name.fly.dev`.

## Development

### Testing

```bash
uv run pytest tests/ -v                    # all tests
uv run pytest tests/test_server.py -v     # unit tests
uv run pytest tests/test_docker.py -v     # Docker tests (container must be running)

python tests/test_mcp_endpoint.py http://localhost:8000   # live endpoint check
python tests/test_search.py "manfred heuberger"           # manual search test
```

### Project layout

```
src/dora_mcp/
  server.py          # all server logic (MCP tools, HTTP routes)
  templates/
    index.html       # landing page template
api/
  openapi.yaml                  # Swagger 2.0 REST spec
  openapi-copilot-studio.yaml   # Copilot Studio spec
tests/
  test_server.py         # unit tests
  test_docker.py         # Docker container tests
  test_mcp_endpoint.py   # live endpoint smoke test
  test_search.py         # manual search script
```

## Possible Extensions

- **Claude Desktop Integration:** While not explicitly tested, this server should theoretically support Claude Desktop. You could attempt to integrate it using the standard HTTP transport pointing to `/mcp`, or by using the experimental `stdio` mode in your `claude_desktop_config.json`:
  ```json
  "mcpServers": {
    "dora": {
      "command": "uv",
      "args": ["run", "dora_mcp"],
      "cwd": "/path/to/dora_mcp",
      "env": { "MCP_TRANSPORT": "stdio" }
    }
  }
  ```
- **Advanced Metadata:** Support for fetching more detailed metadata like DOIs, publication years, or volume/issue info directly in the search results.
- **Improved Caching:** Implementation of a caching layer (e.g., Redis) for frequently requested search terms or abstracts.

## License

See [LICENSE](LICENSE).
