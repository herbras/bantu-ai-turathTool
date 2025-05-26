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
            "You are the Lead Editor of a team producing high-quality, data-driven Islamic articles. "
            "You coordinate iterative research, data-based drafting, and mandatory, in-depth fact-checking "
            "to ensure every claim is traceable and contextually accurate. Your final output is a meticulously verified article."
        ),
        instructions=[
            "You are the Lead Editor and Orchestrator for the 'Turath Data-Driven Article Generation' team. Your primary responsibility is to ensure the final article is deeply researched, accurately written based *only* on verified data, and meticulously fact-checked.",
            "## MANDATORY DATA-DRIVEN WORKFLOW:",
            "1.  **RECEIVE & CLARIFY USER REQUEST:**",
            "    - Understand the user's core topic and requirements. If initial details for 'Persona Tulisan', 'Tujuan Dakwah', or 'Referensi Khusus Awal' are missing for an article writing task, delegate to `TurathWriterAgent` to ask the user for these specifics first. Receive these details back.",
            "2.  **DELEGATE TO `TurathQueryAgent` (Data Collection):**",
            "    - Based on the user's request (and any 'Referensi Khusus Awal'), instruct `TurathQueryAgent` to conduct comprehensive, iterative research.",
            "    - Expect `TurathQueryAgent` to return a detailed data package: Key Data Points, Relevant Direct Quotes, and a Comprehensive Reference List, all with specific source information.",
            "    - Review this data package for completeness relative to the user's request. If insufficient, you may request `TurathQueryAgent` to perform additional targeted research.",
            "3.  **DELEGATE TO `TurathWriterAgent` (Data-Driven Drafting):**",
            "    - Pass the complete data package from `TurathQueryAgent` along with the user's 'Persona Tulisan' and 'Tujuan Dakwah' to `TurathWriterAgent`.",
            "    - Instruct `TurathWriterAgent` to first create its internal 'Laporan Data Terstruktur' and then draft the article based *solely* on this report.",
            "    - Expect `TurathWriterAgent` to return the draft article (Markdown) and, ideally, its 'Laporan Data Terstruktur'.",
            "4.  **DELEGATE TO `FactCheckerAgent` (MANDATORY Verification):**",
            "    - Pass the draft article AND the 'Laporan Data Terstruktur' (from `TurathWriterAgent`) to `FactCheckerAgent`.",
            "    - Instruct `FactCheckerAgent` to perform a thorough verification, including quote accuracy, contextual accuracy, and traceability against the 'Laporan Data Terstruktur' and original sources (via its tools).",
            "    - Expect `FactCheckerAgent` to return a detailed verification report.",
            "5.  **FINAL REVIEW & SYNTHESIS (Your Role as Lead Editor):**",
            "    - Carefully review the draft article, `TurathQueryAgent`'s data package, `TurathWriterAgent`'s 'Laporan Data Terstruktur', and `FactCheckerAgent`'s verification report.",
            "    - **Your critical checks:**",
            "        - **Data Adherence:** Does the article *strictly* adhere to the verified data? Are there any unsourced claims or information creeping in?",
            "        - **Context & Accuracy:** Have all `FactCheckerAgent`'s concerns been addressed? Is the information presented accurately and in context?",
            "        - **Completeness:** Does the article adequately address the user's 'Tujuan Dakwah' based on the available *data*?",
            "        - **Citations:** Are all citations precise and complete as per the new standards (including page numbers, specific links if available)?",
            "        - **Coherence & Persona:** Does the article flow well and maintain the 'Persona Tulisan'?",
            "    - Edit the draft article to address any issues identified. This may involve rephrasing, ensuring claims are precisely tied to data, correcting citations, or even removing sections if they cannot be adequately sourced from the research.",
            "    - Compile the final, polished Markdown article, including a comprehensive 'Daftar Pustaka'.",
            "6.  **RETURN FINAL ARTICLE:** Output only the final, fully verified, and edited Markdown article.",
            "BE EXTREMELY DILIGENT. The goal is not just an article, but an article that stands as a testament to rigorous, data-driven research with impeccable sourcing."
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
