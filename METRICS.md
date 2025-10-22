# Test Metrics System - Summary

## What Was Created

A comprehensive testing and metrics system for tracking the DORA MCP server behavior over time.

## Files Created

### Test Files
1. **`tests/test_with_metrics.py`** - Automated tests that generate metrics output
   - Tests MCP tool listing
   - Tests search for "manfred heuberger"
   - Tests MCP tool call with formatted response
   - Generates JSON output files with timestamps and metrics

### Output Files (in `test_results/`)
2. **`test_results/tools_output.json`** (~1 KB)
   - Lists all MCP tools offered by the server
   - Tool names, descriptions, input schemas
   - Elapsed time for listing tools

3. **`test_results/manfred_heuberger_search.json`** (~50-60 KB)
   - Complete search results for "manfred heuberger"
   - **110 publications** found
   - Response time: ~1.4s
   - Full result with all citations
   - Sample publications for quick review

4. **`test_results/mcp_tool_call_output.json`** (~50-60 KB)
   - MCP protocol formatted response
   - Text content returned by tool
   - Character count (~52,000 chars)
   - Response time: ~1.1s

5. **`test_results/summary_report.json`** (< 1 KB)
   - Overview of test run
   - List of all generated files

### Documentation
6. **`test_results/README.md`**
   - Explains each output file
   - How to track changes over time
   - What metrics to monitor
   - Alerting guidelines

7. **Updated `TESTING.md`**
   - Added metrics tests section
   - Updated quick start guide

### Utilities
8. **`scripts/compare_results.py`**
   - Compare test results between two runs
   - Detect changes in publication counts
   - Track performance regressions
   - Monitor API changes

### Configuration
9. **Updated `.gitignore`**
   - Excludes `test_results/` directory by default
   - Can be committed if desired for tracking

## How to Use

### Run Tests with Metrics

**Unit Mode (Direct Function Calls):**
```bash
cd /mnt/c/git/dora_mcp
uv run python -m pytest tests/test_with_metrics.py -v -s
```

**HTTP Mode (Against Running Server):**
```bash
# Start Docker server first
./docker.sh start

# Run metrics tests in HTTP mode
TEST_MODE=http TEST_SERVER_URL=http://localhost:8000 \
  uv run python -m pytest tests/test_with_metrics.py -v -s
```

The metrics tests are now **adaptable** and can run in both modes. Output files are named with the mode suffix:
- `tools_output_unit.json` or `tools_output_http.json`
- `manfred_heuberger_search_unit.json` or `manfred_heuberger_search_http.json`
- `mcp_tool_call_output_unit.json` or `mcp_tool_call_output_http.json`
- `summary_report_unit.json` or `summary_report_http.json`

### View Generated Files
```bash
ls -lh test_results/
cat test_results/tools_output.json
cat test_results/summary_report.json
```

### Track Changes Over Time
```bash
# Run tests
uv run pytest tests/test_with_metrics.py -v -s

# Archive results with timestamp
timestamp=$(date +%Y-%m-%d_%H-%M-%S)
cp -r test_results "test_results_${timestamp}"

# Compare with previous run
python scripts/compare_results.py \
  test_results_2025-10-22/manfred_heuberger_search.json \
  test_results/manfred_heuberger_search.json
```

## What Gets Tracked

### MCP Tools
- ✅ Tool count (currently: 1)
- ✅ Tool names (currently: "search_publications")
- ✅ Tool descriptions and schemas
- ✅ Response time for listing tools

### Search Results for "manfred heuberger"
- ✅ Publication count (currently: **110**)
- ✅ Response time (currently: ~1.4s)
- ✅ Result size (currently: ~53KB)
- ✅ Sample publications (first 3)
- ✅ **Complete results** with all publications

### MCP Tool Call
- ✅ Formatted text response
- ✅ Character count (currently: ~52,000)
- ✅ Response time (currently: ~1.1s)

## Current Baseline Metrics (Oct 22, 2025)

```json
{
  "tools": {
    "count": 1,
    "names": ["search_publications"]
  },
  "manfred_heuberger_search": {
    "publications": 110,
    "response_time_seconds": 1.378,
    "result_size_bytes": 53358
  },
  "mcp_tool_call": {
    "response_time_seconds": 1.110,
    "text_length_chars": 52527
  }
}
```

## Monitoring Recommendations

### Weekly Checks
- Run metrics tests weekly
- Archive results with timestamp
- Compare with previous week

### Alert Conditions
- ⚠️ Publication count drops significantly (>10%)
- ⚠️ Response time increases significantly (>50%)
- ⚠️ Tool count changes
- ⚠️ Tool schemas change
- ⚠️ Error responses appear

### What Changes to Expect
- ✅ **Publication count increase**: Normal as new papers are added
- ✅ **Minor response time variations**: Normal (±20%)
- ⚠️ **Tool schema changes**: Review for breaking changes
- ⚠️ **Significant performance degradation**: Investigate

## Example Workflow

### 1. Initial Baseline
```bash
# Create baseline
uv run pytest tests/test_with_metrics.py -v -s
mv test_results test_results_baseline
```

### 2. Regular Testing
```bash
# Run tests (weekly/monthly)
uv run pytest tests/test_with_metrics.py -v -s

# Compare with baseline
python scripts/compare_results.py \
  test_results_baseline/manfred_heuberger_search.json \
  test_results/manfred_heuberger_search.json
```

### 3. Review Results
```bash
# Check current metrics
cat test_results/summary_report.json

# Review sample publications
jq '.sample_publications' test_results/manfred_heuberger_search.json
```

## Benefits

1. **Change Detection**: Automatically detect API changes
2. **Performance Tracking**: Monitor response times over time
3. **Data Validation**: Ensure consistent response structure
4. **Regression Testing**: Catch breaking changes early
5. **Documentation**: Baseline metrics for reference
6. **Debugging**: Full results available for investigation

## Integration Options

### GitHub Actions (CI/CD)
```yaml
name: Weekly Metrics
on:
  schedule:
    - cron: '0 0 * * 0'
jobs:
  metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync --all-extras
      - run: uv run pytest tests/test_with_metrics.py -v -s
      - uses: actions/upload-artifact@v4
        with:
          name: metrics-${{ github.run_number }}
          path: test_results/
```

### Local Cron Job
```bash
# Add to crontab
0 0 * * 0 cd /path/to/dora_mcp && uv run pytest tests/test_with_metrics.py
```

## Next Steps

1. ✅ Run initial baseline tests
2. ✅ Archive baseline results
3. 📅 Schedule regular test runs (weekly/monthly)
4. 📊 Set up monitoring alerts (optional)
5. 📈 Review trends over time

## Questions?

See:
- `TESTING.md` - Full testing documentation
- `test_results/README.md` - Output files documentation
- `tests/test_with_metrics.py` - Test implementation
