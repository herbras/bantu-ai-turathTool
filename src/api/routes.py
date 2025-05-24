from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()

# Pydantic model for the agent invocation request body
class AgentInvokeRequest(BaseModel):
    input_query: str
    # You can add other parameters like session_id, etc., if needed
    # session_id: Optional[str] = None 

@router.get("/agents")
async def list_agents(request: Request) -> Dict[str, Any]:
    """List all available agents"""
    agent_service = request.app.state.agent_service
    if not agent_service or not hasattr(agent_service, 'agents'):
        raise HTTPException(status_code=500, detail="Agent service not initialized or agents not loaded")
    return {"agents": list(agent_service.agents.keys())}


@router.get("/teams")
async def list_teams(request: Request) -> Dict[str, Any]:
    """List all available teams"""
    agent_service = request.app.state.agent_service
    if not agent_service or not hasattr(agent_service, 'teams'):
        raise HTTPException(status_code=500, detail="Agent service not initialized or teams not loaded")
    return {"teams": list(agent_service.teams.keys())}


@router.get("/status")
async def get_status() -> Dict[str, str]:
    """Get application status"""
    return {"status": "running", "version": "1.0.0"}


@router.post("/agents/{agent_name}/invoke")
async def invoke_agent(agent_name: str, payload: AgentInvokeRequest, request: Request) -> Dict[str, Any]:
    """Invoke a specific agent with a query."""
    agent_service = request.app.state.agent_service
    if not agent_service:
        raise HTTPException(status_code=500, detail="Agent service not available")

    agent = agent_service.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found.")

    try:
        # Assuming the agent has a 'handle_query' method as seen in TurathQueryAgent
        raw_agent_response = await agent.handle_query(query=payload.input_query)

        print(f"DEBUG: Type of raw_agent_response: {type(raw_agent_response)}")
        print(f"DEBUG: Content of raw_agent_response: {raw_agent_response}")

        # Attempt to extract serializable content.
        # This depends on how 'agno.agent.Agent' structures its response.
        # Common patterns include a dictionary or an object with an attribute like 'output', 'content', or 'text'.
        if isinstance(raw_agent_response, dict):
            # If it's a dict, try to find a common key or return the whole dict if it's simple enough
            # This might need refinement based on the actual dict structure
            final_response = raw_agent_response.get("output", raw_agent_response.get("content", raw_agent_response))
        elif hasattr(raw_agent_response, 'output'): # Check for an 'output' attribute
            final_response = raw_agent_response.output
        elif hasattr(raw_agent_response, 'content'): # Check for a 'content' attribute
            final_response = raw_agent_response.content
        elif hasattr(raw_agent_response, 'text'): # Check for a 'text' attribute for string-like responses
            final_response = raw_agent_response.text
        elif isinstance(raw_agent_response, str):
            final_response = raw_agent_response
        else:
            # If unsure, convert to string as a fallback, though this might not be ideal JSON
            print("WARNING: Agent response is of an unexpected type, attempting str conversion.")
            final_response = str(raw_agent_response) 

        return {"agent_name": agent_name, "response": final_response}
    except Exception as e:
        # Log the exception e for debugging
        print(f"ERROR in invoke_agent: {e}") # Added print for server log
        raise HTTPException(status_code=500, detail=f"Error invoking agent '{agent_name}': {str(e)}")
