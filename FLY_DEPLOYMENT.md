# Fly.io Deployment Guide

This guide walks you through deploying the DORA MCP Server to Fly.io.

## Prerequisites

1. **Install Fly CLI**
   ```bash
   # macOS
   brew install flyctl
   
   # Linux
   curl -L https://fly.io/install.sh | sh
   
   # Windows
   pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Sign up/Login to Fly.io**
   ```bash
   flyctl auth signup
   # or
   flyctl auth login
   ```

## Deployment Steps

### 1. Launch Your Application

From the project root directory:

```bash
flyctl launch
```

This will:
- Detect your `fly.toml` configuration
- Create a new app on Fly.io
- Ask you to confirm the app name and region
- Deploy your application

**Important:** When prompted:
- Choose a unique app name (or use suggested one)
- Select your preferred region (default: `iad` - US East)
- Say **NO** to PostgreSQL database (not needed)
- Say **NO** to Redis (not needed)

### 2. Deploy Updates

After making changes to your code:

```bash
flyctl deploy
```

### 3. Open Your Application

```bash
flyctl open
```

This will open your deployed MCP server in a browser.

## Access Your Server

After deployment, your server will be available at:

```
https://your-app-name.fly.dev
```

### Available Endpoints

- **Root**: `https://your-app-name.fly.dev/`
  - API documentation and information
  
- **Health Check**: `https://your-app-name.fly.dev/health`
  - Server health status
  
- **Tools List**: `https://your-app-name.fly.dev/tools`
  - List of available MCP tools
  
- **SSE Stream**: `https://your-app-name.fly.dev/sse`
  - Server-Sent Events endpoint for MCP clients
  
- **Messages**: `https://your-app-name.fly.dev/messages`
  - JSON-RPC endpoint for MCP protocol

## Useful Commands

### View Logs
```bash
flyctl logs
```

### Check Status
```bash
flyctl status
```

### SSH into Machine
```bash
flyctl ssh console
```

### Monitor Resources
```bash
flyctl dashboard
```

### Scale Resources

If you need more memory or CPU:

```bash
# Scale memory
flyctl scale memory 1024

# Scale CPU
flyctl scale vm shared-cpu-2x

# Scale instances (for high availability)
flyctl scale count 2
```

### Set Environment Variables

If you need to add custom environment variables:

```bash
flyctl secrets set MY_VAR=value
```

## Configuration

The `fly.toml` file contains all configuration:

- **Port**: 8080 (internal)
- **Region**: `iad` (US East) - change in fly.toml
- **Memory**: 512MB - scale up if needed
- **Auto-stop**: Disabled (keeps server running)
- **Health checks**: Uses `/health` endpoint every 30s

## Cost

Fly.io free tier includes:
- Up to 3 shared-cpu-1x VMs with 256MB RAM each
- 160GB outbound data transfer

This server uses:
- 1 VM with 512MB RAM (within free tier if only app)

Monitor your usage at: https://fly.io/dashboard

## Troubleshooting

### Deployment Fails

```bash
# Check logs for errors
flyctl logs

# Restart the app
flyctl restart
```

### App Not Responding

```bash
# Check machine status
flyctl status

# Check health check
curl https://your-app-name.fly.dev/health
```

### Port Issues

Make sure your Dockerfile exposes port 8080:
```dockerfile
EXPOSE 8080
```

And the server starts with:
```bash
uvicorn src.dora_mcp.server:app --host 0.0.0.0 --port 8080
```

## Testing Your Deployment

### Test with curl

```bash
# Health check
curl https://your-app-name.fly.dev/health

# List tools
curl https://your-app-name.fly.dev/tools

# Test SSE endpoint
curl -N https://your-app-name.fly.dev/sse
```

### Test with MCP Client

Use any MCP-compatible client and point it to:
```
https://your-app-name.fly.dev
```

## Rollback

If a deployment breaks something:

```bash
# List releases
flyctl releases

# Rollback to previous version
flyctl releases rollback
```

## Delete App

To completely remove your app from Fly.io:

```bash
flyctl apps destroy your-app-name
```

## Next Steps

- **Custom Domain**: Add your own domain with `flyctl certs add yourdomain.com`
- **Multi-Region**: Deploy to multiple regions for global availability
- **Monitoring**: Set up alerts and metrics at https://fly.io/dashboard
- **CI/CD**: Integrate with GitHub Actions for automatic deployments

## Support

- Fly.io Docs: https://fly.io/docs/
- Community Forum: https://community.fly.io/
- Status Page: https://status.fly.io/
