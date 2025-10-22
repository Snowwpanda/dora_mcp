#!/bin/bash
# Docker management script for DORA MCP server

set -e

CONTAINER_NAME="dora-mcp-server"
IMAGE_NAME="dora-mcp:latest"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo_success() {
    echo -e "${GREEN}✓${NC} $1"
}

echo_info() {
    echo -e "${YELLOW}➜${NC} $1"
}

echo_error() {
    echo -e "${RED}✗${NC} $1"
}

case "$1" in
    build)
        echo_info "Building Docker image..."
        docker build -t $IMAGE_NAME .
        echo_success "Image built successfully"
        ;;
    
    start)
        echo_info "Starting MCP server..."
        docker-compose up -d
        echo_success "Server started"
        echo_info "Waiting for server to be ready..."
        sleep 3
        echo_info "Server URL: http://localhost:8000"
        echo_info "SSE endpoint: http://localhost:8000/sse"
        echo_info "Messages endpoint: http://localhost:8000/messages"
        ;;
    
    stop)
        echo_info "Stopping MCP server..."
        docker-compose down
        echo_success "Server stopped"
        ;;
    
    restart)
        echo_info "Restarting MCP server..."
        docker-compose restart
        echo_success "Server restarted"
        ;;
    
    logs)
        echo_info "Showing logs (Ctrl+C to exit)..."
        docker logs -f $CONTAINER_NAME
        ;;
    
    status)
        if docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}" | grep -q "Up"; then
            STATUS=$(docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}")
            echo_success "Server is running: $STATUS"
            PORT=$(docker ps --filter "name=$CONTAINER_NAME" --format "{{.Ports}}" | cut -d':' -f2 | cut -d'-' -f1)
            echo_info "Accessible at: http://localhost:${PORT:-8000}"
        else
            echo_error "Server is not running"
            exit 1
        fi
        ;;
    
    test)
        echo_info "Running Docker tests..."
        if ! docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}" | grep -q "Up"; then
            echo_error "Server is not running. Start it first with: ./docker.sh start"
            exit 1
        fi
        uv run python -m pytest tests/test_docker.py -v -s
        ;;
    
    rebuild)
        echo_info "Rebuilding and restarting..."
        docker-compose down
        docker build -t $IMAGE_NAME .
        docker-compose up -d
        echo_success "Rebuild complete"
        ;;
    
    clean)
        echo_info "Cleaning up..."
        docker-compose down
        docker rmi $IMAGE_NAME 2>/dev/null || true
        echo_success "Cleanup complete"
        ;;
    
    shell)
        echo_info "Opening shell in container..."
        docker exec -it $CONTAINER_NAME /bin/bash
        ;;
    
    *)
        echo "Usage: $0 {build|start|stop|restart|logs|status|test|rebuild|clean|shell}"
        echo ""
        echo "Commands:"
        echo "  build    - Build the Docker image"
        echo "  start    - Start the MCP server"
        echo "  stop     - Stop the MCP server"
        echo "  restart  - Restart the MCP server"
        echo "  logs     - Show server logs"
        echo "  status   - Check server status"
        echo "  test     - Run Docker tests (server must be running)"
        echo "  rebuild  - Rebuild image and restart server"
        echo "  clean    - Stop and remove containers and images"
        echo "  shell    - Open a shell in the container"
        exit 1
        ;;
esac
