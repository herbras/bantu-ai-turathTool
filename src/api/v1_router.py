from fastapi import APIRouter
from agno.agent import Agent  # Base class for type hinting
from agno.playground import Playground
from typing import List, Dict  # Ensure List and Dict are imported

# Import teams
from src.teams.turath_research_team import get_turath_research_team

# Import workflows
from src.workflows import TurathResearchWorkflow, TurathPublicationWorkflow

# The TurathQueryAgent and its config are used by get_turath_research_team internally.
# If TurathQueryAgent is also initialized in main.py and passed via initialized_agents,
# it will be available directly in the playground. The team will use its own instance.


# This function will be called from main.py after agents are initialized
async def create_v1_router(
    initialized_agents: List[Agent], agent_service=None
) -> APIRouter:
    # --- Health Check Router ---
    health_router = APIRouter(tags=["V1 Health"])

    @health_router.get("/health")  # Changed path to /health as per your example
    async def get_health() -> Dict[str, str]:  # Changed to async
        """Check the health of the API"""
        return {"status": "success"}

    turath_research_team = await get_turath_research_team()

    # Initialize workflow instances with agent service injection
    research_workflow = TurathResearchWorkflow(session_id="playground_research")
    publication_workflow = TurathPublicationWorkflow(
        session_id="playground_publication"
    )

    # Debug agent service injection
    print(f"🔍 Agent service type: {type(agent_service)}")
    print(f"🔍 Agent service is None: {agent_service is None}")
    if agent_service:
        print(
            f"🔍 Available agents: {list(agent_service.agents.keys()) if hasattr(agent_service, 'agents') else 'No agents attr'}"
        )

    # Inject agent service into workflows
    research_workflow._agent_service = agent_service
    publication_workflow._agent_service = agent_service

    # Verify injection
    print(f"🔍 Research workflow agent service: {research_workflow._agent_service}")
    print(
        f"🔍 Publication workflow agent service: {publication_workflow._agent_service}"
    )

    workflows = [research_workflow, publication_workflow]

    # Create an agno.playground.Playground instance
    playground = Playground(
        agents=initialized_agents,  # These are the agents initialized in main.py
        workflows=workflows,  # Add the Turath workflows
        teams=[turath_research_team],  # Add the new team
    )

    # Get the async router for the playground
    playground_router = playground.get_async_router()

    # --- Main V1 Router ---
    v1_router = APIRouter(prefix="/v1")
    v1_router.include_router(health_router)
    v1_router.include_router(playground_router)

    print("AGNO V1 Router with Playground created.")
    print(
        f"Registered {len(workflows)} workflows: {[w.__class__.__name__ for w in workflows]}"
    )
    return v1_router
