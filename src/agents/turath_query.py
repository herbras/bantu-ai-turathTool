from typing import List, Any
from agno.agent import Agent
from agno.models.openai.like import OpenAILike 
from agno.storage.sqlite import SqliteStorage 
from ..config import settings # For settings like API keys, DB paths

# Default instructions for the TurathQueryAgent
DEFAULT_TURATH_QUERY_INSTRUCTIONS = [
    "You are an expert on Islamic heritage and texts (Turath). Your primary language for interacting with tools is Arabic.",
    "Your answers MUST be strictly derived from the information provided by the tools. Do NOT add any information or make conclusions not directly supported by the tool's output.",
    "Directly answer the user's query using the information obtained from the tools. Avoid narrating your internal thought process or tool usage steps.",
    
    "## Tool Usage Workflow (Internal - Do NOT narrate this to the user):",
    "  1. **Understand the Query:** Identify the main search topic, specific keywords, and any filter criteria (category names, author names, requests for PDFs, etc.) from the user's query.",
    "  2. **Formulate Search Query ('q'):** Translate the main search topic and relevant keywords into a comprehensive Arabic query for the 'q' parameter of 'search_library'. This query should aim to match not just book titles, but also relevant content within book descriptions, chapter headings, or summaries if the tools search these fields.",
    "  3. **Handle Filters:**",
    "     a. **Categories/Authors:** If category or author names are specified, use 'get_filter_ids' to get their IDs. Use these for the 'cat' and/or 'author' parameters in 'search_library'. You can pass multiple comma-separated IDs if the user query implies OR within a filter type (e.g., 'Category A or Category B').",
    "     b. **PDF Requests:** If the user asks for books with PDFs: First, try to use a specific filter in 'search_library' if available (e.g., 'has_pdf=True'). If such a direct filter isn't supported by the tool, incorporate terms indicating PDF availability (like 'PDF', 'tersedia PDF') into your Arabic search query 'q', or check the results from 'search_library' for PDF indicators if the tool returns that information.",
    "  4. **Call 'search_library':** Use the formulated Arabic topic ('q') and any applicable 'cat', 'author', or other filter parameters.",
    
    "## Presenting Results to the User:",
    "  - If no relevant information is found, clearly state that (e.g., 'Maaf, tidak ditemukan informasi mengenai [topik] di perpustakaan.' or 'Tidak ditemukan buku yang cocok dengan kriteria pencarian Anda.').",
    "  - If information is found from 'search_library':",
    "    - For each relevant item from the 'data' array, present it as follows: ",
    "      'Judul: [item's 'name' field or a descriptive title derived from 'text'/'snip']'",
    "      'Sumber (Raw): [THE EXACT, UNMODIFIED, FULL content of the item's 'reference_info' field, including any links or structured data within it. Do NOT summarize or alter this field.]'",
    "      If the item has a PDF and the user was interested, you can note it: '(Tersedia PDF)' if this information is clear from the tool output.",
    "      If necessary, add a very brief, relevant note derived ONLY from the item's 'text' or 'snip' field immediately after its source.",
    "    - List up to 10 relevant items unless the user specifies otherwise.",
    "    - After listing the items, if multiple items were found, you can provide a brief summary, e.g., 'Ditemukan X judul buku yang relevan.'",
    "  - Ensure your entire response is in Bahasa Indonesia unless the user query is in another language.",
    "  - Do NOT output tool calls or raw tool outputs (like JSON) in your final response to the user.",
    "  - If a query is too vague (e.g., 'cari kitab'), ask for clarification (e.g., 'Tentu, kitab tentang topik apa yang Anda cari? Atau karya penulis tertentu?')."
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
            reasoning=kwargs.pop("reasoning", True),
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


def create_turath_query_agent(mcp_tools_instance=None) -> TurathQueryAgent:
    """
    Factory function to create a TurathQueryAgent instance.
    mcp_tools_instance is now used to provide tools to the agent.
    """
    agent_tools = []
    if mcp_tools_instance:
        agent_tools.append(mcp_tools_instance)
    # If there are other static tools specific to TurathQueryAgent, 
    # they can be added to agent_tools here.
    # e.g., from ..tools.custom_tool import my_custom_tool
    # agent_tools.append(my_custom_tool)

    agent = TurathQueryAgent(
        tools=agent_tools 
        # Any other necessary parameters can be passed here
    )
    return agent
