# PDF Full Text Feature Disabled

## Date: 2024

## Reason
The `get_publication_fulltext` feature has been **temporarily disabled** due to "payload too large" errors. 

When encoding PDFs (typically ~1.8MB) to base64 format, the resulting strings (~2.4M characters) exceed the practical JSON-RPC payload size limits for the MCP protocol.

## Changes Made

### 1. Server Code (`src/dora_mcp/server.py`)
- **Line 6**: Commented out `import base64` (no longer needed)
- **Lines ~170-222**: Commented out entire `get_publication_fulltext()` async function implementation
- **Lines ~300-330**: Commented out Tool registration for `get_publication_fulltext` in `list_tools()`
- **Lines ~386-415**: Commented out handler for `get_publication_fulltext` in `call_tool()`

All disabled code is marked with: `# DISABLED: Payload too large for MCP protocol`

### 2. Active Tools (Still Working)
✅ **search_publications** - Search DORA by keywords  
✅ **get_publication_abstract** - Retrieve publication abstracts and metadata

### 3. Disabled Tool
❌ **get_publication_fulltext** - Download PDF full text (disabled)

## Testing

After these changes, the server should:
- ✅ List only 2 tools (`search_publications`, `get_publication_abstract`)
- ✅ Compile without errors
- ✅ Return "Unknown tool" error if `get_publication_fulltext` is called
- ✅ Search and abstract extraction continue to work normally

## Future Considerations

To re-enable PDF downloads, consider:
1. **Chunked responses**: Split large PDFs into smaller chunks
2. **Streaming protocol**: Use HTTP streaming instead of JSON-RPC
3. **Direct URLs**: Return only the PDF URL, not the encoded content
4. **External storage**: Store PDFs temporarily and provide download links
5. **MCP protocol limits**: Check if future versions support larger payloads

## Rollback Instructions

To re-enable the feature:
1. Uncomment all sections marked with `# DISABLED: Payload too large for MCP protocol`
2. Uncomment `import base64` on line 6
3. Rebuild and deploy the Docker container

Note: Re-enabling will restore the "payload too large" errors unless a different solution is implemented.
