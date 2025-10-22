# Testing the DORA MCP Server

This document describes how to test the DORA MCP server.

## Quick Start

```bash
# Run all automated tests
uv run python -m pytest tests/test_server.py -v

# Run tests with metrics output
uv run python -m pytest tests/test_with_metrics.py -v -s

# Run manual test with default searches
uv run python examples/test_search.py

# Run manual test with custom search
uv run python examples/test_search.py "your search term here"
```

## Test Suite Overview

### 1. Automated Unit Tests (`tests/test_server.py`)

The test suite includes:

- **Constants Tests**: Verify API endpoints and URLs
- **Search Query Tests**: Test query construction and URL encoding
- **MCP Protocol Tests**: Test tool listing and tool calling
- **DORA Integration Tests**: Real API tests with known queries
- **Error Handling Tests**: Test graceful error handling

Run with:
```bash
uv run python -m pytest tests/test_server.py -v
```

Example output:
```
tests/test_server.py::TestConstants::test_base_url PASSED
tests/test_server.py::TestMCPProtocol::test_list_tools PASSED
tests/test_server.py::TestDORAIntegration::test_search_manfred_heuberger PASSED
...
12 passed in 34.04s
```

### 2. Metrics Tests (`tests/test_with_metrics.py`)

**NEW!** Tests that generate detailed output files for tracking server behavior over time:

- **MCP Tools Inventory**: Lists all available tools with schemas
- **Search Results**: Complete results for "manfred heuberger" query
- **Performance Metrics**: Response times and data sizes
- **Output Files**: JSON files in `test_results/` directory

Run with:
```bash
uv run python -m pytest tests/test_with_metrics.py -v -s
```

Example output:
```
✓ Saved tools output to: test_results/tools_output.json
✓ Found 1 tool(s)
✓ Saved search results to: test_results/manfred_heuberger_search.json
✓ Found 110 publication(s)
✓ Result size: 53,358 bytes
✓ Elapsed time: 1.378s
```

**Generated Files:**
- `test_results/tools_output.json` - MCP tool definitions
- `test_results/manfred_heuberger_search.json` - Complete search results
- `test_results/mcp_tool_call_output.json` - MCP formatted response
- `test_results/summary_report.json` - Test run summary

See [`test_results/README.md`](test_results/README.md) for details on using these files to track changes over time.

### 3. Manual Test Script (`examples/test_search.py`)

Interactive test script that:
- Shows the constructed query
- Tests direct API calls
- Tests MCP tool calls
- Displays response previews
- Provides a summary report

Run with default searches:
```bash
uv run python examples/test_search.py
```

Run with custom search:
```bash
uv run python examples/test_search.py "manfred heuberger"
```

Example output:
```
======================================================================
Testing search: 'manfred heuberger'
======================================================================

1. Query constructed: mods_titleInfo_title_mt%3A%28manfred%20...
2. Testing direct API call...
   ✓ Got response of type: <class 'list'>
3. Testing MCP tool call...
   ✓ Got 1 TextContent objects
   ✓ Response has 52527 characters
```

## Test Cases

### Known Good Searches

These searches should return results:

1. **"manfred heuberger"** - Known author, should return publications
2. **"polymer tribology"** - Topic search, should return relevant papers
3. **"nanotechnology"** - General term, should return various papers

### Edge Cases

- Empty strings (should fail validation)
- Special characters (should be properly encoded)
- Very long search terms (should be handled)
- Nonexistent terms (should return empty results gracefully)

## What Gets Tested

### API Response Structure
- The DORA API returns a list of publication objects
- Each publication has: `pid`, `object_url`, `citation` fields
- Citations include multiple formats: ACS, APA, Chicago, etc.

### MCP Tool Behavior
- Tool listing returns the correct schema
- Tool calling requires `search_string` parameter
- Errors are caught and returned as TextContent
- Responses are properly formatted

## Expected Results

For `"manfred heuberger"`:
- Should return 50+ publications
- Should include citations in multiple formats
- Response size: ~50KB of JSON data

For `"polymer tribology"`:
- Should return relevant publications about polymers and tribology
- Response size: ~3-4KB of JSON data

## Troubleshooting

### Tests Fail Due to Network Issues
Some tests make real HTTP requests to the DORA API. If these fail:
- Check your internet connection
- Verify the DORA API is accessible: https://www.dora.lib4ri.ch/empa
- Tests will skip gracefully if the API is unavailable

### Import Errors
Make sure dependencies are installed:
```bash
uv sync --all-extras
```

### Slow Tests
Tests that query the real API can take 30+ seconds. This is normal as we:
- Make real HTTP requests
- Wait for API responses
- Test multiple search terms

## Continuous Integration

To add these tests to CI/CD:

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync --all-extras
      - run: uv run python -m pytest tests/ -v
```

## Adding New Tests

To add a new test case:

1. Add to `tests/test_server.py`:
```python
@pytest.mark.asyncio
async def test_my_new_feature(self):
    """Test description."""
    result = await my_function()
    assert result == expected
```

2. Or add to `examples/test_search.py`:
```python
test_cases = [
    "existing search",
    "my new search term",  # Add here
]
```

## Performance Benchmarks

Expected performance:
- Unit tests: < 1 second
- Integration tests: 30-40 seconds (due to network)
- Manual test script: 5-10 seconds per search

On WSL with `/mnt/c/` filesystem, add 2-5x overhead.
