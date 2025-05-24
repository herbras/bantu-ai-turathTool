import logging
from typing import List
from agno.tools.mcp import MCPTools
from ..agents.turath_query import create_turath_query_agent
from ..agents.turath_writer import create_turath_writer_agent
from ..agents.fact_checker import create_fact_checker_agent
from ..teams.turath_editor import create_turath_editor_team


class AgentService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agents = {}
        self.teams = {}

    async def initialize_agents(self, mcp_tools: MCPTools):
        """Initialize all agents and teams"""
        try:
            # Create agents
            # TurathQueryAgent no longer uses mcp_tools for dynamic discovery
            turath_query_agent = create_turath_query_agent(mcp_tools_instance=None) 
            await turath_query_agent.initialize()

            # TurathWriterAgent and FactCheckerAgent might use mcp_tools directly or for other config
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
