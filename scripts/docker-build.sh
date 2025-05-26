#!/bin/bash

# Docker build script for Turath AI Agent
# Usage: ./scripts/docker-build.sh [--no-cache] [--push]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
PUSH=false
NO_CACHE=""
VERSION=$(date +%Y%m%d-%H%M%S)

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}🐳 Building Turath AI Agent Docker Images${NC}"
echo -e "${YELLOW}Version: ${VERSION}${NC}"

# Build MCP Server
echo -e "${GREEN}📦 Building MCP Server...${NC}"
docker build $NO_CACHE -f Dockerfile.mcp -t turath-mcp-server:latest -t turath-mcp-server:$VERSION .

# Build AI Agent
echo -e "${GREEN}🤖 Building AI Agent...${NC}"
docker build $NO_CACHE -f Dockerfile -t turath-ai-agent:latest -t turath-ai-agent:$VERSION .

# Optional push to registry
if [ "$PUSH" = true ]; then
    echo -e "${GREEN}🚀 Pushing images to registry...${NC}"
    docker push turath-mcp-server:latest
    docker push turath-mcp-server:$VERSION
    docker push turath-ai-agent:latest
    docker push turath-ai-agent:$VERSION
fi

echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo -e "${YELLOW}To run the services: docker-compose up${NC}" 