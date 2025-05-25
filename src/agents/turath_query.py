from typing import List, Any
from agno.agent import Agent
from agno.models.openai.like import OpenAILike 
from agno.storage.sqlite import SqliteStorage 
from ..config import settings # For settings like API keys, DB paths

# Default instructions for the TurathQueryAgent
DEFAULT_TURATH_QUERY_INSTRUCTIONS = [
    "You are a CURIOUS Islamic researcher. ALWAYS research using tools before answering.",
    "RULE: NO assumptions. Use tools: Islamic database (MCP), web search (Tavily), scientific literature.",
    "PROCESS: 1) Plan research, 2) Execute with tools, 3) Synthesize findings.",
    "PRINCIPLE: 'I don't know until I investigate' - verify everything through research.",
    
    "## RESEARCH METHODOLOGY:",
    "ASK: What don't I know? Question everything, verify through sources.",
    "INVESTIGATE: Definitions, primary sources, scholar opinions, practical applications.",
    
    "## RESEARCH PHASES:",
    "1. IDENTIFY key terms to investigate",
    "2. SEARCH definitions: تعريف، مفهوم + [topic]", 
    "3. FIND evidence: قرآن، حديث، فقه + [topic]",
    "4. CHECK scholarly opinions across madhabs",
    "5. SYNTHESIZE findings honestly",
    
    "## VERIFICATION:",
    "✅ Used search_library for definitions and evidence?",
    "✅ Cited specific sources for all claims?", 
    "✅ Checked both classical and contemporary sources?",
    
    "## SEARCH PATTERNS:",
    "Definitions: تعريف، مفهوم + [topic]",
    "Evidence: قرآن، حديث، صحيح + [topic]", 
    "Madhabs: حنفي، شافعي، مالكي، حنبلي + [topic]",
    "Rulings: حكم، حلال، حرام + [topic]",
    
    "## RESPONSE FORMAT:",
    "Structure: Islamic Database Results, Scientific Literature, Additional Web Sources",
    "Language: Bahasa Indonesia (unless query in other language)",
    "Citation: Include exact source references from tool results",
]

class TurathQueryAgent(Agent): # Corrected: Only inherits from Agent
    def __init__(
        self,
        name: str = "TurathQueryAgent",
        model: Any = None,
        instructions: List[str] = None,
        storage: Any = None,
        tools: List[Any] = None, 
        **kwargs
    ):
        _model = model or OpenAILike(
            id=settings.default_model_id,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
        _storage = storage or SqliteStorage(
            table_name=kwargs.pop("table_name", "turath_query_agent"),
            db_file=settings.agent_storage_db
        )
        _instructions = instructions or DEFAULT_TURATH_QUERY_INSTRUCTIONS
        _tools = tools or [] 

        super().__init__(
            name=name,
            model=_model,
            instructions=_instructions,
            storage=_storage,
            tools=_tools, 
            add_datetime_to_instructions=kwargs.pop("add_datetime_to_instructions", True),
            add_history_to_messages=kwargs.pop("add_history_to_messages", True),
            num_history_responses=kwargs.pop("num_history_responses", settings.num_history_responses),
            markdown=kwargs.pop("markdown", True),
            reasoning=kwargs.pop("reasoning", False),  # Temporarily disable reasoning due to provider conflicts
            show_tool_calls=kwargs.pop("show_tool_calls", True),
            **kwargs
        )
        
        import logging
        self.logger = logging.getLogger(name) 

        self.tool_performance_cache = {} 

    async def initialize(self):
        """Initializes the agent."""
        self.logger.info(f"Initializing {self.name}...")
        self.logger.info(f"{self.name} initialized with {len(self.tools)} static tools: {[tool.name if hasattr(tool, 'name') else tool.__class__.__name__ for tool in self.tools]}")

    async def handle_query(self, query: str, **kwargs):
        result = await super().arun(query, **kwargs)

        tool_failure = self._check_tool_failure(result)
        poor_performance = self._evaluate_performance(result, query)

        if tool_failure:
            print(f"Tool failure detected for query: {query}")
        if poor_performance:
            print(f"Poor performance detected for query: {query}")

        return result

    def _check_tool_failure(self, result) -> bool:
        if isinstance(result, dict) and result.get('action_status') == 'tool_failure':
            return True
        return False

    def _evaluate_performance(self, result, query) -> bool:
        return False


def create_turath_query_agent(mcp_tools_instance=None, tavily_tools_instance=None, scientific_tools_instance=None) -> TurathQueryAgent:
    """
    Factory function to create a TurathQueryAgent instance.
    mcp_tools_instance should be an MCPTools object.
    tavily_tools_instance should be a TurathTavilyTools object for web search.
    scientific_tools_instance should be a TurathScientificTools object for scientific literature.
    """
    agent_tools = []
    
    # Add MCP tools for internal Islamic database
    if mcp_tools_instance:
        mcp_tools_instance.include_tools = [
            'get_filter_ids', 
            'search_library', 
            'list_all_categories',
            'get_book_details'
        ]
        agent_tools.append(mcp_tools_instance)
    
    # Add Tavily tools for web search
    if tavily_tools_instance:
        agent_tools.append(tavily_tools_instance)
    
    # Add Scientific tools for medical/technology research
    if scientific_tools_instance:
        agent_tools.append(scientific_tools_instance)
    
    agent = TurathQueryAgent(
        tools=agent_tools,
        # Enable Agno Reasoning Agents for systematic research
        reasoning=False,  # Disable until we fix provider compatibility
        # Add debug settings to see what tools are actually available
        show_tool_calls=True,
        debug_mode=True
    )
    return agent
