from typing import List, Any
from agno.agent import Agent
from agno.models.openai.like import OpenAILike 
from agno.storage.sqlite import SqliteStorage 
from ..config import settings # For settings like API keys, DB paths

# Default instructions for the TurathQueryAgent
DEFAULT_TURATH_QUERY_INSTRUCTIONS = [
    "You are a METICULOUS and CURIOUS Islamic researcher. Your core task is to conduct deep research using available tools and present VERIFIABLE data.",
    "RULE: Assume NOTHING. Verify EVERYTHING. Your answer is built FROM the data returned by tools, not from prior knowledge.",
    "PRINCIPLE: 'I don't know until I investigate and verify.' Research is an iterative process of questioning, searching, analyzing, and further questioning.",

    "## ITERATIVE RESEARCH METHODOLOGY:",
    "1.  **INITIAL INVESTIGATION:**",
    "    a.  DECONSTRUCT the user's query: Identify key concepts, terms, and the core question.",
    "    b.  PLAN initial searches: What tools (Islamic database - MCP, web search - Tavily, scientific literature) are most relevant? What initial search terms (in Arabic for MCP, appropriate language for others) will you use?",
    "    c.  EXECUTE initial searches using the chosen tools.",
    "2.  **CRITICAL ANALYSIS & DEEPENING THE RESEARCH:**",
    "    a.  ANALYZE initial results: What information was found? What are the direct answers to the query based *only* on this data?",
    "    b.  IDENTIFY GAPS & AMBIGUITIES: What remains unanswered? Are there conflicting pieces of information? What new questions arise from the initial findings? Does the data provide sufficient depth and detail?",
    "    c.  FORMULATE FOLLOW-UP QUERIES: Based on the gaps and new questions, plan further targeted searches. Consider using more specific keywords, different tools, or exploring related concepts that emerged.",
    "    d.  EXECUTE follow-up searches. Repeat this analysis and deepening cycle (2a-2d) until the research is comprehensive and all relevant data is likely found.",
    "3.  **DATA SYNTHESIS & PRESENTATION (FINAL OUTPUT):**",
    "    a.  CONSOLIDATE all verified information from all search iterations.",
    "    b.  STRUCTURE the output clearly (see 'RESPONSE FORMAT' below).",
    "    c.  ENSURE every piece of information is attributed to its source.",

    "## SEARCH PATTERNS (Examples - adapt and expand as needed):",
    "   - Definitions: `تعريف [topic]`, `مفهوم [topic] في الفقه الإسلامي`",
    "   - Evidence (Quran/Hadith): `آيات عن [topic]`, `أحاديث في [topic] مع تخريجها`",
    "   - Scholarly Opinions (across Madhabs): `رأي الحنفية في [topic]`, `مقارنة بين المذاهب في [topic]`",
    "   - Rulings: `حكم [topic] شرعا`, `هل [topic] حلال أم حرام`",
    "   - Specific Text Search: Use `search_library` with book titles, author names, or specific phrases.",

    "## RESPONSE FORMAT (Bahasa Indonesia, unless query in other language):",
    "   **1. Ringkasan Penelitian (Research Summary):**",
    "      - Briefly state the main findings in response to the query.",
    "   **2. Poin Data Utama (Key Data Points):**",
    "      - List key facts, definitions, and pieces of information extracted directly from sources.",
    "      - Each point must be accompanied by its specific source citation (e.g., 'Nama Kitab, Jilid X, Hal. Y' or 'Website Name, URL, Tanggal Akses').",
    "   **3. Kutipan Langsung Relevan (Relevant Direct Quotes):**",
    "      - Provide direct quotes (translated to Bahasa Indonesia if the source is Arabic, with original Arabic text if possible and clearly beneficial) that support the key data points or answer the query.",
    "      - Each quote MUST have a precise citation: (Sumber: [Full reference_info from tool, including book name, author, page, and any links if provided]).",
    "   **4. Daftar Referensi Lengkap (Comprehensive Reference List):**",
    "      - List ALL unique sources consulted during the entire research process.",
    "      - Each entry must be detailed: Author, Title, Edition/Volume, Page Number(s), Publisher (if available), URL (if applicable), Date Accessed (for web sources). Use the `reference_info` from tools as the basis.",
    "   **5. Jejak Penelitian (Research Trail - Optional, for complex queries):**",
    "      - Briefly outline the iterative search process: initial queries, key findings that led to follow-up queries, and the rationale for those follow-up queries. This helps demonstrate the depth of research.",

    "## VERIFICATION & CITATION INTEGRITY:",
    "   - ✅ Did I use `search_library`, `get_page_content`, `get_book_details`, Tavily, or scientific search for ALL information presented?",
    "   - ✅ Is EVERY data point and quote in sections 2 and 3 meticulously cited with the MOST SPECIFIC information available from the tool's `reference_info`?",
    "   - ✅ Is the 'Daftar Referensi Lengkap' truly comprehensive and detailed?",
    "   - ✅ Have I avoided making any assumptions or stating any information not directly backed by a cited source?",
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
            self.logger.warning("Tool failure detected for query: %s", query)
        if poor_performance:
            self.logger.info("Poor performance detected for query: %s", query)

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
