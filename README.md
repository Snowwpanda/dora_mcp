# dora_mcp

MCP (Model Context Protocol) server for the [DORA](https://www.dora.lib4ri.ch/empa) scientific publications repository. Exposes two tools — search and abstract retrieval — over both stdio (Claude Desktop) and HTTP Streamable transport (Copilot Studio, web clients).

## Quick start

```bash
# Install (requires uv — https://docs.astral.sh/uv/)
uv sync

# Run locally in stdio mode (for Claude Desktop)
uv run python -m dora_mcp

# Run as HTTP server (for Copilot Studio / browser)
$env:MCP_TRANSPORT="http"; $env:MCP_PORT="8000"; uv run python -m dora_mcp
# Linux/macOS: MCP_TRANSPORT=http MCP_PORT=8000 uv run python -m dora_mcp
```

Open [http://localhost:8000](http://localhost:8000) for the landing page and Swagger UI.

## MCP tools

| Tool | Description |
|---|---|
| `search_publications` | Search DORA by keyword or author name |
| `get_publication_abstract` | Fetch the abstract for a publication by ID or URL |

### `search_publications`

```json
{ "search_string": "manfred heuberger" }
```

Use short keywords or an author name (1–3 words). Searches title, abstract, authors, and other metadata with weighted relevance.

### `get_publication_abstract`

```json
{ "identifier_or_url": "empa:27842" }
```

Accepts a full URL (`https://www.dora.lib4ri.ch/empa/item/empa:27842`) or just the publication identifier.

## Connecting AI clients

### Claude Desktop

Add to `claude_desktop_config.json`
(`%APPDATA%\Claude\` on Windows, `~/Library/Application Support/Claude/` on macOS):

```json
{
  "mcpServers": {
    "dora": {
      "type": "http",
      "url": "https://dora-mcp-xrtnba.fly.dev/mcp"
    }
  }
}
```

For a local server replace the URL with `http://127.0.0.1:8000/mcp`.  
For **stdio mode** (Claude runs the process directly):

```json
{
  "mcpServers": {
    "dora": {
      "command": "uv",
      "args": ["run", "python", "-m", "dora_mcp"],
      "cwd": "/path/to/dora_mcp"
    }
  }
}
```

### Microsoft Copilot Studio

1. Enable **Generative orchestration** in your agent settings.
2. **Tools** → **Add a tool** → **New tool** → **Model Context Protocol**
3. Server URL: `https://dora-mcp-xrtnba.fly.dev/mcp` — Authentication: None
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
| POST | `/api/search` | Search — body: `{"search_string": "…"}` |
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
uv run pytest tests/test_with_metrics.py -v -s  # metrics + JSON output
uv run pytest tests/test_docker.py -v     # Docker tests (container must be running)

python tests/test_mcp_endpoint.py http://localhost:8000   # live endpoint check
python tests/test_search.py "manfred heuberger"           # manual search test
```

Metrics tests write JSON snapshots to `test_results/`. Run `scripts/compare_results.py` to diff two runs.

### Project layout

```
src/dora_mcp/
  server.py          # all server logic (MCP tools, HTTP routes)
  templates/
    index.html       # landing page template
api/
  openapi.yaml                  # Swagger 2.0 REST spec
  openapi-copilot-studio.yaml   # Copilot Studio spec
  open_tool_description.yaml    # tool description
tests/
  test_server.py         # unit tests
  test_with_metrics.py   # metrics / output tests
  test_docker.py         # Docker container tests
  test_mcp_endpoint.py   # live endpoint smoke test
  test_search.py         # manual search script
scripts/
  compare_results.py     # diff two test_results/ runs
test_results/            # JSON snapshots (gitignored by default)
```

### Disabled feature: PDF full text

`get_publication_fulltext` is commented out in `server.py`. PDFs encode to ~2.4 M chars of base64 which exceeds practical MCP payload limits. To re-enable: uncomment the function, the `Tool` registration, the `call_tool` branch, and `import base64`.

## License

See [LICENSE](LICENSE).
