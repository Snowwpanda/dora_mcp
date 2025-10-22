# Quick Reference: Copilot Studio MCP Setup

## ✅ Your Server is Ready!

### What I Fixed:
1. ✅ Added `x-ms-agentic-protocol: mcp-streamable-1.0` to OpenAPI spec
2. ✅ Created minimal OpenAPI spec matching Microsoft's example
3. ✅ Added CORS support for Copilot Studio connections
4. ✅ Fixed OpenAPI YAML syntax (was mixing Swagger 2.0 and OpenAPI 3.0)
5. ✅ Created comprehensive testing and documentation

### Deploy & Test (3 steps):

```bash
# 1. Deploy to Fly.io
fly deploy

# 2. Test the MCP endpoint
python test_mcp_endpoint.py https://your-app-name.fly.dev

# 3. Add to Copilot Studio (see below)
```

### Add to Copilot Studio (2 methods):

#### Method 1: MCP Wizard (Easiest) ⭐
1. Copilot Studio → **Tools** → **Add a tool** → **Model Context Protocol**
2. Enter:
   - Name: `DORA Publications`
   - Description: `Search DORA for scientific publications`
   - URL: `https://your-app-name.fly.dev/mcp`
3. Click **Create** → **Add to agent**

#### Method 2: Custom Connector
1. Copilot Studio → **Tools** → **Custom connector**
2. **Import OpenAPI file** → Upload `openapi-minimal.yaml`
3. Complete setup in Power Apps

### Test in Copilot Studio:
Ask your agent:
- "Search DORA for publications by Manfred Heuberger"
- "Find climate change research in DORA"

### Important URLs:
| What | URL |
|------|-----|
| MCP Endpoint | `https://your-app.fly.dev/mcp` |
| OpenAPI Spec (minimal) | `https://your-app.fly.dev/openapi-minimal.json` |
| OpenAPI Spec (detailed) | `https://your-app.fly.dev/openapi-copilot.json` |
| Health Check | `https://your-app.fly.dev/health` |

### Documentation:
- Full setup guide: `COPILOT_STUDIO_SETUP.md`
- Fix summary: `COPILOT_FIX_SUMMARY.md`
- Main README: `README.md`

### Need Help?
Run the test script to verify everything works:
```bash
python test_mcp_endpoint.py https://your-app-name.fly.dev
```

All tests should pass ✓
