import logging
import ssl
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agno.playground import Playground
from agno.tools.mcp import MCPTools
from ..config import settings
from ..services.agent_factory import AgentService
from .workflow_routes import router as workflow_router

ssl._create_default_https_context = ssl._create_unverified_context

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("🚀 Starting Turath AI application...")
    logger.info(f"🔗 Connecting to MCP server at {settings.mcp_server_url}...")

    try:
        async with MCPTools(transport="sse", url=settings.mcp_server_url) as mcp_tools:
            logger.info("✅ Successfully connected to MCP server")

            # Initialize agent service
            agent_service = AgentService()
            agents, teams = await agent_service.initialize_agents(mcp_tools)

            # Store agent service in app state for workflow access
            app.state.agent_service = agent_service

            # Create Agno Playground
            playground = Playground(
                teams=list(teams.values()),
                agents=list(agents.values()),
            )

            # Get playground app and include its routes
            playground_app = playground.get_app()
            app.include_router(playground_app.router)

            logger.info("🎯 Agno Playground initialized and routes included")
            logger.info("📋 Workflow routes added at /workflows")
            logger.info("🌟 Application startup complete!")

            yield

    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise

    # Shutdown
    logger.info("🛑 Application shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="🕌 Turath AI API",
        description="Islamic Heritage and Text Analysis API powered by Agno with Workflow Orchestration",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include workflow routes
    app.include_router(workflow_router)

    @app.get("/")
    async def root():
        return {
            "message": "🕌 Welcome to Turath AI API",
            "status": "running",
            "docs": "/docs",
            "features": {
                "agents": "Individual AI agents for specific tasks",
                "teams": "Collaborative multi-agent teams",
                "workflows": "Orchestrated multi-stage research workflows",
                "playground": "Interactive Agno playground interface",
            },
            "endpoints": {
                "agents": "/agents",
                "teams": "/teams",
                "workflows": "/workflows",
                "playground": "/playground",
                "docs": "/docs",
            },
        }

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "turath-ai",
            "components": {
                "playground": "active",
                "workflows": "active",
                "mcp_connection": "active",
            },
        }

    return app


# Create the app instance
app = create_app()
