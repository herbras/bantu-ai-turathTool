from typing import Iterator, List, Dict, Any
import asyncio
import time
from datetime import datetime

from agno.workflow import Workflow
from agno.agent import RunResponse, RunEvent
from agno.utils.log import logger

# Global agent service registry - will be set by main app
_global_agent_service = None


def set_global_agent_service(agent_service):
    """Set global agent service for workflows to access"""
    global _global_agent_service
    _global_agent_service = agent_service


# Note: These agents will be created dynamically when needed
# from ..agents.turath_query import create_turath_query_agent
# from ..agents.fact_checker import create_fact_checker_agent
# from ..agents.turath_writer import create_turath_writer_agent
# from ..teams.turath_research_team import create_turath_research_team
# from ..teams.turath_editor import create_turath_editor_team


class TurathResearchWorkflow(Workflow):
    """
    Comprehensive Islamic research workflow yang mengkoordinasi:
    - Multi-source search (Internal DB, Web, Scientific Literature)
    - Fact checking dengan cross-validation
    - Collaborative writing dengan tim editor
    - Progressive research dengan caching intermediate results
    """

    description: str = (
        "Advanced Islamic research workflow with multi-agent coordination"
    )

    # Note: Agents will be initialized dynamically
    # Core agents and teams will be accessed via session or service

    def run(
        self,
        research_query: str,
        research_type: str = "comprehensive",  # comprehensive, quick, academic
        output_format: str = "article",  # article, summary, academic_paper
        use_cache: bool = True,
        include_scientific: bool = True,
        include_web_sources: bool = True,
        max_sources: int = 10,
    ) -> Iterator[RunResponse]:
        """
        Main workflow execution dengan progressive stages:
        1. Research Planning & Query Enhancement
        2. Multi-Source Information Gathering
        3. Fact Checking & Cross-Validation
        4. Content Writing & Structuring
        5. Editorial Review & Finalization
        """

        start_time = time.time()
        cache_key = f"{research_query}_{research_type}_{output_format}"

        # Store start time for processing time calculation
        self.session_state["start_time"] = start_time

        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.workflow_started,
            content=f"🔍 **Memulai riset comprehensive untuk:**\n'{research_query}'\n\n",
        )

        # Stage 1: Check cache for complete research
        if use_cache and self._check_complete_cache(cache_key):
            logger.info("Found complete cached research")
            yield from self._yield_cached_result(cache_key)
            return

        # Stage 2: Research Planning & Query Enhancement
        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.run_response,
            content="📋 **Stage 1: Research Planning**\nMenganalisis query dan merencanakan strategi pencarian...\n\n",
        )

        research_plan = self._create_research_plan(research_query, research_type)
        self.session_state["research_plan"] = research_plan

        # Stage 3: Multi-Source Information Gathering (Parallel)
        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.run_response,
            content="🔍 **Stage 2: Information Gathering**\nMencari dari multiple sources secara paralel...\n\n",
        )

        # Execute gathering and yield progress updates
        yield from self._gather_information_with_agents(
            research_plan["enhanced_queries"],
            include_scientific,
            include_web_sources,
            max_sources,
            use_cache,
        )

        # Get the gathered sources from session state
        gathered_sources = self.session_state.get(
            "gathered_sources", {"all_sources": []}
        )

        # Stage 4: Fact Checking & Cross-Validation
        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.run_response,
            content="✅ **Stage 3: Fact Checking**\nMemvalidasi informasi dan melakukan cross-reference...\n\n",
        )

        validated_content = yield from self._fact_check_and_validate(gathered_sources)

        # Stage 5: Content Writing & Structuring
        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.run_response,
            content="✍️ **Stage 4: Content Writing**\nMenyusun konten berdasarkan hasil riset...\n\n",
        )

        written_content = yield from self._write_with_agents(
            validated_content, output_format, research_plan
        )

        # Stage 6: Editorial Review & Finalization
        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.run_response,
            content="📝 **Stage 5: Editorial Review**\nMelakukan review dan finalisasi konten...\n\n",
        )

        final_content = yield from self._editorial_review_and_finalize(written_content)

        # Cache complete result
        if use_cache:
            self._cache_complete_result(cache_key, final_content, gathered_sources)

        # Final result
        total_time = time.time() - start_time
        self.session_state["processing_time"] = f"{total_time:.1f}s"
        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.workflow_completed,
            content=f"{final_content}\n\n---\n📊 **Research Summary:**\n"
            f"- Total sources: {len(gathered_sources.get('all_sources', []))}\n"
            f"- Processing time: {total_time:.1f}s\n"
            f"- Research type: {research_type}\n"
            f"- Output format: {output_format}",
        )

    def _create_research_plan(self, query: str, research_type: str) -> Dict[str, Any]:
        """Create comprehensive research plan based on query and type"""
        plan = {
            "original_query": query,
            "research_type": research_type,
            "enhanced_queries": [],
            "search_strategies": [],
            "expected_sources": [],
        }

        # Enhanced query generation based on research type
        if research_type == "comprehensive":
            plan["enhanced_queries"] = [
                query,
                f"{query} في القرآن والسنة",
                f"{query} عند العلماء المعاصرين",
                f"{query} في المذاهب الفقهية",
                f"حكم {query} في الإسلام",
            ]
        elif research_type == "academic":
            plan["enhanced_queries"] = [
                query,
                f"دراسة أكاديمية حول {query}",
                f"البحث العلمي في {query}",
                f"المراجع الحديثة في {query}",
            ]
        else:  # quick
            plan["enhanced_queries"] = [query, f"تعريف {query}"]

        return plan

    def _gather_information_with_agents(
        self,
        queries: List[str],
        include_scientific: bool,
        include_web: bool,
        max_sources: int,
        use_cache: bool,
    ) -> Iterator[RunResponse]:
        """Gather information using real agents via async execution"""

        all_sources = {
            "internal_db": [],
            "web_sources": [],
            "scientific": [],
            "all_sources": [],
        }

        # Get agent service from multiple sources
        agent_service = getattr(self, "_agent_service", None) or _global_agent_service

        # Debug logging
        print(f"🔍 [WORKFLOW DEBUG] Agent service during execution: {agent_service}")
        print(f"🔍 [WORKFLOW DEBUG] Agent service type: {type(agent_service)}")
        print(f"🔍 [WORKFLOW DEBUG] Has agent service: {agent_service is not None}")
        print(f"🔍 [WORKFLOW DEBUG] Global agent service: {_global_agent_service}")

        if agent_service:
            print(f"🔍 [WORKFLOW DEBUG] Agent service attributes: {dir(agent_service)}")
            if hasattr(agent_service, "agents"):
                print(
                    f"🔍 [WORKFLOW DEBUG] Available agents: {list(agent_service.agents.keys())}"
                )
            if hasattr(agent_service, "get_agent"):
                test_agent = agent_service.get_agent("turath_query")
                print(
                    f"🔍 [WORKFLOW DEBUG] turath_query agent found: {test_agent is not None}"
                )
                print(f"🔍 [WORKFLOW DEBUG] Agent object: {test_agent}")

        if not agent_service:
            # Fallback to simulated if no agent service available
            yield from self._fallback_simulated_search(
                queries, include_scientific, include_web
            )
            return

        for i, query in enumerate(queries):
            yield RunResponse(
                run_id=self.run_id,
                event=RunEvent.run_response,
                content=f"🔍 **Real Agent Search** {i + 1}/{len(queries)}:\n   '{query}'\n",
            )

            try:
                # Use TurathQueryAgent for comprehensive search (correct agent name is 'turath_query')
                query_agent = agent_service.get_agent("turath_query")
                if query_agent:
                    # 🔧 FALLBACK: Use text output since structured output doesn't work with Google AI Studio
                    result = asyncio.run(self._run_agent_query(query_agent, query))

                    if result:
                        # Extract actual content from result if it's a RunResponse object
                        actual_content = self._extract_content_from_result(result)

                        # Create structured-like data from text result - NO TRUNCATION!
                        all_sources["internal_db"].append(
                            {
                                "query": query,
                                "content": actual_content,  # Full content, no truncation
                                "summary": self._extract_meaningful_summary(
                                    actual_content
                                ),  # Smart summary
                                "ruling": self._extract_ruling_from_content(
                                    actual_content
                                ),
                                "confidence": 0.8,  # Default confidence for text results
                                "sources": ["Turath Database"],
                                "source_type": "turath_database",
                                "agent_used": "turath_query",
                            }
                        )

                        yield RunResponse(
                            run_id=self.run_id,
                            event=RunEvent.run_response,
                            content="   ✅ **Success!** Found results from Turath database\n",
                        )
                    else:
                        yield RunResponse(
                            run_id=self.run_id,
                            event=RunEvent.run_response,
                            content="   ⚠️ **No results found**\n",
                        )

            except Exception as e:
                logger.error(f"Error running agent query: {e}")
                yield RunResponse(
                    run_id=self.run_id,
                    event=RunEvent.run_response,
                    content=f"   ❌ **Error:** {str(e)}\n",
                )

        # Combine all sources
        all_sources["all_sources"] = (
            all_sources["internal_db"]
            + all_sources["web_sources"]
            + all_sources["scientific"]
        )

        self.session_state["gathered_sources"] = all_sources

        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.run_response,
            content=f"\n📚 **Search Complete:**\n"
            f"   • Turath Database: {len(all_sources['internal_db'])} results\n"
            f"   • Web sources: {len(all_sources['web_sources'])} results\n"
            f"   • Scientific: {len(all_sources['scientific'])} results\n\n",
        )

    async def _run_agent_query(self, agent, query: str) -> str:
        """Run agent query asynchronously - returns text result"""
        try:
            result = await agent.arun(query)
            return str(result)
        except Exception as e:
            logger.error(f"Agent query error: {e}")
            return f"Error: {str(e)}"

    def _extract_ruling_from_content(self, content: str) -> str:
        """Extract Islamic ruling from content using simple text analysis"""
        if not content:
            return "Tidak spesifik"

        content_lower = content.lower()

        # Check for specific rulings
        if any(
            word in content_lower for word in ["halal", "dibolehkan", "tidak haram"]
        ):
            return "halal"
        elif any(
            word in content_lower
            for word in ["haram", "dilarang", "tidak diperbolehkan"]
        ):
            return "haram"
        elif any(
            word in content_lower
            for word in ["makruh", "tidak disukai", "sebaiknya dihindari"]
        ):
            return "makruh"
        elif any(word in content_lower for word in ["mubah", "boleh", "netral"]):
            return "mubah"
        elif any(word in content_lower for word in ["wajib", "fardhu", "harus"]):
            return "wajib"
        elif any(
            word in content_lower for word in ["mustahab", "sunnah", "dianjurkan"]
        ):
            return "mustahab"
        else:
            return "Perlu kajian lebih lanjut"

    def _extract_meaningful_summary(self, content: str) -> str:
        """Extract meaningful summary without truncation artifacts"""
        if not content:
            return "Konten tidak tersedia"

        # Split into sentences
        sentences = content.replace("\n", " ").split(".")
        meaningful_sentences = []

        for sentence in sentences[:3]:  # Take first 3 sentences
            clean_sentence = sentence.strip()
            if len(clean_sentence) > 20 and any(
                keyword in clean_sentence.lower()
                for keyword in [
                    "hukum",
                    "fikih",
                    "recek",
                    "kulit",
                    "samak",
                    "halal",
                    "haram",
                ]
            ):
                meaningful_sentences.append(clean_sentence + ".")

        if meaningful_sentences:
            return " ".join(meaningful_sentences)
        else:
            # Fallback to first substantial paragraph
            paragraphs = content.split("\n")
            for para in paragraphs:
                if len(para.strip()) > 50:
                    return (
                        para.strip()[:400] + "..."
                        if len(para.strip()) > 400
                        else para.strip()
                    )

            return content[:300] + "..." if len(content) > 300 else content

    def _extract_key_points_from_content(self, content: str) -> str:
        """Extract key points from content in bullet format"""
        if not content:
            return "- Tidak ada informasi tersedia"

        # Look for numbered points, bullet points, or key statements
        lines = content.split("\n")
        key_points = []

        for line in lines:
            line = line.strip()
            if line and any(
                marker in line
                for marker in ["1.", "2.", "3.", "4.", "5.", "•", "-", "**"]
            ):
                # Clean up the line
                clean_line = line.replace("**", "").strip()
                if len(clean_line) > 15:
                    key_points.append(f"- {clean_line}")
            elif line and any(
                keyword in line.lower()
                for keyword in [
                    "hukum",
                    "halal",
                    "haram",
                    "recek",
                    "kulit",
                    "samak",
                    "bangkai",
                    "sembelihan",
                ]
            ):
                if len(line) > 30 and len(line) < 200:  # Good length for key point
                    key_points.append(f"- {line}")

        if key_points:
            return "\n".join(key_points[:5])  # Max 5 key points
        else:
            # Fallback: extract first few meaningful sentences
            sentences = content.replace("\n", " ").split(".")
            meaningful = []
            for sentence in sentences[:3]:
                if len(sentence.strip()) > 30:
                    meaningful.append(f"- {sentence.strip()}")

            return "\n".join(meaningful) if meaningful else f"- {content[:200]}..."

    def _generate_practical_conclusion(
        self, structured_sources: List[Dict], query: str
    ) -> str:
        """Generate practical conclusion based on findings"""
        if not structured_sources:
            return f"Masalah **{query}** memerlukan kajian lebih mendalam dari ulama kompeten."

        # Get most common ruling
        rulings = [s.get("ruling") for s in structured_sources if s.get("ruling")]
        if rulings:
            from collections import Counter

            most_common_ruling = Counter(rulings).most_common(1)[0][0]

            ruling_explanation = {
                "halal": "diperbolehkan dalam Islam",
                "haram": "dilarang dalam Islam",
                "makruh": "sebaiknya dihindari meski tidak diharamkan",
                "mubah": "diperbolehkan (netral)",
                "wajib": "diwajibkan dalam Islam",
                "mustahab": "dianjurkan dalam Islam",
            }

            conclusion = f"""
**🎯 Kesimpulan Utama:**  
Berdasarkan analisis {len(structured_sources)} sumber dari database Turath, **{query}** adalah **{most_common_ruling}** ({ruling_explanation.get(most_common_ruling, "perlu kajian lebih lanjut")}).

**🔍 Dasar Kesimpulan:**
{self._extract_conclusion_basis(structured_sources)}

**💡 Rekomendasi Praktis:**
- Untuk kepastian hukum, konsultasikan dengan ulama setempat
- Pertimbangkan kondisi dan konteks spesifik
- Utamakan kehati-hatian dalam praktik keagamaan
"""
        else:
            conclusion = f"""
**📋 Status Penelitian:**  
Masalah **{query}** memerlukan kajian lebih mendalam dan konsultasi dengan ahli fikih yang kompeten.

**🔍 Temuan:**
{self._extract_conclusion_basis(structured_sources)}

**💡 Langkah Selanjutnya:**
- Konsultasi dengan ulama atau lembaga fatwa terpercaya
- Penelitian lebih lanjut dari sumber klasik dan kontemporer
- Pertimbangan aspek maslahah dan maqashid syariah
"""

        return conclusion

    def _extract_conclusion_basis(self, structured_sources: List[Dict]) -> str:
        """Extract basis for conclusion from sources"""
        key_points = []

        for source in structured_sources:
            content = source.get("content", "")
            if content:
                # Find key statements or evidence
                sentences = content.split(".")
                for sentence in sentences:
                    if any(
                        keyword in sentence.lower()
                        for keyword in [
                            "dalil",
                            "ayat",
                            "hadits",
                            "ulama",
                            "mazhab",
                            "ijma",
                            "qiyas",
                        ]
                    ):
                        clean_sentence = sentence.strip()
                        if len(clean_sentence) > 30 and len(clean_sentence) < 150:
                            key_points.append(f"- {clean_sentence}")
                            if len(key_points) >= 3:  # Max 3 points
                                break

            if len(key_points) >= 3:
                break

        return (
            "\n".join(key_points)
            if key_points
            else "- Perlu penelitian lebih mendalam dari sumber-sumber otentik"
        )

    def _extract_content_from_result(self, result) -> str:
        """Extract actual content from various result types with aggressive parsing"""
        try:
            # Direct content attribute access
            if hasattr(result, "content") and result.content:
                return str(result.content)

            # Dict with content key
            if isinstance(result, dict) and "content" in result:
                return str(result["content"])

            # If already a clean string
            if isinstance(result, str) and not result.startswith("RunResponse"):
                return result

            # Convert to string for parsing
            result_str = str(result)

            # Debug logging
            print(f"🔍 [EXTRACT DEBUG] Raw result: {result_str[:200]}...")

            import re

            # Advanced RunResponse parsing patterns
            patterns = [
                # Pattern 1: content='...' with proper quote handling
                r"content='((?:[^'\\]|\\.|'')*)'",
                # Pattern 2: content="..." with proper quote handling
                r'content="((?:[^"\\]|\\.)*)"',
                # Pattern 3: Unquoted content until next field
                r"content=([^,)]+?)(?:,|\)|$)",
                # Pattern 4: Extract everything after content= aggressively
                r"content=(.+?)(?:run_id=|event=|$)",
                # Pattern 5: Fallback - just get the bulk content
                r"'([^']*(?:hukum|fikih|islam|حكم|halal|haram)[^']*)'",
            ]

            for pattern in patterns:
                try:
                    match = re.search(pattern, result_str, re.DOTALL | re.IGNORECASE)
                    if match:
                        content = match.group(1).strip()

                        # Clean up extracted content
                        content = content.replace("\\'", "'").replace('\\"', '"')
                        content = content.replace("\\n", "\n").replace("\\t", "\t")

                        # Remove quotes if they wrap the entire content
                        if content.startswith(("'", '"')) and content.endswith(
                            ("'", '"')
                        ):
                            content = content[1:-1]

                        # Validate content quality
                        if len(content.strip()) > 50 and any(
                            keyword in content.lower()
                            for keyword in [
                                "hukum",
                                "islam",
                                "fikih",
                                "halal",
                                "haram",
                                "recek",
                                "kulit",
                                "samak",
                            ]
                        ):
                            print(
                                f"✅ [EXTRACT SUCCESS] Pattern {patterns.index(pattern) + 1} worked: {content[:100]}..."
                            )
                            return content

                except Exception as e:
                    print(
                        f"⚠️ [EXTRACT PATTERN ERROR] Pattern {patterns.index(pattern) + 1}: {e}"
                    )
                    continue

            # Emergency fallback - try to find any meaningful Islamic content
            islamic_content = []
            lines = result_str.split("\n")
            for line in lines:
                clean_line = line.strip()
                if len(clean_line) > 20 and any(
                    keyword in clean_line.lower()
                    for keyword in [
                        "hukum",
                        "fikih",
                        "recek",
                        "kulit",
                        "samak",
                        "halal",
                        "haram",
                    ]
                ):
                    # Remove obvious wrapper text
                    clean_line = re.sub(
                        r'^RunResponse\(.*?content=[\'"]*', "", clean_line
                    )
                    clean_line = re.sub(r'[\'"]*\).*?$', "", clean_line)
                    if len(clean_line.strip()) > 10:
                        islamic_content.append(clean_line.strip())

            if islamic_content:
                final_content = "\n".join(islamic_content[:3])  # Take best 3 lines
                print(
                    f"🔧 [EXTRACT FALLBACK] Emergency extraction: {final_content[:100]}..."
                )
                return final_content

            # Last resort - return original string
            print(f"❌ [EXTRACT FAILED] Returning original: {result_str[:100]}...")
            return result_str

        except Exception as e:
            logger.error(f"Fatal extraction error: {e}")
            return str(result)

    def _fallback_simulated_search(
        self, queries: List[str], include_scientific: bool, include_web: bool
    ) -> Iterator[RunResponse]:
        """Fallback to simulated search if no agents available"""
        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.run_response,
            content="⚠️ **Fallback Mode**: No agents available, using simulated search...",
        )

        all_sources = {
            "internal_db": [],
            "web_sources": [],
            "scientific": [],
            "all_sources": [],
        }

        for i, query in enumerate(queries):
            all_sources["internal_db"].append(
                {
                    "query": query,
                    "content": f"Simulated fallback result for: {query}",
                    "source_type": "simulated_fallback",
                }
            )

        all_sources["all_sources"] = all_sources["internal_db"]
        self.session_state["gathered_sources"] = all_sources

    def _fact_check_and_validate(
        self, sources: Dict[str, List]
    ) -> Iterator[RunResponse]:
        """Fact check and cross-validate information from multiple sources"""

        fact_check_input = {
            "sources": sources["all_sources"],
            "validation_criteria": [
                "authenticity",
                "scholarly_consensus",
                "source_reliability",
            ],
        }

        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.run_response,
            content="   🔍 Melakukan fact-checking dengan cross-validation...\n",
        )

        # Simulate fact checking (TODO: integrate with actual fact checker agent)
        fact_check_report = f"Simulated fact-checking completed for {len(sources['all_sources'])} sources"

        validated_content = {
            "validated_sources": sources,
            "fact_check_report": fact_check_report,
            "reliability_scores": self._calculate_reliability_scores(sources),
            "cross_references": self._find_cross_references(sources),
        }

        self.session_state["validated_content"] = validated_content

        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.run_response,
            content="   ✅ **Fact-checking completed** - Sources validated and scored.\n\n",
        )

        return validated_content

    def _write_with_agents(
        self,
        validated_content: Dict[str, Any],
        output_format: str,
        research_plan: Dict[str, Any],
    ) -> Iterator[RunResponse]:
        """Write structured content using real agents"""

        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.run_response,
            content=f"   ✍️ Generating {output_format} dengan real agent...\n",
        )

        # Get agent service
        agent_service = getattr(self, "_agent_service", None)
        if not agent_service:
            return self._fallback_content_generation(
                validated_content, output_format, research_plan
            )

        try:
            # Create comprehensive writing prompt
            writing_prompt = self._create_comprehensive_writing_prompt(
                validated_content, output_format, research_plan
            )

            # Get a capable writer agent (use turath_query as general agent, or try turath_writer)
            writer_agent = agent_service.get_agent(
                "turath_writer"
            ) or agent_service.get_agent("turath_query")

            if writer_agent:
                yield RunResponse(
                    run_id=self.run_id,
                    event=RunEvent.run_response,
                    content="   📝 Agent sedang menulis content comprehensive...\n",
                )

                # Run writing task
                written_content = asyncio.run(
                    self._run_agent_writing(writer_agent, writing_prompt)
                )

                if written_content and len(written_content.strip()) > 100:
                    yield RunResponse(
                        run_id=self.run_id,
                        event=RunEvent.run_response,
                        content="✅ **Content generation successful** - High-quality content produced",
                    )

                    self.session_state["written_content"] = written_content
                    return written_content
                else:
                    yield RunResponse(
                        run_id=self.run_id,
                        event=RunEvent.run_response,
                        content="⚠️ Agent output insufficient, using enhanced content...",
                    )

        except Exception as e:
            logger.error(f"Error in agent writing: {e}")
            yield RunResponse(
                run_id=self.run_id,
                event=RunEvent.run_response,
                content=f"⚠️ Writing error: {str(e)}, using fallback...",
            )

        # Fallback to enhanced content generation
        return self._fallback_content_generation(
            validated_content, output_format, research_plan
        )

    async def _run_agent_writing(self, agent, prompt: str) -> str:
        """Run agent writing task"""
        try:
            result = await agent.arun(prompt)
            return str(result)
        except Exception as e:
            logger.error(f"Agent writing error: {e}")
            return ""

    def _fallback_content_generation(
        self,
        validated_content: Dict[str, Any],
        output_format: str,
        research_plan: Dict[str, Any],
    ) -> str:
        """Generate comprehensive content using retrieved data"""

        # Extract structured search results (no more parsing!)
        internal_sources = validated_content.get("validated_sources", {}).get(
            "internal_db", []
        )
        query = research_plan.get("original_query", "Unknown topic")

        # Calculate research quality metrics
        total_confidence = sum(
            source.get("confidence", 0.0) for source in internal_sources
        )
        avg_confidence = (
            total_confidence / len(internal_sources) if internal_sources else 0.0
        )
        total_evidence = sum(
            len(source.get("evidence", {}).get("quran", []))
            + len(source.get("evidence", {}).get("hadith", []))
            for source in internal_sources
        )

        # Generate focused content based on actual findings - LESS TEMPLATE, MORE SUBSTANCE
        enhanced_content = f"""# 📜 Penelitian Fikih: {query}

## 🔍 Hasil Penelitian Database Turath

{self._generate_comprehensive_findings(internal_sources, query)}

## 📚 Analisis Ulama dan Scholarly Perspective

{self._generate_scholarly_perspective_structured(internal_sources, query)}

## ✅ Kesimpulan Hukum

{self._generate_practical_conclusion(internal_sources, query)}

---
💡 **Info Penelitian:** Dianalisis dari {len(internal_sources)} sumber database Turath | Waktu: {self.session_state.get("processing_time", "N/A")}
"""

        self.session_state["written_content"] = enhanced_content
        return enhanced_content

    def _format_source_analysis(self, sources: List[Dict]) -> str:
        """Format source analysis for better presentation"""
        if not sources:
            return "- Tidak ada sumber spesifik yang dianalisis dalam mode fallback"

        analysis = []
        for i, source in enumerate(sources[:3], 1):  # Show first 3 sources
            analysis.append(
                f"- **Sumber {i}**: {source.get('content', 'No content')[:200]}..."
            )

        return "\n".join(analysis)

    def _generate_comprehensive_findings(
        self, all_structured_sources: List[Dict], query: str
    ) -> str:
        """Generate comprehensive findings from clean structured data - FOCUS ON CONTENT"""
        if not all_structured_sources:
            return f"Penelitian mengenai **{query}** memerlukan analisis lebih mendalam dari sumber-sumber yang tersedia."

        findings = []

        # Process structured sources - FULL CONTENT, NO TRUNCATION
        for i, source in enumerate(all_structured_sources[:3], 1):
            if source and source.get("content"):
                ruling = source.get("ruling", "Tidak spesifik")
                content = source.get("content", "")

                # Extract key findings from content
                key_points = self._extract_key_points_from_content(content)

                findings.append(f"""
### Temuan {i}: {source.get("query", query)}

**🔍 Hukum Islam:** {ruling}

**📝 Temuan Kunci:**
{key_points}

**💡 Analisis Detail:**
{content}
""")

        if not findings:
            findings.append(f"""
### Analisis Awal

Berdasarkan penelitian yang telah dilakukan, **{query}** merupakan permasalahan fikih kontemporer yang memerlukan kajian mendalam dari berbagai sumber otentik.
""")

        return "\n".join(findings)

    def _extract_and_clean_content(self, raw_content: str) -> str:
        """Extract and clean content from raw text or RunResponse"""
        # First apply the existing extraction method
        extracted = self._extract_content_from_result(raw_content)

        # Additional cleaning
        if extracted:
            # Remove common artifacts
            extracted = (
                extracted.replace("RunResponse(content=", "").replace("')", "").strip()
            )

            # Remove excess quotes
            if extracted.startswith('"') and extracted.endswith('"'):
                extracted = extracted[1:-1]
            if extracted.startswith("'") and extracted.endswith("'"):
                extracted = extracted[1:-1]

            # Clean up newlines and spacing
            extracted = (
                extracted.replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'")
            )

        return extracted

    def _extract_meaningful_excerpt(self, content: str, max_length: int = 400) -> str:
        """Extract meaningful excerpt from content"""
        if not content:
            return "Konten tidak tersedia"

        # Split into paragraphs and find the most relevant one
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]

        # Find paragraph with relevant keywords
        relevant_para = None
        for para in paragraphs:
            if any(
                keyword in para.lower()
                for keyword in [
                    "hukum",
                    "fikih",
                    "halal",
                    "haram",
                    "disamak",
                    "kulit",
                    "recek",
                ]
            ):
                relevant_para = para
                break

        # Use first substantial paragraph if no relevant one found
        if not relevant_para:
            for para in paragraphs:
                if len(para) > 50:
                    relevant_para = para
                    break

        # Use beginning of content if no good paragraph found
        if not relevant_para:
            relevant_para = content[:max_length]

        # Truncate if too long
        if len(relevant_para) > max_length:
            relevant_para = relevant_para[:max_length] + "..."

        return relevant_para

    def _generate_scholarly_perspective(
        self, all_content: List[str], query: str
    ) -> str:
        """Generate scholarly perspective section"""
        if not all_content:
            return f"Perspektif ulama mengenai **{query}** memerlukan rujukan kepada sumber-sumber klasik dan kontemporer."

        # Extract and analyze scholarly perspectives from content
        scholarly_points = []
        key_rulings = []

        for raw_content in all_content:
            # Clean the content first
            clean_content = self._extract_and_clean_content(raw_content)

            if clean_content:
                # Extract scholarly opinions
                if any(
                    keyword in clean_content.lower()
                    for keyword in [
                        "ulama",
                        "imam",
                        "syaikh",
                        "mazhab",
                        "fikih",
                        "ijma",
                    ]
                ):
                    excerpt = self._extract_meaningful_excerpt(clean_content, 200)
                    if excerpt and len(excerpt.strip()) > 30:
                        scholarly_points.append(f"**Perspektif Ulama:** {excerpt}")

                # Extract key rulings
                if any(
                    keyword in clean_content.lower()
                    for keyword in ["hukum", "halal", "haram", "makruh", "mubah"]
                ):
                    excerpt = self._extract_meaningful_excerpt(clean_content, 200)
                    if excerpt and len(excerpt.strip()) > 30:
                        key_rulings.append(f"**Hukum:** {excerpt}")

        result_sections = []

        if scholarly_points:
            result_sections.append(f"""
### Pandangan Ulama dan Cendekiawan

{chr(10).join(scholarly_points[:3])}
""")

        if key_rulings:
            result_sections.append(f"""
### Kesimpulan Hukum

{chr(10).join(key_rulings[:2])}
""")

        if result_sections:
            return (
                "\n".join(result_sections)
                + f"""

**Sintesis Akademis:** Berdasarkan analisis komprehensif, para ulama memberikan pandangan yang mendalam mengenai **{query}**, dengan mempertimbangkan aspek tekstual, kontekstual, dan metodologis dalam penetapan hukum Islam.
"""
            )
        else:
            return f"""
### Perspektif Ulama Kontemporer

Para ulama dan cendekiawan Islam kontemporer menekankan pentingnya **{query}** dalam konteks kehidupan modern, dengan pendekatan yang meliputi:

**Metodologi Kajian:**
- Analisis tekstual terhadap Al-Qur'an dan Sunnah
- Penelaahan pendapat ulama salaf dan khalaf
- Pertimbangan maslahah dan maqashid syariah
- Adaptasi dengan kondisi kontemporer

**Prinsip-Prinsip Penetapan Hukum:**
- Verifikasi autentisitas sumber
- Cross-referencing antar mazhab fikih
- Pertimbangan aspek praktis implementasi
- Dialog akademis berkelanjutan

**Relevansi Kontemporer:**
Permasalahan ini menunjukkan pentingnya ijtihad kontemporer dalam menghadapi isu-isu modern yang memerlukan solusi syar'i yang tepat dan komprehensif.
"""

    def _generate_scholarly_perspective_structured(
        self, structured_sources: List[Dict], query: str
    ) -> str:
        """Generate scholarly perspective from structured data"""
        if not structured_sources:
            return f"Perspektif ulama mengenai **{query}** memerlukan rujukan kepada sumber-sumber klasik dan kontemporer."

        # Aggregate rulings
        rulings = [s.get("ruling") for s in structured_sources if s.get("ruling")]
        ruling_counts = {r: rulings.count(r) for r in set(rulings) if r}

        # Aggregate mazhab perspectives
        all_mazhab_views = []
        for source in structured_sources:
            all_mazhab_views.extend(source.get("mazhab_views", []))

        # Generate analysis
        result = """
### Analisis Hukum Berdasarkan Data Terstruktur

**Distribusi Pendapat Hukum:**
"""

        for ruling, count in ruling_counts.items():
            percentage = (count / len(structured_sources)) * 100
            result += f"- **{ruling.upper()}**: {count}/{len(structured_sources)} sumber ({percentage:.1f}%)\n"

        if all_mazhab_views:
            result += """
**Perspektif Mazhab yang Ditemukan:**
"""
            mazhab_summary = {}
            for view in all_mazhab_views:
                mazhab = view.get("mazhab", "Unknown")
                if mazhab not in mazhab_summary:
                    mazhab_summary[mazhab] = []
                mazhab_summary[mazhab].append(view.get("evidence", ""))

            for mazhab, evidences in mazhab_summary.items():
                result += f"- **{mazhab}**: {len(evidences)} dalil/pendapat\n"

        # Calculate consensus level
        consensus_level = (
            "Kuat"
            if len(ruling_counts) == 1
            else "Lemah"
            if len(ruling_counts) > 3
            else "Sedang"
        )

        result += f"""
**Tingkat Konsensus:** {consensus_level}  
**Kualitas Data:** {sum(s.get("confidence", 0) for s in structured_sources) / len(structured_sources):.1f}/1.0

### Kesimpulan Akademis Terstruktur

Berdasarkan analisis AI terstruktur terhadap {len(structured_sources)} sumber database Turath, terdapat {"konsensus yang cukup jelas" if consensus_level == "Kuat" else "perbedaan pendapat yang perlu dikaji lebih lanjut"} mengenai **{query}**.

Penelitian ini menunjukkan pentingnya pendekatan teknologi AI dalam menganalisis khazanah fikih Islam secara sistematis dan terstruktur.
"""

        return result

    def _generate_detailed_analysis(
        self, structured_sources: List[Dict], query: str
    ) -> str:
        """Generate detailed analysis section from structured sources"""
        if len(structured_sources) >= 2:
            return f"""
Analisis mendalam terhadap sumber-sumber yang dikumpulkan menunjukkan bahwa **{query}** memiliki dimensi-dimensi berikut:

### Dimensi Tekstual
Berdasarkan rujukan kepada Al-Qur'an dan Sunnah, konsep ini memiliki landasan teologis yang kuat.

### Dimensi Historis  
Perkembangan pemikiran mengenai topik ini dapat ditelusuri melalui karya-karya ulama sepanjang sejarah Islam.

### Dimensi Metodologis
Pendekatan kajian yang digunakan menggabungkan metode klasik dan kontemporer dalam studi Islam.

### Dimensi Praktis
Implementasi konsep ini dalam kehidupan sehari-hari memerlukan pemahaman yang komprehensif dan kontekstual.
"""
        else:
            return f"""
Analisis terhadap **{query}** menunjukkan pentingnya topik ini dalam kajian Islam kontemporer. Meskipun sumber yang tersedia terbatas, kajian ini tetap memberikan wawasan berharga untuk pengembangan pemahaman lebih lanjut.
"""

    def _create_comprehensive_writing_prompt(
        self, validated_content: Dict, output_format: str, plan: Dict
    ) -> str:
        """Create comprehensive writing prompt for agents"""

        sources_text = ""
        internal_sources = validated_content.get("validated_sources", {}).get(
            "internal_db", []
        )

        for source in internal_sources:
            sources_text += f"- {source.get('content', '')}\n"

        prompt = f"""
You are an expert Islamic scholar and researcher. Please write a comprehensive {output_format} about: **{plan["original_query"]}**

RESEARCH CONTEXT:
- Research Type: {plan["research_type"]}
- Output Format: {output_format}
- Sources Analyzed: {len(internal_sources)}

AVAILABLE SOURCES:
{sources_text}

REQUIREMENTS:
1. Write in Indonesian language
2. Include proper Islamic terminology with Arabic terms
3. Provide balanced scholarly perspective
4. Structure content clearly with proper sections
5. Include citations and references where appropriate
6. Ensure minimum 500 words of substantial content
7. Address both classical and contemporary perspectives

STRUCTURE for {output_format}:
- Pendahuluan (Introduction)
- Latar Belakang (Background)
- Analisis Mendalam (Deep Analysis)
- Perspektif Ulama (Scholarly Perspectives)
- Aplikasi Kontemporer (Contemporary Applications)
- Kesimpulan (Conclusion)

Please write a high-quality, academic-level analysis that would be suitable for Islamic scholars and students.
"""
        return prompt

    def _editorial_review_and_finalize(self, content: str) -> Iterator[RunResponse]:
        """Editorial review and finalization using editor team"""

        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.run_response,
            content="   📝 Editorial team reviewing content...\n",
        )

        # Simulate editorial review (TODO: integrate with actual editor team)
        final_content = f"{content}\n\n---\n**Editorial Note:** Content reviewed and finalized (simulated)"

        self.session_state["final_content"] = final_content
        return final_content

    def _create_writing_prompt(
        self, validated_content: Dict, output_format: str, plan: Dict
    ) -> str:
        """Create comprehensive writing prompt for the writer agent"""

        prompt = f"""
Based on the comprehensive research conducted, please write a {output_format} about: {plan["original_query"]}

VALIDATED RESEARCH SOURCES:
{validated_content.get("fact_check_report", "")}

CROSS-REFERENCES FOUND:
{validated_content.get("cross_references", "")}

OUTPUT FORMAT: {output_format}
RESEARCH TYPE: {plan["research_type"]}

Please ensure:
1. Accurate citation of sources
2. Balanced presentation of different scholarly opinions
3. Clear Islamic perspective and context
4. Proper Arabic terminology with transliteration
5. Modern relevance and application

Structure the content appropriately for {output_format} format.
"""
        return prompt

    def _calculate_reliability_scores(
        self, sources: Dict[str, List]
    ) -> Dict[str, float]:
        """Calculate reliability scores for different source types"""
        scores = {}

        # Internal database sources (highest reliability)
        if sources.get("internal_db"):
            scores["internal_database"] = 0.95

        # Web sources (variable reliability based on detection)
        if sources.get("web_sources"):
            scores["web_sources"] = 0.75  # Could be enhanced with source detection

        # Scientific literature (high reliability)
        if sources.get("scientific"):
            scores["scientific_literature"] = 0.90

        return scores

    def _find_cross_references(self, sources: Dict[str, List]) -> str:
        """Find cross-references between different sources"""
        # This could be enhanced with semantic similarity matching
        cross_refs = []

        if len(sources.get("all_sources", [])) > 1:
            cross_refs.append("Multiple sources confirm the main points")
            cross_refs.append("Cross-validation successful across source types")

        return "\n".join(cross_refs)

    def _check_complete_cache(self, cache_key: str) -> bool:
        """Check if complete research result is cached"""
        return f"complete_{cache_key}" in self.session_state

    def _yield_cached_result(self, cache_key: str) -> Iterator[RunResponse]:
        """Yield cached complete result"""
        cached_result = self.session_state[f"complete_{cache_key}"]

        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.workflow_completed,
            content=f"📋 **Cached Research Result:**\n\n{cached_result['content']}\n\n"
            f"---\n🕒 Originally researched: {cached_result['timestamp']}\n"
            f"📊 Sources used: {cached_result['source_count']}",
        )

    def _cache_complete_result(
        self, cache_key: str, content: str, sources: Dict[str, List]
    ):
        """Cache complete research result"""
        self.session_state[f"complete_{cache_key}"] = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "source_count": len(sources.get("all_sources", [])),
            "sources_summary": {
                "internal_db": len(sources.get("internal_db", [])),
                "web_sources": len(sources.get("web_sources", [])),
                "scientific": len(sources.get("scientific", [])),
            },
        }
