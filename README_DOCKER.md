# 🐳 Docker Setup for Turath AI Agent

Complete Docker containerization for your Turath AI Agent system with MCP server and FastAPI application.

## 📋 Prerequisites

- Docker Desktop installed and running
- Docker Compose v2.0+
- WSL2 (recommended for Windows)
- Git

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp env.example .env

# Edit with your actual API keys
nano .env  # or use your preferred editor
```

### 2. Development Mode (Hot Reload)

```bash
# Using Docker Compose (recommended)
docker-compose up

# Or using convenience script (Linux/WSL)
./scripts/docker-run.sh dev

# Or using Windows batch file
scripts\docker-run.bat dev
```

### 3. Production Mode

```bash
# Linux/WSL
./scripts/docker-run.sh prod

# Windows
scripts\docker-run.bat prod

# Or manual
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   MCP Server    │
│   AI Agent      │◄──►│   (Turath)      │
│   Port: 8000    │    │   Port: 8001    │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
                 │
         ┌─────────────────┐
         │   Docker        │
         │   Network       │
         └─────────────────┘
```

## 📁 File Structure

```
├── Dockerfile              # FastAPI agent container
├── Dockerfile.mcp          # MCP server container
├── docker-compose.yml      # Base compose configuration
├── docker-compose.override.yml  # Development overrides
├── docker-compose.prod.yml # Production overrides
├── .dockerignore           # Files to exclude from build
├── env.example             # Environment template
└── scripts/
    ├── docker-build.sh     # Build script (Linux/WSL)
    ├── docker-run.sh       # Run script (Linux/WSL)
    └── docker-run.bat      # Run script (Windows)
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `TAVILY_API_KEY` | Tavily search API key | `tvly-...` |
| `MCP_SERVER_URL` | MCP server endpoint | `http://mcp-server:8001/sse` |
| `LOG_LEVEL` | Logging level | `info`, `debug` |

### Docker Compose Profiles

#### Development (`docker-compose.override.yml`)
- Hot reload enabled
- Source code mounted as volumes
- Debug logging
- Port mapping: 8000:8000, 8001:8001

#### Production (`docker-compose.prod.yml`)
- Resource limits
- Log rotation
- Restart policies
- Optimized for performance

## 🛠️ Commands

### Build Images

```bash
# Build all services
docker-compose build

# Build with no cache
docker-compose build --no-cache

# Build specific service
docker-compose build ai-agent
```

### Run Services

```bash
# Development (with hot reload)
docker-compose up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services
docker-compose up --scale ai-agent=2
```

### Logs and Monitoring

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f ai-agent

# Health checks
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:8001/sse
```

### Management

```bash
# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart specific service
docker-compose restart ai-agent

# Execute commands in container
docker-compose exec ai-agent bash
```

## 🔍 Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check what's using the ports
   netstat -tulpn | grep :8000
   netstat -tulpn | grep :8001
   ```

2. **Permission issues (Linux/WSL)**
   ```bash
   sudo chown -R $USER:$USER .
   chmod +x scripts/*.sh
   ```

3. **Database connection issues**
   ```bash
   # Check if database file exists
   ls -la turath_metadata.db
   
   # Verify file permissions
   chmod 644 turath_metadata.db
   ```

4. **Network connectivity**
   ```bash
   # Test internal network
   docker-compose exec ai-agent ping mcp-server
   
   # Check DNS resolution
   docker-compose exec ai-agent nslookup mcp-server
   ```

### Health Checks

Services include built-in health checks:

- **AI Agent**: `GET /health` → `{"status": "healthy"}`
- **MCP Server**: `GET /sse` → SSE connection test

### Resource Usage

Monitor resource consumption:

```bash
# Container stats
docker stats

# System resource usage
docker system df

# Remove unused resources
docker system prune
```

## 🔒 Security

- Non-root users in containers
- Read-only volume mounts where possible
- Network isolation
- Environment variable validation
- Security scanning with Hadolint

```bash
# Scan Dockerfile for security issues
hadolint Dockerfile
hadolint Dockerfile.mcp
```

## 📊 Production Deployment

### Resource Requirements

| Service | CPU | Memory | Storage |
|---------|-----|--------|---------|
| AI Agent | 0.5-1.0 cores | 512MB-1GB | 100MB |
| MCP Server | 0.25-0.5 cores | 256MB-512MB | 50MB + DB |

### Scaling

```bash
# Scale AI agent instances
docker-compose up --scale ai-agent=3

# Use with load balancer (nginx, traefik, etc.)
```

### Monitoring

Consider adding:
- Prometheus metrics
- Grafana dashboards
- Log aggregation (ELK stack)
- Health check endpoints

## 🎯 Performance Optimization

1. **Multi-stage builds** - Reduces image size
2. **Layer caching** - Faster builds
3. **Resource limits** - Prevents resource exhaustion
4. **Health checks** - Automatic recovery
5. **Graceful shutdown** - Proper cleanup

## 📝 Development Workflow

1. **Code changes** → Auto-reload in dev mode
2. **Test locally** → `docker-compose up`
3. **Build for production** → `./scripts/docker-build.sh`
4. **Deploy** → Production compose file

## 🤝 Contributing

When adding new features:
1. Update Dockerfile if dependencies change
2. Add environment variables to `env.example`
3. Update health checks if needed
4. Test both dev and prod configurations

---

**Happy Dockerizing! 🐳✨** 