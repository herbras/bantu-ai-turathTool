#!/bin/bash

# Docker run script for Turath AI Agent
# Usage: ./scripts/docker-run.sh [dev|prod] [--build]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENV="dev"
BUILD=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        dev|development)
            ENV="dev"
            shift
            ;;
        prod|production)
            ENV="prod"
            shift
            ;;
        --build)
            BUILD=true
            shift
            ;;
        *)
            echo "Usage: $0 [dev|prod] [--build]"
            exit 1
            ;;
    esac
done

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Copying from env.example...${NC}"
    if [ -f env.example ]; then
        cp env.example .env
        echo -e "${RED}🔑 Please edit .env file with your actual API keys before running!${NC}"
        exit 1
    else
        echo -e "${RED}❌ env.example file not found. Please create .env file manually.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}🐳 Starting Turath AI Agent in ${ENV} mode${NC}"

# Build if requested
if [ "$BUILD" = true ]; then
    echo -e "${GREEN}🔨 Building Docker images...${NC}"
    docker-compose build
fi

# Run based on environment
if [ "$ENV" = "prod" ]; then
    echo -e "${GREEN}🚀 Starting production environment...${NC}"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
else
    echo -e "${GREEN}🔧 Starting development environment...${NC}"
    docker-compose up
fi

if [ "$ENV" = "prod" ]; then
    echo -e "${GREEN}✅ Services started in production mode!${NC}"
    echo -e "${YELLOW}🌐 AI Agent: http://localhost:8000${NC}"
    echo -e "${YELLOW}🔧 MCP Server: http://localhost:8001${NC}"
    echo -e "${YELLOW}📊 Check logs: docker-compose logs -f${NC}"
    echo -e "${YELLOW}🛑 Stop services: docker-compose down${NC}"
fi 