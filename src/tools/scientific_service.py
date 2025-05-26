import re
from typing import List, Any

from agno.tools import Toolkit
from agno.utils.log import logger

try:
    from agno.tools.arxiv import ArxivTools
    from agno.tools.pubmed import PubmedTools
except ImportError:
    logger.warning(
        "ArxivTools or PubmedTools not available. Install with: pip install arxiv pypdf"
    )
    ArxivTools = None
    PubmedTools = None


class TurathScientificTools(Toolkit):
    """
    Scientific search tools for medical and technology topics in Islamic context.
    Combines ArxivTools and PubmedTools with Islamic perspective.
    """

    def __init__(
        self,
        email: str = "research@turath.ai",
        max_results: int = 5,
        include_arxiv: bool = True,
        include_pubmed: bool = True,
        **kwargs,
    ):
        self.email = email
        self.max_results = max_results

        # Initialize individual tools
        self.arxiv_tools = None
        self.pubmed_tools = None

        tools: List[Any] = []

        if include_arxiv and ArxivTools:
            try:
                self.arxiv_tools = ArxivTools()
                tools.append(self.search_arxiv_with_islamic_context)
            except Exception as e:
                logger.warning(f"Failed to initialize ArxivTools: {e}")

        if include_pubmed and PubmedTools:
            try:
                self.pubmed_tools = PubmedTools(email=email, max_results=max_results)
                tools.append(self.search_pubmed_with_islamic_context)
            except Exception as e:
                logger.warning(f"Failed to initialize PubmedTools: {e}")

        # Add combined search function
        if tools:
            tools.append(self.search_scientific_literature)

        super().__init__(name="turath_scientific_tools", tools=tools, **kwargs)

    def search_arxiv_with_islamic_context(
        self, query: str, max_results: int = 5
    ) -> str:
        """Search ArXiv for technology and scientific papers with Islamic perspective.
        Use this for technology, AI, computer science, physics, mathematics, and other scientific topics
        that might have Islamic ethics or perspective considerations.

        Args:
            query (str): Scientific or technology topic to search for
            max_results (int): Maximum number of results to return. Defaults to 5.

        Returns:
            str: Formatted search results from ArXiv with Islamic context notes.
        """
        if not self.arxiv_tools:
            return "ArXiv search not available. Please install: pip install arxiv pypdf"

        try:
            # Enhance query for broader scientific context
            enhanced_query = f"{query} ethics philosophy"

            # Use the correct ArxivTools method with correct parameter name
            results = self.arxiv_tools.search_arxiv_and_return_articles(
                enhanced_query, num_articles=max_results
            )

            # Add Islamic context note
            context_note = self._add_islamic_scientific_context(query)

            formatted_results = f"# Scientific Literature Search: {query}\n\n"
            formatted_results += f"## Islamic Perspective Note\n{context_note}\n\n"
            formatted_results += f"## ArXiv Results\n{results}\n\n"

            return formatted_results

        except Exception as e:
            logger.error(f"ArXiv search failed: {e}")
            return f"ArXiv search failed: {str(e)}"

    def search_pubmed_with_islamic_context(
        self, query: str, max_results: int = 5
    ) -> str:
        """Search PubMed for medical research with Islamic bioethics considerations.
        Use this for medical, health, bioethics, and healthcare topics that need
        Islamic perspective on medical ethics and bioethics.

        Args:
            query (str): Medical or health topic to search for
            max_results (int): Maximum number of results to return. Defaults to 5.

        Returns:
            str: Formatted search results from PubMed with Islamic bioethics context.
        """
        if not self.pubmed_tools:
            return "PubMed search not available. PubmedTools might not be installed properly."

        try:
            # Search PubMed
            results = self.pubmed_tools.search_pubmed(query, max_results=max_results)

            # Add Islamic bioethics context
            bioethics_note = self._add_islamic_bioethics_context(query)

            formatted_results = f"# Medical Literature Search: {query}\n\n"
            formatted_results += (
                f"## Islamic Bioethics Perspective\n{bioethics_note}\n\n"
            )
            formatted_results += f"## PubMed Results\n{results}\n\n"

            return formatted_results

        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return f"PubMed search failed: {str(e)}"

    def search_scientific_literature(
        self, query: str, search_type: str = "auto"
    ) -> str:
        """Comprehensive scientific literature search with automatic type detection.
        Searches both ArXiv and PubMed based on query content and provides Islamic perspective.

        Args:
            query (str): Scientific topic to search for
            search_type (str): "auto", "medical", "technology", or "both". Defaults to "auto".

        Returns:
            str: Combined search results with Islamic context.
        """
        query_lower = query.lower()

        # Auto-detect search type
        if search_type == "auto":
            medical_keywords = [
                "medical",
                "health",
                "disease",
                "treatment",
                "therapy",
                "clinical",
                "patient",
                "medicine",
                "bioethics",
                "pharmaceutical",
                "genetics",
            ]
            tech_keywords = [
                "technology",
                "ai",
                "artificial intelligence",
                "computer",
                "algorithm",
                "machine learning",
                "physics",
                "mathematics",
                "engineering",
            ]

            is_medical = any(keyword in query_lower for keyword in medical_keywords)
            is_tech = any(keyword in query_lower for keyword in tech_keywords)

            if is_medical and not is_tech:
                search_type = "medical"
            elif is_tech and not is_medical:
                search_type = "technology"
            else:
                search_type = "both"

        results = f"# Comprehensive Scientific Literature Search: {query}\n\n"

        # Search based on detected/specified type
        if search_type in ["medical", "both"] and self.pubmed_tools:
            pubmed_results = self.search_pubmed_with_islamic_context(
                query, self.max_results
            )
            results += pubmed_results + "\n"

        if search_type in ["technology", "both"] and self.arxiv_tools:
            arxiv_results = self.search_arxiv_with_islamic_context(
                query, self.max_results
            )
            results += arxiv_results + "\n"

        # Add general Islamic perspective on science
        results += self._add_general_islamic_science_perspective()

        return results

    def _add_islamic_scientific_context(self, query: str) -> str:
        """Add Islamic perspective on scientific topics"""
        return (
            f"**Islamic Perspective on {query}:**\n"
            "Islam encourages the pursuit of knowledge ('Ilm) in all fields including science and technology. "
            "The Quran states: 'And say: My Lord, increase me in knowledge' (20:114). "
            "Scientific research should be conducted with ethical considerations, seeking benefit for humanity "
            "while avoiding harm. Islamic ethics emphasize the importance of intention (niyyah) and "
            "the responsibility of using knowledge for the betterment of society."
        )

    def _add_islamic_bioethics_context(self, query: str) -> str:
        """Add Islamic bioethics perspective on medical topics"""
        return (
            f"**Islamic Bioethics on {query}:**\n"
            "Islamic bioethics is guided by principles from the Quran and Sunnah, emphasizing the sanctity of life, "
            "the prohibition of harm (la darar wa la dirar), and the concept of maslaha (public interest). "
            "Medical treatments should preserve life, maintain health, and avoid prohibited substances or methods. "
            "Consultation with Islamic scholars (ulama) specialized in medical ethics is recommended for "
            "complex bioethical issues. The principle of 'necessity permits the forbidden' (al-darurat tubih al-mahzurat) "
            "may apply in life-threatening situations."
        )

    def _add_general_islamic_science_perspective(self) -> str:
        """Add general Islamic perspective on science and knowledge"""
        return (
            "## Islamic View on Science and Knowledge\n\n"
            "**Core Principles:**\n"
            "- **Pursuit of Knowledge**: 'Seek knowledge from the cradle to the grave'\n"
            "- **Ethical Responsibility**: Science should benefit humanity and avoid harm\n"
            "- **Tawhid (Unity)**: All knowledge ultimately points to the Creator\n"
            "- **Stewardship (Khilafah)**: Humans are trustees of knowledge and technology\n\n"
            "**Recommended Approach:**\n"
            "- Consult Islamic scholars for ethical guidance\n"
            "- Consider the wider implications for society and environment\n"
            "- Ensure research methods and applications align with Islamic values\n"
            "- Seek beneficial knowledge that serves humanity's welfare"
        )

    def detect_query_type(self, query: str) -> str:
        """Detect if a query is medical, technological, or general"""
        query_lower = query.lower()

        medical_patterns = [
            r"\b(medical|health|disease|treatment|therapy|clinical|patient|medicine)\b",
            r"\b(bioethics|pharmaceutical|genetics|surgery|diagnosis)\b",
            r"\b(healthcare|hospital|doctor|nurse|medication|drug)\b",
        ]

        tech_patterns = [
            r"\b(technology|ai|artificial intelligence|computer|algorithm)\b",
            r"\b(machine learning|physics|mathematics|engineering|science)\b",
            r"\b(robotics|automation|digital|software|hardware)\b",
        ]

        is_medical = any(
            re.search(pattern, query_lower) for pattern in medical_patterns
        )
        is_tech = any(re.search(pattern, query_lower) for pattern in tech_patterns)

        if is_medical and is_tech:
            return "both"
        elif is_medical:
            return "medical"
        elif is_tech:
            return "technology"
        else:
            return "general"
