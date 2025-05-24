from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
from src.services.agent_factory import AgentService
from src.api.v1_router import create_v1_router
from agno.tools.mcp import MCPTools
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import settings  # Corrected import path for settings

# Global instance of AgentService
agent_service = AgentService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    mcp_server_url = settings.mcp_server_url # Use the value from settings
    mcp_tools = None 
    try:
        print(f"🔧 Initializing MCPTools with URL: {mcp_server_url} using SSE transport...")
        # Corrected instantiation based on DynamicToolDiscovery
        mcp_tools = MCPTools(transport="sse", url=mcp_server_url)
        print("✅ MCPTools Initialized.")
    except Exception as e_generic:
        print(f"❌ A general error occurred during MCPTools initialization: {e_generic}. Dynamic tools may not work.")
        mcp_tools = None # Ensure mcp_tools is None

    print("🚀 Initializing Agents...")
    await agent_service.initialize_agents(mcp_tools=mcp_tools) 
    app.state.agent_service = agent_service 
    print("✅ Agents Initialized.")

    initialized_agent_instances = agent_service.get_all_agents()
    print(f"Retrieved {len(initialized_agent_instances)} agent instances from AgentService: {initialized_agent_instances}") 

    v1_api_router = await create_v1_router(initialized_agents=initialized_agent_instances)
    app.include_router(v1_api_router)
    print("✅ V1 API Router with Playground included.")

    yield
    print("ℹ️ Application shutdown.")

app = FastAPI(lifespan=lifespan)

# --- CORS Configuration --- 
# Define the origins allowed to make cross-origin requests.
# Based on your screenshot, the Agno Playground UI is at https://app.agno.com
# If you access it from other origins (e.g., localhost for development), add them too.
origins = [
    "https://app.agno.com", # From your screenshot's Referer header
    "http://localhost", # Common for local dev if UI served locally
    "http://localhost:3000", # Common for React/Vue/etc. dev servers
    "http://localhost:8000", # If UI is served by this app and makes client-side requests
    # Add your actual frontend origins here if different
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # List of allowed origins
    allow_credentials=True, # Allow cookies to be included in cross-origin requests
    allow_methods=["*"],    # Allow all standard HTTP methods
    allow_headers=["*"],    # Allow all headers
)
# --- End CORS Configuration ---

if __name__ == "__main__":
    print("🚀 Starting Turath AI Server with V1 Playground and CORS...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
