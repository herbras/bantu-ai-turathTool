# Deployment

This directory contains all Docker-related files for the Turath AI Agent project.

## Quick Start

### From Project Root
```bash
# Linux/Mac
./docker-compose-helper.sh up -d

# Windows PowerShell  
.\docker-compose-helper.ps1 up -d
```

### From This Directory
```bash
docker-compose up -d
```

## Files

- **docker-compose.yml** - Main service definitions
- **docker-compose.override.yml** - Development overrides
- **docker-compose.prod.yml** - Production optimizations
- **Dockerfile** - Main AI agent container
- **Dockerfile.mcp** - Turath MCP server container
- **requirements.txt** - Python dependencies for AI agent
- **requirements-mcp.txt** - Python dependencies for MCP server

## Environment Variables

Copy `../config/env.example` to `../.env` and configure:
- `OPENAI_API_KEY`
- `TAVILY_API_KEY`

## Services

- **ai-agent**: FastAPI application on port 8080
- **mcp-server**: Turath MCP server on port 8001 