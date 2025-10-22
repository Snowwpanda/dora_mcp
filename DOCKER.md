# Docker Deployment Guide

This guide covers running the DORA MCP server in Docker with HTTP Streamable transport.

## Quick Start

```bash
# Build and start the server
./docker.sh build
./docker.sh start

# Check status
./docker.sh status

# View logs
./docker.sh logs

# Run tests
./docker.sh test

# Stop the server
./docker.sh stop
```

## Server URL

Once running, access at: **http://localhost:8000**

**REST Endpoints:**
- Root: `http://localhost:8000/` - API documentation
- Health: `http://localhost:8000/health` - Health check
- Tools: `http://localhost:8000/tools` - List available MCP tools
- Search: `http://localhost:8000/api/search` - REST API for searching publications
- Connector: `http://localhost:8000/connector` - Power Automate connector endpoint

**MCP Protocol Endpoints:**
- MCP: `http://localhost:8000/mcp` - MCP Streamable endpoint (for Copilot Studio)

**OpenAPI Specifications:**
- `/openapi-minimal.json` - Minimal spec for Copilot Studio
- `/openapi-copilot.json` - Detailed spec for Copilot Studio
- `/openapi-connector.json` - Spec for Power Automate connectors

## Testing

```bash
# Automated tests (server must be running)
./docker.sh test

# Test MCP endpoint
python test_mcp_endpoint.py http://localhost:8000

# Manual health check
curl http://localhost:8000/health

# List available tools
curl http://localhost:8000/tools

# Get API documentation
curl http://localhost:8000/
```

## Management Commands

```bash
./docker.sh build    # Build the Docker image
./docker.sh start    # Start the server
./docker.sh stop     # Stop the server
./docker.sh restart  # Restart the server
./docker.sh logs     # View logs
./docker.sh status   # Check if running
./docker.sh test     # Run Docker tests
./docker.sh rebuild  # Rebuild and restart
./docker.sh clean    # Remove everything
```

## Configuration

Edit `docker-compose.yml` to change port or settings:

```yaml
ports:
  - "9000:8000"  # Use port 9000 externally
environment:
  - MCP_PORT=8000
```

See [full Docker documentation](DOCKER.md) for advanced deployment options.
