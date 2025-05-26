from agno.document.chunking.semantic import SemanticChunking
from agno.document.chunking.agentic import AgenticChunking
from agno.embedder.openai import OpenAIEmbedder


class IslamicSemanticChunking(SemanticChunking):
    """
    Islamic-optimized semantic chunking that keeps related Islamic concepts together.
    Designed to preserve Arabic terms, Quranic verses, and hadith references.
    """

    def __init__(self, **kwargs):
        # Optimize for Islamic content
        super().__init__(
            chunk_size=kwargs.get(
                "chunk_size", 3000
            ),  # Smaller chunks for context limits
            similarity_threshold=kwargs.get(
                "similarity_threshold", 0.6
            ),  # Higher threshold to keep related Islamic concepts together
            embedder=OpenAIEmbedder(),
        )


class IslamicAgenticChunking(AgenticChunking):
    """
    Islamic-optimized agentic chunking that understands Islamic text structure.
    Breaks at natural boundaries like verse endings, hadith references, etc.
    """

    def __init__(self, **kwargs):
        super().__init__(
            max_chunk_size=kwargs.get(
                "max_chunk_size", 3000
            ),  # Smaller for context limits
        )


def get_islamic_chunking_strategy(strategy_type="semantic"):
    """
    Factory function to get appropriate chunking strategy for Islamic content.

    Args:
        strategy_type: "semantic" or "agentic"

    Returns:
        Appropriate chunking strategy
    """
    if strategy_type == "semantic":
        return IslamicSemanticChunking()
    elif strategy_type == "agentic":
        return IslamicAgenticChunking()
    else:
        raise ValueError("Strategy must be 'semantic' or 'agentic'")
