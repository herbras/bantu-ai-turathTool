import logging
from typing import Dict, List, Any
from agno.agent import Agent
from agno.tools.mcp import MCPTools


class DynamicToolDiscovery:
    def __init__(self, mcp_server_url: str):
        self.mcp_server_url = mcp_server_url
        self.available_tools: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> Dict[str, Dict[str, Any]]:
        try:
            async with MCPTools(transport="sse", url=self.mcp_server_url) as mcp_tools:
                self.available_tools = await mcp_tools.list_available_tools()
                self.logger.info(
                    f"Discovered {len(self.available_tools)} tools from MCP server"
                )
                return self.available_tools
        except Exception as e:
            self.logger.error(f"Failed to initialize dynamic tool discovery: {e}")
            return {}

    async def get_relevant_tools(self, user_query: str, agent: Agent) -> List[Any]:
        try:
            current_tool_names = {tool.__class__.__name__ for tool in agent.tools}

            async with MCPTools(transport="sse", url=self.mcp_server_url) as mcp_tools:
                relevant_tools = await mcp_tools.semantic_tool_search(
                    query=user_query, max_results=5, min_relevance_score=0.7
                )

                new_tools = []
                for tool_info in relevant_tools:
                    tool_name = tool_info["name"]
                    if tool_name not in current_tool_names:
                        tool = await mcp_tools.get_tool(tool_name)
                        if tool:
                            new_tools.append(tool)
                            self.logger.info(f"Dynamically added tool: {tool_name}")

                return new_tools
        except Exception as e:
            self.logger.error(f"Error finding relevant tools: {e}")
            return [] 