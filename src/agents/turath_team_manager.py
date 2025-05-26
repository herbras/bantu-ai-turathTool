from typing import List, Any
from agno.agent import Agent
from agno.models.openai.like import OpenAILike  # For model
from agno.storage.sqlite import SqliteStorage  # For storage
from ..config import settings  # For settings like API keys, DB paths

DEFAULT_TURATH_TEAM_MANAGER_INSTRUCTIONS = [
    "You are the manager of a research team focused on Islamic heritage (Turath).",
    "Your role is to coordinate tasks among team members and ensure high-quality responses.",
    "For now, your primary member is the TurathQueryAgent.",
    "Delegate queries about Turath texts directly to the TurathQueryAgent.",
]


class TurathTeamManagerAgent(Agent):
    def __init__(
        self,
        name: str = "TurathTeamManagerAgent",
        model: Any = None,  # Allow passing a model, or create a default
        instructions: List[str] = None,
        storage: Any = None,  # Allow passing storage, or create a default
        tools: List[Any] = None,
        **kwargs,
    ):
        _model = model or OpenAILike(
            id=settings.default_model_id,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
        # Pop table_name from kwargs for storage, or use a default. Ensure db_file is from settings.
        _storage = storage or SqliteStorage(
            table_name=kwargs.pop("table_name", "turath_team_manager_agent"),
            db_file=settings.agent_storage_db,
        )
        _instructions = instructions or DEFAULT_TURATH_TEAM_MANAGER_INSTRUCTIONS
        _tools = tools or []

        super().__init__(
            name=name,
            model=_model,
            instructions=_instructions,
            storage=_storage,
            tools=_tools,
            add_datetime_to_instructions=kwargs.pop(
                "add_datetime_to_instructions", True
            ),
            add_history_to_messages=kwargs.pop("add_history_to_messages", True),
            num_history_responses=kwargs.pop(
                "num_history_responses", settings.num_history_responses
            ),
            markdown=kwargs.pop("markdown", True),
            reasoning=kwargs.pop("reasoning", True),
            show_tool_calls=kwargs.pop("show_tool_calls", True),
            **kwargs,  # Pass any remaining kwargs
        )
