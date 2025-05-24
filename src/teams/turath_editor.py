import logging
import types
from agno.team import Team
from agno.models.openai.like import OpenAILike
from ..config import settings


def create_turath_editor_team(
    turath_query_agent, turath_writer_agent, fact_checker_agent
) -> Team:
    """Create and configure the Turath Editor Team"""

    team = Team(
        name="Turath Content Coordinator",
        mode="coordinate",
        model=OpenAILike(
            id=settings.default_model_id,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        ),
        members=[
            turath_query_agent,
            turath_writer_agent,
            fact_checker_agent,
        ],
        description=(
            "You are the Team Leader coordinating the production of high-quality Islamic articles. "
            "First break down the user's request into search, drafting, and fact-checking tasks. "
            "Then synthesize all member outputs into one coherent, fully-sourced final article."
        ),
        instructions=[
            "1. Terima permintaan user. Tentukan apakah ini soal pencarian atau penulisan artikel.",
            "2. Jika butuh referensi, delegasikan ke Turath Query Agent untuk `search_library` dan `get_filter_ids`.",
            "3. Terima hasil pencarian, terus berikan ke Turath Article Writer Agent untuk menghasilkan draf artikel.",
            "4. (Opsional) Berikan draf tersebut ke Turath Fact-Checker Agent untuk verifikasi sitasi.",
            "5. Ambil semua output, edit dan satukan menjadi satu artikel final Markdown:",
            "   - Pastikan setiap klaim memiliki sitasi 'Sumber: ...' sesuai `reference_info`.",
            "   - Periksa konsistensi persona dan tujuan dakwah.",
            "   - Tampilkan 'Daftar Pustaka' unik di akhir.",
            "Return only the final synthesized article.",
        ],
        add_datetime_to_instructions=True,
        enable_agentic_context=True,
        share_member_interactions=True,
        show_members_responses=True,
        markdown=True,
    )

    # Patch initialize_agent method for Team compatibility
    _patch_team_initialization(team)

    return team


def _patch_team_initialization(team):
    """Patch the team to ensure compatibility with the Agent interface"""
    logger = logging.getLogger(__name__)

    if hasattr(team, "initialize_team") and not hasattr(team, "initialize_agent"):
        logger.info(
            f"Patching '{team.name}' instance: setting 'initialize_agent' to call 'initialize_team'."
        )

        def initialize_agent_for_team(self_instance, *args, **kwargs):
            return self_instance.initialize_team(*args, **kwargs)

        team.initialize_agent = types.MethodType(initialize_agent_for_team, team)

    elif not hasattr(team, "initialize_agent"):
        logger.warning(
            f"Patching '{team.name}' instance: 'initialize_team' not found. Adding a no-op 'initialize_agent'."
        )

        def no_op_initialize_agent_method(self_instance, *args, **kwargs):
            logger.info(f"No-op initialize_agent called on {self_instance.name}")

        team.initialize_agent = types.MethodType(no_op_initialize_agent_method, team)
