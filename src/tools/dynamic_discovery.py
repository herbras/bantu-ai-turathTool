import logging
from typing import Dict, List, Any
from agno.agent import Agent
from agno.tools.mcp import MCPTools


class DynamicToolDiscovery:
    def __init__(self, mcp_server_url: str):
        self.mcp_server_url = mcp_server_url
        self.available_tools: Dict[str, Dict[str, Any]] = {}  # Stores tool metadata
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> Dict[str, Dict[str, Any]]:
        """
        Discovers available tools from the MCP server and stores their metadata.
        Returns a dictionary of available tool metadata.
        """
        self.logger.info(f"Attempting to initialize dynamic tool discovery from {self.mcp_server_url}")
        try:
            # Ensure MCPTools is used as an async context manager
            async with MCPTools(transport="sse", url=self.mcp_server_url) as mcp_tools:
                self.available_tools = await mcp_tools.list_available_tools()
                self.logger.info(
                    f"Discovered {len(self.available_tools)} tools from MCP server: {list(self.available_tools.keys())}"
                )
                return self.available_tools
        except Exception as e:
            self.logger.error(f"Failed to initialize dynamic tool discovery (list_available_tools): {e}", exc_info=True)
            self.available_tools = {}  # Ensure it's empty on failure
            return {}

    async def get_all_tool_instances(self) -> List[Any]:
        """
        Gets instances of all tools discovered by the initialize() method.
        Assumes initialize() has been called and self.available_tools is populated.
        """
        tool_instances: List[Any] = []
        if not self.available_tools:
            self.logger.warning(
                "No available tools found in self.available_tools. Ensure initialize() was called successfully before get_all_tool_instances()."
            )
            return []

        self.logger.info(f"Attempting to instantiate {len(self.available_tools)} discovered tools: {list(self.available_tools.keys())}")
        try:
            async with MCPTools(transport="sse", url=self.mcp_server_url) as mcp_tools:
                for tool_name in self.available_tools.keys():
                    try:
                        tool_instance = await mcp_tools.get_tool(tool_name)
                        if tool_instance:
                            tool_instances.append(tool_instance)
                            self.logger.info(f"Successfully instantiated tool: {tool_name}")
                        else:
                            self.logger.warning(f"Could not get instance for tool: {tool_name} (get_tool returned None)")
                    except Exception as e_tool:
                        self.logger.error(f"Error instantiating tool {tool_name}: {e_tool}", exc_info=True)
            self.logger.info(f"Successfully instantiated {len(tool_instances)} tools.")
            return tool_instances
        except Exception as e:
            self.logger.error(f"Failed to get all tool instances during MCPTools context management: {e}", exc_info=True)
            return []

    async def get_relevant_tools(self, user_query: str, agent: Agent) -> List[Any]:
        """
        Finds tools relevant to a user query and returns new tool instances.
        """
        self.logger.info(f"Searching for relevant tools for query: '{user_query}'")
        try:
            current_tool_names = {tool.__class__.__name__ for tool in agent.tools} # Assuming agent.tools stores instances

            async with MCPTools(transport="sse", url=self.mcp_server_url) as mcp_tools:
                # The semantic_tool_search might directly hit the server.
                # If it relies on a local cache that initialize() populates, ensure initialize() is called.
                # if not self.available_tools: # Optional: ensure metadata is loaded if semantic_tool_search relies on it
                #     await self.initialize()
                
                relevant_tools_info = await mcp_tools.semantic_tool_search(
                    query=user_query, max_results=5, min_relevance_score=0.7
                )
                self.logger.info(f"Semantic search found {len(relevant_tools_info)} potentially relevant tools.")

                new_tools = []
                for tool_info in relevant_tools_info: # Assuming relevant_tools_info is a list of dicts with 'name'
                    tool_name = tool_info.get("name")
                    if not tool_name:
                        self.logger.warning(f"Tool info missing 'name': {tool_info}")
                        continue

                    if tool_name not in current_tool_names:
                        try:
                            tool_instance = await mcp_tools.get_tool(tool_name)
                            if tool_instance:
                                new_tools.append(tool_instance)
                                self.logger.info(f"Dynamically added relevant tool: {tool_name}")
                            else:
                                self.logger.warning(f"Could not get instance for relevant tool: {tool_name} (get_tool returned None)")
                        except Exception as e_tool:
                            self.logger.error(f"Error instantiating relevant tool {tool_name}: {e_tool}", exc_info=True)
                    else:
                        self.logger.info(f"Tool {tool_name} is already part of the agent's tools.")
                return new_tools
        except Exception as e:
            self.logger.error(f"Error finding relevant tools: {e}", exc_info=True)
            return []