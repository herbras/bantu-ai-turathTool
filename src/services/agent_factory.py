import logging
from typing import List, Optional
from agno.tools.mcp import MCPTools
from ..tools.tavily_service import TurathTavilyTools
from ..tools.scientific_service import TurathScientificTools
from ..agents.turath_query import create_turath_query_agent
from ..agents.turath_writer import create_turath_writer_agent
from ..agents.fact_checker import create_fact_checker_agent
from ..teams.turath_editor import create_turath_editor_team


class AgentService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agents = {}
        self.teams = {}
        self.tavily_tools: Optional[TurathTavilyTools] = None
        self.scientific_tools: Optional[TurathScientificTools] = None

    def initialize_tavily_tools(
        self, api_key: Optional[str] = None
    ) -> TurathTavilyTools:
        """Initialize TavilyTools for web search"""
        try:
            self.tavily_tools = TurathTavilyTools(
                api_key=api_key,
                search=True,
                max_tokens=6000,
                include_answer=True,
                search_depth="advanced",
                format="markdown",
            )
            self.logger.info("TavilyTools initialized successfully")
            return self.tavily_tools
        except Exception as e:
            self.logger.warning(f"Failed to initialize TavilyTools: {e}")
            return None

    def initialize_scientific_tools(
        self, email: str = "research@turath.ai"
    ) -> TurathScientificTools:
        """Initialize Scientific Tools for ArXiv and PubMed search"""
        try:
            self.scientific_tools = TurathScientificTools(
                email=email, max_results=5, include_arxiv=True, include_pubmed=True
            )
            self.logger.info("Scientific Tools (ArXiv/PubMed) initialized successfully")
            return self.scientific_tools
        except Exception as e:
            self.logger.warning(f"Failed to initialize Scientific Tools: {e}")
            return None

    async def initialize_agents(
        self,
        mcp_tools: MCPTools,
        tavily_api_key: Optional[str] = None,
        enable_scientific_search: bool = True,
    ):
        """Initialize all agents and teams"""
        try:
            # Initialize TavilyTools if API key is provided
            tavily_tools = None
            if tavily_api_key:
                tavily_tools = self.initialize_tavily_tools(tavily_api_key)

            # Initialize Scientific Tools if enabled
            scientific_tools = None
            if enable_scientific_search:
                scientific_tools = self.initialize_scientific_tools()

            # Create agents with MCP, Tavily, and Scientific tools
            self.logger.info(
                "Creating agents with MCPTools, TavilyTools, and Scientific Tools..."
            )
            turath_query_agent = create_turath_query_agent(
                mcp_tools_instance=mcp_tools,
                tavily_tools_instance=tavily_tools,
                scientific_tools_instance=scientific_tools,
            )
            await turath_query_agent.initialize()

            # TurathWriterAgent and FactCheckerAgent also get MCPTools
            turath_writer_agent = create_turath_writer_agent(mcp_tools)
            fact_checker_agent = create_fact_checker_agent(mcp_tools)

            # Store agents
            self.agents = {
                "turath_query": turath_query_agent,
                "turath_writer": turath_writer_agent,
                "fact_checker": fact_checker_agent,
            }

            # Create teams
            turath_editor_team = create_turath_editor_team(
                turath_query_agent, turath_writer_agent, fact_checker_agent
            )

            self.teams = {"turath_editor": turath_editor_team}

            self.logger.info("All agents and teams initialized successfully")
            return self.agents, self.teams

        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise

    def get_agent(self, name: str):
        return self.agents.get(name)

    def get_team(self, name: str):
        return self.teams.get(name)

    def get_all_agents(self) -> List:
        return list(self.agents.values())

    def get_all_teams(self) -> List:
        return list(self.teams.values())
