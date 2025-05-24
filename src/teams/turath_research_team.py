import os
from agno.team import Team
from ..agents.turath_query import create_turath_query_agent, TurathQueryAgent
from ..agents.turath_team_manager import TurathTeamManagerAgent
from agno.tools.mcp import MCPTools
from ..config import settings
from typing import List, Any
from agno.models.openai.like import OpenAILike

def get_turath_query_agent_instance(mcp_tools_instance: MCPTools = None) -> TurathQueryAgent:
    """Gets an instance of the TurathQueryAgent using the factory method."""
    # create_turath_query_agent no longer uses mcp_tools_instance for dynamic discovery
    return create_turath_query_agent(mcp_tools_instance=mcp_tools_instance) # Pass mcp_tools_instance

def get_turath_team_manager_agent_instance(tools: List[Any] = None): 
    """Gets an instance of the TurathTeamManagerAgent."""
    return TurathTeamManagerAgent(
        tools=tools # Pass tools to the agent
    )

async def get_turath_research_team() -> Team:
    # Get MCP_SERVER_URL from environment or settings
    mcp_server_url_val = os.getenv("MCP_SERVER_URL", settings.mcp_server_url or "http://127.0.0.1:8001")
    
    mcp_tools = None # This might still be used by the Team or Manager directly
    try:
        print(f" [Team] Initializing MCPTools with URL: {mcp_server_url_val} using SSE transport...")
        mcp_tools = MCPTools(transport="sse", url=mcp_server_url_val) 
        print("[Team] MCPTools Initialized.")

        # Log discovered tools from MCPTools instance
        try:
            # Assuming 'openai' model_type as OpenAILike is used by agents.
            # This method should return tool schemas formatted for the specified model type.
            tool_schemas = mcp_tools.get_tools_for_model(model_type="openai") 
            if tool_schemas:
                discovered_tool_names = [schema.get('function', {}).get('name', 'UnknownTool') for schema in tool_schemas]
                if not discovered_tool_names and isinstance(tool_schemas, list):
                    # This case means get_tools_for_model returned an empty list of schemas
                    print("[Team] MCPTools get_tools_for_model('openai') returned an empty list. No tools were formatted or available.")
                else:
                    print(f"[Team] MCPTools successfully fetched and formatted tool schemas for 'openai' model. Tool names: {discovered_tool_names}")
            else:
                # This case means get_tools_for_model returned None or something else falsy (e.g. not a list)
                print("[Team] MCPTools get_tools_for_model('openai') returned None or non-list. No tools discovered or formatted.")
        except AttributeError:
            print("[Team] MCPTools instance does not have 'get_tools_for_model' method as expected, or it failed. Cannot list tools.")
        except Exception as tool_log_exc:
            print(f"[Team] Error while trying to list tools from MCPTools: {tool_log_exc}")

    except Exception as e:
        print(f"[Team] WARNING: Could not initialize MCPTools in get_turath_research_team. If the Team or Manager agent uses MCPTools directly, they might fail. Error: {e}")
        mcp_tools = None

    # Pass mcp_tools instance to the manager agent if it was initialized
    manager_agent_tools = [mcp_tools] if mcp_tools else []
    manager_agent = get_turath_team_manager_agent_instance(tools=manager_agent_tools)
    
    # TurathQueryAgent now needs mcp_tools_instance to get its tools
    turath_query_member_agent = get_turath_query_agent_instance(mcp_tools_instance=mcp_tools)
    if hasattr(turath_query_member_agent, 'initialize') and callable(getattr(turath_query_member_agent, 'initialize')):
        print(f"Initializing member agent: {turath_query_member_agent.name}...")
        await turath_query_member_agent.initialize()
        print(f"Member agent {turath_query_member_agent.name} initialized.")
    else:
        print(f"Member agent {turath_query_member_agent.name} does not have an initialize method.")

    # Explicitly configure the model for the Team
    team_llm = OpenAILike(
        id=settings.default_model_id,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )

    turath_research_team = Team(
        name="Turath Research Team",
        members=[manager_agent, turath_query_member_agent],
        instructions=[
            "This team specializes in researching Islamic heritage (Turath) texts.",
            "The TurathQueryAgent is the primary expert for finding and detailing specific texts.",
            "The TurathTeamManagerAgent coordinates and delegates tasks."
        ],
        model=team_llm # Pass the explicitly configured model
    )
    return turath_research_team
