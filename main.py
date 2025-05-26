from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
from src.services.agent_factory import AgentService
from src.api.v1_router import create_v1_router
from agno.tools.mcp import MCPTools
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import settings

agent_service = AgentService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    mcp_server_url = settings.mcp_server_url

    print(f"🔧 Initializing MCPTools with URL: {mcp_server_url} using SSE transport...")
    
    # Use MCPTools as async context manager for proper connection handling
    async with MCPTools(transport="sse", url=mcp_server_url) as mcp_tools:
        print("✅ MCPTools Initialized and connected.")

        print("🚀 Initializing Agents...")
        await agent_service.initialize_agents(
            mcp_tools=mcp_tools,
            tavily_api_key=settings.tavily_api_key  # Add Tavily API key support
        ) 
        app.state.agent_service = agent_service 
        print("✅ Agents Initialized.")

        initialized_agent_instances = agent_service.get_all_agents()

        v1_api_router = await create_v1_router(initialized_agents=initialized_agent_instances)
        app.include_router(v1_api_router)
        print("✅ V1 API Router with Playground included.")

        yield
        
    print("ℹ️ Application shutdown and MCPTools disconnected.")

app = FastAPI(lifespan=lifespan)

origins = [
    "https://app.agno.com",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    print("🚀 Starting Turath AI Server with V1 Playground and CORS...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
