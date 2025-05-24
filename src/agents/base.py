from typing import List, Any, Optional
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from agno.storage.sqlite import SqliteStorage
from ..config import settings


class BaseAgentConfig:
    def __init__(
        self,
        name: str,
        instructions: List[str],
        table_name: str,
        tools: Optional[List[Any]] = None,
        **kwargs,
    ):
        self.name = name
        self.instructions = instructions
        self.table_name = table_name
        self.tools = tools or []
        self.kwargs = kwargs


class AgentFactory:
    @staticmethod
    def create_agent(config: BaseAgentConfig) -> Agent:
        model = OpenAILike(
            id=settings.default_model_id,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )

        storage = SqliteStorage(
            table_name=config.table_name, db_file=settings.agent_storage_db
        )

        return Agent(
            name=config.name,
            model=model,
            tools=config.tools,
            instructions=config.instructions,
            storage=storage,
            add_datetime_to_instructions=True,
            add_history_to_messages=True,
            num_history_responses=settings.num_history_responses,
            markdown=True,
            reasoning=True,
            show_tool_calls=True,
            **config.kwargs,
        )
