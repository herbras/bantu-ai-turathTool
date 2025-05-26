import json
import re
from os import getenv
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse

from agno.tools import Toolkit
from agno.utils.log import logger

try:
    from tavily import TavilyClient
except ImportError:
    raise ImportError("`tavily-python` not installed. Please install using `pip install tavily-python`")


class TurathTavilyTools(Toolkit):
    """
    Enhanced TavilyTools specifically designed for Islamic research and Turath studies.
    Provides web search capabilities to complement the internal MCP database.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        search: bool = True,
        max_tokens: int = 6000,
        include_answer: bool = True,
        search_depth: Literal["basic", "advanced"] = "advanced",
        format: Literal["json", "markdown"] = "markdown",
        use_search_context: bool = False,
        **kwargs,
    ):
        self.api_key = api_key or getenv("TAVILY_API_KEY")
        if not self.api_key:
            logger.error("TAVILY_API_KEY not provided")

        self.client: TavilyClient = TavilyClient(api_key=self.api_key)
        self.search_depth: Literal["basic", "advanced"] = search_depth
        self.max_tokens: int = max_tokens
        self.include_answer: bool = include_answer
        self.format: Literal["json", "markdown"] = format

        tools: List[Any] = []
        if search:
            if use_search_context:
                tools.append(self.search_islamic_references_web)
            else:
                tools.append(self.search_islamic_content_web)

        super().__init__(name="turath_tavily_tools", tools=tools, **kwargs)

    def search_islamic_content_web(self, query: str, max_results: int = 5) -> str:
        """Search the web for Islamic content, scholarly articles, and references.
        Use this to find additional Islamic sources, contemporary scholarly opinions, 
        or cross-references that complement the internal Turath database.

        Args:
            query (str): Islamic topic or query to search for (e.g., "Shafi'i jurisprudence", "hadith authentication")
            max_results (int): Maximum number of results to return. Defaults to 5.

        Returns:
            str: Formatted search results with Islamic sources and references.
        """
        
        # Enhance query for Islamic content
        enhanced_query = f"{query} Islam Islamic scholar fiqh hadith Quran"
        
        response = self.client.search(
            query=enhanced_query, 
            search_depth=self.search_depth, 
            include_answer=self.include_answer, 
            max_results=max_results
        )

        clean_response: Dict[str, Any] = {"query": query, "enhanced_query": enhanced_query}
        if "answer" in response:
            clean_response["answer"] = response["answer"]

        clean_results = []
        current_token_count = len(json.dumps(clean_response))
        for result in response.get("results", []):
            _result = {
                "title": result["title"],
                "url": result["url"],
                "content": result["content"],
                "score": result["score"],
                "source_type": self._identify_source_type(result["url"])
            }
            current_token_count += len(json.dumps(_result))
            if current_token_count > self.max_tokens:
                break
            clean_results.append(_result)
        clean_response["results"] = clean_results

        if self.format == "json":
            return json.dumps(clean_response) if clean_response else "No Islamic web references found."
        elif self.format == "markdown":
            return self._format_islamic_markdown(query, clean_response)

    def search_islamic_references_web(self, query: str) -> str:
        """Search for Islamic references using Tavily's context API.
        Provides more contextual and summarized information about Islamic topics.

        Args:
            query (str): Islamic topic to search for context and references.

        Returns:
            str: Contextual information about the Islamic topic.
        """
        enhanced_query = f"{query} Islam Islamic scholarship fiqh"
        
        return self.client.get_search_context(
            query=enhanced_query, 
            search_depth=self.search_depth, 
            max_tokens=self.max_tokens, 
            include_answer=self.include_answer
        )

    def _identify_source_type(self, url: str) -> str:
        """Identify the type of Islamic source based on URL (granular Dorar support)."""
        url_lc = url.lower()
        netloc = urlparse(url_lc).netloc
        path = urlparse(url_lc).path

        # ------------------------------------------------
        # 1) FATWA / Q&A  (incl. MUI & rumahfiqih)
        # ------------------------------------------------
        if any(d in netloc for d in [
            'dar-alifta.org', 'alifta.gov.sa', 'islam.gov.kw',
            'islamqa.info', 'binbaz.org.sa', 'binbaz.co.uk',
            'uthaymeen.com', 'binothaimeen.net', 'binuthaymin.co.uk',
            'dralfawzann.com', 'albaani', 'thealbaani.site',
            'fatwaonline.net', 'islamweb.net', 'abdurrahman.org',
            'mui.or.id', 'rumahfiqih.com', 'rumahfiqih'
        ]):
            return "Fatwa/Q&A Site"

        # ------------------------------------------------
        # 2) DORAR.NET  –– granular by sub-path (check BEFORE generic hadith)
        # ------------------------------------------------
        if 'dorar.net' in netloc:
            # mapping path prefix ➜ label
            dorar_map = {
                r'^/tafseer':        "Tafsir Encyclopedia",
                r'^/hadith':         "Hadith Encyclopedia",
                r'^/aqeeda':         "Aqidah Encyclopedia",
                r'^/adyan':          "Religions Encyclopedia",
                r'^/frq':            "Firaq (Sects) Encyclopedia",
                r'^/feqhia':         "Fiqh Encyclopedia",
                r'^/osolfeqh':       "Usul Fiqh Encyclopedia",
                r'^/qfiqhia':        "Qawaid Fiqhiyya Encyclopedia",
                r'^/alakhlaq':       "Akhlaq Encyclopedia",
                r'^/history':        "History Encyclopedia",
                r'^/aadab':          "Adab Shar'iyyah Encyclopedia",
                r'^/arabia':         "Arabic Language Encyclopedia",
                r'^/fake-hadith':    "Weak & Fabricated Hadiths",
                r'^/apps':           "Islamic App Page",
                r'^/store':          "Dorar Store"
            }
            for pattern, label in dorar_map.items():
                if re.match(pattern, path):
                    return label
            # fallback when domain dorar.net tidak cocok pattern di atas
            return "Dorar – Other Section"

        # ------------------------------------------------
        # 3) HADITH COLLECTION  – specific domains only (after Dorar check)
        # ------------------------------------------------
        if any(d in netloc for d in ['sunnah.com']) or \
           any(pattern in url_lc for pattern in ['bukhari', 'muslim']) and 'hadith' in url_lc:
            return "Hadith Collection"

        # ------------------------------------------------
        # 4) QURANIC RESOURCE
        # ------------------------------------------------
        if any(d in netloc for d in ['quran.com', 'tanzil.net', 'corpus.quran.com']):
            return "Quranic Resource"

        # ------------------------------------------------
        # 5) ISLAMIC DIGITAL LIBRARY – PDF / eBook
        # ------------------------------------------------
        if any(d in netloc for d in [
            'shamela.ws', 'shamela.org', 'amuslim.org',
            'kalamullah.net', 'islamhouse.com',
            'waqfeya.net',                 # مكتبة الوقفية
        ]):
            return "Islamic Digital Library"

        # ------------------------------------------------
        # 6) ISLAMIC MULTIMEDIA
        # ------------------------------------------------
        if any(d in netloc for d in [
            'yufid.com', 'kajian.net', 'radiotarbiyahsunnah.com',
            'islamway.net', 'ar.islamway.net',   # إسلام ويب مالتيميديا
        ]):
            return "Islamic Multimedia"

        # ------------------------------------------------
        # 7) ISLAMIC PORTAL / ARTICLE HUB
        # ------------------------------------------------
        if any(d in netloc for d in [
            'rumaysho.com', 'muslim.or.id', 'almanhaj.or.id',
            'salafy.or.id', 'konsultasisyariah.com', 'bimbinganislam.com',
            'aslibumiayu.net', 'mawdoo3.com', 'alukah.net',
            'spubs.com', 'troid.org', 'salafiri.com',
            'islamicfinder.org', 'islamicity.org'
        ]):
            return "Islamic Portal"

        # ------------------------------------------------
        # 8) ACADEMIC PAPER
        # ------------------------------------------------
        if any(d in netloc for d in ['academia.edu', 'jstor', 'doi.org']):
            return "Academic Paper"

        # ------------------------------------------------
        # 9) DEFAULT
        # ------------------------------------------------
        return "General Web Source"

    def _format_islamic_markdown(self, query: str, response: Dict[str, Any]) -> str:
        """Format search results specifically for Islamic content"""
        _markdown = f"# Web References for: {query}\n\n"
        
        if "answer" in response:
            _markdown += "## Summary\n"
            _markdown += f"{response.get('answer')}\n\n"
            
        _markdown += "## Additional Web Sources\n\n"
        
        for i, result in enumerate(response["results"], 1):
            source_type = result.get("source_type", "Web Source")
            _markdown += f"### {i}. [{result['title']}]({result['url']})\n"
            _markdown += f"**Source Type:** {source_type}  \n"
            _markdown += f"**Relevance Score:** {result['score']:.2f}  \n"
            _markdown += f"{result['content']}\n\n"
            _markdown += "---\n\n"
            
        return _markdown 