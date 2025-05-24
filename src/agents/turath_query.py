from typing import List
from .base import BaseAgentConfig, AgentFactory
from ..tools.dynamic_discovery import DynamicToolDiscovery
from agno.agent import Agent


class TurathQueryAgentConfig(BaseAgentConfig):
    @staticmethod
    def get_instructions() -> List[str]:
        return [
            "You are an expert on Islamic heritage and texts (Turath). Your primary language for interacting with tools is Arabic.",
            "Your answers MUST be strictly derived from the information provided by the tools. Do NOT add any information or make conclusions not directly supported by the tool's output.",
            "Your main task is to answer user questions by searching the Turath library.",
            "  1. Identify the main search topic and any potential filter criteria (like category names e.g., 'Fiqih', 'Mazhab Syafi'i', 'Aqidah', or author names) from the user's query.",
            "  2. Translate the main search topic into accurate Arabic. This will be the 'q' parameter for 'search_library'.",
            "  3. If filter criteria (category or author names) are identified:",
            "     a. Use the 'get_filter_ids' tool. Pass the identified category name to 'category_name' parameter and/or author name to 'author_name' parameter of the 'get_filter_ids' tool.",
            "     b. The 'get_filter_ids' tool will return a dictionary with 'category_ids' and/or 'author_ids'. These will be comma-separated strings of IDs.",
            "     c. Store these IDs to be used as 'cat' or 'author' parameters for the 'search_library' tool.",
            "  4. Call the 'search_library' tool: ",
            "     a. Use the translated Arabic topic as the 'q' parameter.",
            "     b. If you obtained 'category_ids' from 'get_filter_ids', use that string as the 'cat' parameter.",
            "     c. If you obtained 'author_ids' from 'get_filter_ids', use that string as the 'author' parameter.",
            "     d. Do not pass 'cat' or 'author' parameters if no IDs were found or if no filter criteria were identified.",
            "When processing results from 'search_library':",
            "  a. For each item within the 'data' array that you use to construct your answer, you MUST extract information primarily from its 'text' and/or 'snip' fields.",
            "  b. For every piece of information or summary derived from an item's 'text' or 'snip', you MUST immediately present its corresponding 'reference_info' field **in its entirety, including any provided links**. Format this as: 'Sumber: [full content of the reference_info field from that specific item]'.",
            "  c. If you synthesize information from multiple items for a single point in your answer, you must clearly cite all corresponding 'reference_info' (including links) for each part of the synthesis.",
            "  d. If the tool output includes a 'count' field indicating the total number of results, you may mention this if it'srelevant (e.g., 'Ditemukan X hasil, berikut adalah beberapa di antaranya:').",
            "Use other available tools like 'get_book_details' or 'get_page_content' as needed, always ensuring that conclusions are based on tool output and references are cited if applicable (e.g., from book metadata).",
            "Provide clear, concise, and informative answers.",
            "If providing book details or search results, format them clearly for the user, ensuring each piece of information is followed by its source.",
            "If a search yields no results or an error occurs, inform the user politely and state the query that was attempted (both original and translated, and any filters applied).",
        ]


class DynamicAgent(Agent):
    def __init__(self, *args, mcp_server_url: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_discovery = (
            DynamicToolDiscovery(mcp_server_url) if mcp_server_url else None
        )
        self.default_tools = self.tools.copy()
        self.tool_performance_cache = {}

    async def initialize(self):
        if self.tool_discovery:
            await self.tool_discovery.initialize()

    async def handle_query(self, query: str, **kwargs):
        result = await super().arun(query, **kwargs)

        tool_failure = self._check_tool_failure(result)
        poor_performance = self._evaluate_performance(result, query)

        if tool_failure or poor_performance and self.tool_discovery:
            self.logger.info("Default tools inadequate, searching for better tools...")
            new_tools = await self.tool_discovery.get_relevant_tools(query, self)

            if new_tools:
                original_tools = self.tools
                self.tools = original_tools + new_tools
                enhanced_result = await super().arun(query, **kwargs)
                self._record_tool_performance(new_tools, enhanced_result, query)
                self.tools = original_tools
                self._retain_valuable_tools(new_tools, query)
                return enhanced_result

        return result

    def _check_tool_failure(self, result) -> bool:
        return "tool execution failed" in str(result).lower()

    def _evaluate_performance(self, result, query) -> bool:
        return False  # Placeholder

    def _record_tool_performance(self, tools, result, query):
        for tool in tools:
            tool_name = tool.__class__.__name__
            self.tool_performance_cache[tool_name] = {
                "query_type": self._categorize_query(query),
                "performance_score": 0.8,
                "last_used": "timestamp",
            }

    def _retain_valuable_tools(self, new_tools, query):
        for tool in new_tools:
            tool_name = tool.__class__.__name__
            if tool_name in self.tool_performance_cache:
                if self.tool_performance_cache[tool_name]["performance_score"] > 0.8:
                    if tool not in self.default_tools:
                        self.default_tools.append(tool)
                        self.logger.info(
                            f"Permanently added high-performing tool: {tool_name}"
                        )

    def _categorize_query(self, query) -> str:
        return "general"  # Placeholder


def create_turath_query_agent(mcp_tools_instance) -> DynamicAgent:
    # mcp_tools_instance is the MCPTools object, which has the mcp_server_url attribute
    mcp_url = None
    if hasattr(mcp_tools_instance, 'mcp_server_url') and mcp_tools_instance.mcp_server_url:
        mcp_url = mcp_tools_instance.mcp_server_url
    elif hasattr(mcp_tools_instance, 'url') and mcp_tools_instance.url: # Common alternative attribute name
        mcp_url = mcp_tools_instance.url
    else:
        print("WARNING: MCPTools instance in create_turath_query_agent does not have a readily available mcp_server_url or url attribute. DynamicToolDiscovery might not work.")

    config_kwargs = {}
    if mcp_url:
        config_kwargs['mcp_server_url'] = mcp_url

    config = TurathQueryAgentConfig(
        name="Turath Query Agent",
        instructions=TurathQueryAgentConfig.get_instructions(),
        table_name="turath_query_agent",
        tools=[mcp_tools_instance] if mcp_tools_instance else [], # Pass the MCPTools instance itself as a tool, or an empty list if None
        **config_kwargs
    )

    base_agent = AgentFactory.create_agent(config)

    # DynamicAgent inherits from agno.Agent
    # It uses mcp_server_url for its DynamicToolDiscovery
    dynamic_agent = DynamicAgent(
        name=base_agent.name,
        model=base_agent.model,
        tools=base_agent.tools, # base_agent.tools should now correctly reflect [mcp_tools_instance]
        instructions=base_agent.instructions,
        storage=base_agent.storage,
        mcp_server_url=config.kwargs.get('mcp_server_url'), # This should pick up the mcp_url passed via config_kwargs
        add_datetime_to_instructions=True,
        add_history_to_messages=True,
        num_history_responses=3, # settings.num_history_responses
        markdown=True,
        reasoning=False, # Keep reasoning False for now to avoid previous errors
        show_tool_calls=True,
    )

    return dynamic_agent
