FROM python:3.11-slim

# Install ca-certificates and update them to avoid SSL issues
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Set Python path to find the dora_mcp module
ENV PYTHONPATH=/app/src

# Set the entrypoint to run the MCP server
ENTRYPOINT ["python", "-m", "dora_mcp.server"]
