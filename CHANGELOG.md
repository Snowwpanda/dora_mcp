# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-22

### Added
- Initial release of DORA MCP Server
- MCP server implementation using the `mcp` library (v0.9.0+)
- Integration with DORA (Digital Object Repository for Academia) API
- `search_publications` tool for searching scientific publications
- Multi-field search with weighted relevance:
  - Title (weight: 5)
  - Abstract (weight: 2)  
  - Creator (weight: 2)
  - Original Author List (weight: 2)
  - Contributor (weight: 1)
  - Type (weight: 1)
  - Catch-all MODS fields (weight: 1)
- Docker support with Dockerfile and docker-compose.yml
- Comprehensive documentation:
  - README.md with project overview
  - INSTALLATION.md with setup instructions
  - USAGE.md with detailed usage examples
- Example scripts for testing (examples/test_search.py)
- Unit tests for core functionality
- Python package configuration (pyproject.toml)
- Direct dependency list (requirements.txt)

### Technical Details
- Python 3.10+ required
- Uses httpx for async HTTP requests
- Implements MCP protocol via stdio
- Containerized with Python 3.11-slim base image
- No external environment variables required for basic operation

### Security
- All dependencies checked for vulnerabilities (0 found)
- CodeQL security analysis passed with 0 alerts

[0.1.0]: https://github.com/Snowwpanda/dora_mcp/releases/tag/v0.1.0
