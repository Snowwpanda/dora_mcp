# Installation Guide

This guide provides detailed instructions for installing and setting up the DORA MCP Server.

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- (Optional) Docker and Docker Compose for containerized deployment

## Installation Methods

### Method 1: Local Installation (Recommended for Development)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Snowwpanda/dora_mcp.git
   cd dora_mcp
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On Linux/Mac:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install the package:**
   ```bash
   pip install -e .
   ```

4. **Verify installation:**
   ```bash
   python -c "from dora_mcp import server; print('Installation successful!')"
   ```

### Method 2: Docker Installation (Recommended for Production)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Snowwpanda/dora_mcp.git
   cd dora_mcp
   ```

2. **Build the Docker image:**
   ```bash
   docker build -t dora-mcp .
   ```

3. **Verify the image:**
   ```bash
   docker images | grep dora-mcp
   ```

### Method 3: Docker Compose (Easiest for Quick Setup)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Snowwpanda/dora_mcp.git
   cd dora_mcp
   ```

2. **Start the service:**
   ```bash
   docker-compose up -d
   ```

3. **Check the service status:**
   ```bash
   docker-compose ps
   ```

## Development Installation

For development with additional tools and dependencies:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# This includes:
# - pytest for testing
# - pytest-asyncio for async test support
```

## Running the Server

### Local Execution

```bash
# Run directly
python -m dora_mcp.server

# Or run from the src directory
cd src
python -m dora_mcp.server
```

### Docker Execution

```bash
# Run interactively
docker run -i dora-mcp

# Run with docker-compose
docker-compose up
```

## Configuration

The server uses the DORA API at `https://www.dora.lib4ri.ch/empa`. No additional configuration is required for basic operation.

### Environment Variables

Currently, the server does not require any environment variables. All configuration is built into the code.

For future customization, you can create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

## Testing the Installation

### Quick Test

```bash
# Test the search query builder
python -c "from dora_mcp.server import build_search_query; print(build_search_query('test'))"
```

### Run Example Script

```bash
# Test with default search term
python examples/test_search.py

# Test with custom search term
python examples/test_search.py "manfred heuberger"
```

### Run Unit Tests

```bash
# Install test dependencies first
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

### Manual Server Test

You can test the server manually by running it and sending MCP protocol messages via stdin:

```bash
python -m dora_mcp.server
```

The server will wait for JSON-RPC messages on stdin.

## Integration with MCP Clients

### Claude Desktop

1. Locate your Claude Desktop configuration file:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. Add the DORA MCP server configuration:

   **For local installation:**
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

   **For Docker installation:**
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

3. Restart Claude Desktop

4. The DORA search tool should now be available in Claude

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'dora_mcp'`

**Solution:**
```bash
# Make sure you're in the right directory
cd /path/to/dora_mcp

# Reinstall the package
pip install -e .
```

### Permission Errors

**Problem:** Permission denied when installing

**Solution:**
```bash
# Use a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .

# Or install with --user flag
pip install --user -e .
```

### Docker Build Fails

**Problem:** SSL certificate errors during build

**Solution:**
```bash
# Try building with host network
docker build --network=host -t dora-mcp .

# Or update ca-certificates on your system
sudo apt-get update && sudo apt-get install ca-certificates
```

### Network Connectivity Issues

**Problem:** Cannot connect to DORA API

**Solution:**
- Check your internet connection
- Verify the DORA website is accessible: https://www.dora.lib4ri.ch/empa
- Check if you're behind a proxy or firewall
- Try accessing the API directly in your browser

### Python Version Issues

**Problem:** The server requires Python 3.10+

**Solution:**
```bash
# Check your Python version
python --version

# If needed, use a specific Python version
python3.10 -m venv venv
source venv/bin/activate
pip install -e .
```

## Uninstallation

### Local Installation

```bash
pip uninstall dora-mcp
```

### Docker Installation

```bash
# Remove the container
docker-compose down

# Remove the image
docker rmi dora-mcp

# Remove unused volumes
docker volume prune
```

## Next Steps

After installation:

1. Read the [USAGE.md](USAGE.md) guide for detailed usage instructions
2. Try the example scripts in the `examples/` directory
3. Check the [README.md](README.md) for API details and features
4. Run the tests to ensure everything works correctly

## Getting Help

If you encounter issues:

1. Check this installation guide thoroughly
2. Review the troubleshooting section
3. Check the existing issues on GitHub
4. Create a new issue with:
   - Your operating system and version
   - Python version (`python --version`)
   - Error messages and stack traces
   - Steps to reproduce the problem
