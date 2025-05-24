from fastapi import APIRouter
from typing import List, Dict
from agno.agent import Agent # Base class for type hinting
from agno.playground import Playground # CORRECTED IMPORT
import os

# This function will be called from main.py after agents are initialized
def create_v1_router(initialized_agents: List[Agent]) -> APIRouter:
    # --- Health Check Router --- 
    health_router = APIRouter(tags=["V1 Health"])
    @health_router.get("/health") # Changed path to /health as per your example
    def get_health() -> Dict[str, str]: # Synchronous as per example
        """Check the health of the API"""
        return {"status": "success"}

    # --- Playground Router --- 
    # Ensure all agents passed to Playground are actual agent instances
    print(f"Creating AGNO Playground with {len(initialized_agents)} agents.")
    for i, agent_instance in enumerate(initialized_agents):
        if not hasattr(agent_instance, 'name') or not agent_instance.name:
            default_name = f"agent_{i}"
            print(f"WARNING: Agent at index {i} has no name, assigning default: '{default_name}' for Playground.")
            # agno.playground.Playground might require agents to have a .name attribute.
            # If direct assignment isn't possible or doesn't work, this might need a wrapper.
            try:
                agent_instance.name = default_name
            except AttributeError:
                print(f"ERROR: Could not assign name to agent {type(agent_instance)}. Playground might fail.")
        print(f"  - Agent: {getattr(agent_instance, 'name', 'Unnamed Agent')} (Type: {type(agent_instance)})")

    # Create an agno.playground.Playground instance
    # The example uses: playground = Playground(agents=[web_agent, agno_assist, finance_agent])
    playground = Playground(agents=initialized_agents)

    # Get the async router for the playground
    # The example uses: playground_router = playground.get_async_router()
    playground_router = playground.get_async_router() # This provides the /playground routes

    # --- Main V1 Router --- 
    # The example also includes an 'agents_router'. For now, we'll stick to health and playground.
    # If you have a separate 'agents_router' (like your old src.api.routes), we can add it here.
    v1_router = APIRouter(prefix="/v1")
    v1_router.include_router(health_router)
    v1_router.include_router(playground_router) 

    print("AGNO V1 Router with Playground created.")
    return v1_router
