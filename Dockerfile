FROM python:3.11-slim

# Install system dependencies including git (needed for uv to install from git repos)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        curl && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY requirements.txt ./

# Copy application code
COPY src/ ./src/

# Install dependencies using uv
RUN uv pip install --system --no-cache -r requirements.txt

# Set Python path to find the dora_mcp module
ENV PYTHONPATH=/app/src

# Set default transport to HTTP for Docker deployments
ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8080

# Expose the port (Fly.io uses 8080 by default)
EXPOSE 8080

# Set the entrypoint to run the MCP server
ENTRYPOINT ["python", "-m", "dora_mcp.server"]
