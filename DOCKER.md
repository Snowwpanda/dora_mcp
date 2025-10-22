# Docker Deployment Guide

This guide covers running the DORA MCP server in Docker with HTTP/SSE transport.

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

**MCP Protocol Endpoints:**
- SSE: `http://localhost:8000/sse` - Server-Sent Events for MCP clients
- Messages: `http://localhost:8000/messages` - JSON-RPC messages (POST)

## Testing

```bash
# Automated tests (server must be running)
./docker.sh test

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
