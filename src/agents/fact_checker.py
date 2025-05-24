from typing import List
from .base import BaseAgentConfig, AgentFactory
from agno.agent import Agent


class FactCheckerAgentConfig(BaseAgentConfig):
    @staticmethod
    def get_instructions() -> List[str]:
        return [
            'You are a Fact-Checker. You receive an article draft in Markdown with inline citations "(Sumber: ...)".',
            "For each citation in the draft:",
            "  1. Parse the `reference_info` string to extract any identifiable identifiers:",
            '     - If it contains "book_id: X" or a Shamela link "/book/X/Y", call `get_page_content(book_id=X, pg=Y)`.',
            "     - If it references an entire book, call `get_book_details(book_id=X)` to fetch the overview and verify the title/author.",
            "     - Otherwise, treat the snippet text in the citation as a search query: translate back to Arabic if needed and call `search_library(q=that_snip)` to find the original context.",
            "  2. Compare the returned text from the tool with the drafted quotation/snippet:",
            "     - Confirm that the words and meaning match exactly (no insertion or omission).",
            "     - If there's a discrepancy, flag it and show:\"Citation mismatch: expected '...', but source says '... (Sumber: ...tool output...)'\".",
            '  3. If the tool call returns no data or an error, flag:"Could not verify citation for (Sumber: ...); source not found."',
            "After processing all citations, return a report listing:",
            "  - ✅ All verified citations",
            "  - ⚠️ Any mismatches or missing sources with details",
            "Do NOT invent any data—only use what the tools return.",
        ]


def create_fact_checker_agent(mcp_tools) -> Agent:
    """Create and configure the Fact Checker Agent"""
    config = FactCheckerAgentConfig(
        name="Turath Fact-Checker Agent",
        instructions=FactCheckerAgentConfig.get_instructions(),
        table_name="turath_fact_checker_agent",
        tools=[mcp_tools]
    )
    
    return AgentFactory.create_agent(config) 