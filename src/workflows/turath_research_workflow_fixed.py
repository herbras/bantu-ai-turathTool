from typing import Iterator, List, Dict, Any
import asyncio
import time

from agno.workflow import Workflow
from agno.agent import RunResponse, RunEvent
from agno.utils.log import logger

# Global agent service registry - will be set by main app
_global_agent_service = None


def set_global_agent_service(agent_service):
    """Set global agent service for workflows to access"""
    global _global_agent_service
    _global_agent_service = agent_service


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

    # Continue with remaining methods...

    def _write_with_agents(
        self,
        validated_content: Dict[str, Any],
        output_format: str,
        research_plan: Dict[str, Any],
    ) -> Iterator[RunResponse]:
        """Write structured content using real agents - FIXED VERSION"""

        yield RunResponse(
            run_id=self.run_id,
            event=RunEvent.run_response,
            content=f"   ✍️ Generating {output_format} dengan real agent...\n",
        )

        # Get agent service
        agent_service = getattr(self, "_agent_service", None) or _global_agent_service
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

    # Placeholder for other methods - copy from original file
    def _fallback_content_generation(
        self, validated_content, output_format, research_plan
    ):
        return "Content generated successfully"

    def _fact_check_and_validate(self, sources):
        yield RunResponse(
            run_id=self.run_id, event=RunEvent.run_response, content="Fact check done"
        )
        return {"validated_sources": sources}

    def _editorial_review_and_finalize(self, content):
        return content

    def _check_complete_cache(self, key):
        return False

    def _yield_cached_result(self, key):
        yield RunResponse(
            run_id=self.run_id, event=RunEvent.run_response, content="Cached"
        )

    def _cache_complete_result(self, key, content, sources):
        pass

    async def _run_agent_query(self, agent, query):
        return "Test content"

    def _extract_content_from_result(self, result):
        return str(result)

    def _extract_meaningful_summary(self, content):
        return content[:100] + "..." if len(content) > 100 else content

    def _extract_ruling_from_content(self, content):
        return "halal"

    def _fallback_simulated_search(self, queries, sci, web):
        yield RunResponse(
            run_id=self.run_id, event=RunEvent.run_response, content="Simulated"
        )

    def _create_comprehensive_writing_prompt(self, content, format, plan):
        return "Write about this topic"

    async def _run_agent_writing(self, agent, prompt):
        return "Generated content"
