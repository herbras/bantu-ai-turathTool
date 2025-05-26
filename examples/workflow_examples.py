#!/usr/bin/env python3
"""
Comprehensive examples of Turath Workflows
Menunjukkan berbagai use cases dan konfigurasi workflow
"""

import asyncio
from agno.storage.workflow.sqlite import SqliteWorkflowStorage
from agno.utils.pprint import pprint_run_response

from src.workflows import TurathResearchWorkflow, TurathPublicationWorkflow


def example_quick_research():
    """Example: Quick research untuk jawaban fatwa"""
    print("🔍 Example 1: Quick Research untuk Fatwa")

    workflow = TurathResearchWorkflow(
        session_id="quick-research-zakat-emas",
        storage=SqliteWorkflowStorage(
            table_name="turath_research_workflows", db_file="workflows.db"
        ),
    )

    response = workflow.run(
        research_query="حكم زكاة الذهب المُدَّخر للزينة",
        research_type="quick",
        output_format="summary",
        include_scientific=False,
        include_web_sources=True,
        max_sources=5,
    )

    pprint_run_response(response, markdown=True)


def example_comprehensive_research():
    """Example: Comprehensive research dengan multi-source"""
    print("📚 Example 2: Comprehensive Research - AI in Islamic Banking")

    workflow = TurathResearchWorkflow(
        session_id="comprehensive-ai-islamic-banking",
        storage=SqliteWorkflowStorage(
            table_name="turath_research_workflows", db_file="workflows.db"
        ),
    )

    response = workflow.run(
        research_query="penggunaan AI dalam sistem perbankan syariah",
        research_type="comprehensive",
        output_format="article",
        include_scientific=True,  # Include ArXiv + PubMed
        include_web_sources=True,  # Include Tavily web search
        max_sources=15,
    )

    pprint_run_response(response, markdown=True)


def example_academic_publication():
    """Example: Academic paper dengan peer review"""
    print("📖 Example 3: Academic Publication - Maqasid Research")

    workflow = TurathPublicationWorkflow(
        session_id="academic-maqasid-shariah",
        storage=SqliteWorkflowStorage(
            table_name="turath_publication_workflows", db_file="workflows.db"
        ),
    )

    response = workflow.run(
        publication_topic="تطبيق مقاصد الشريعة في النوازل المعاصرة",
        publication_type="academic_paper",
        target_audience="academic",
        citation_style="chicago",
        peer_review_rounds=3,
        word_count_target=8000,
    )

    pprint_run_response(response, markdown=True)


def example_book_chapter():
    """Example: Book chapter untuk publikasi"""
    print("📘 Example 4: Book Chapter - Islamic Bioethics")

    workflow = TurathPublicationWorkflow(
        session_id="book-chapter-bioethics",
        storage=SqliteWorkflowStorage(
            table_name="turath_publication_workflows", db_file="workflows.db"
        ),
    )

    response = workflow.run(
        publication_topic="Islamic Bioethics in Modern Medical Practice",
        publication_type="book_chapter",
        target_audience="general",
        citation_style="apa",
        peer_review_rounds=2,
        word_count_target=5000,
    )

    pprint_run_response(response, markdown=True)


def example_parallel_workflows():
    """Example: Running multiple workflows in parallel"""
    print("⚡ Example 5: Parallel Workflows")

    async def run_parallel():
        # Multiple research topics simultaneously
        topics = [
            "حكم التجارة الإلكترونية",
            "ضوابط الاستثمار في العملات الرقمية",
            "فقه النوازل في الطب الحديث",
        ]

        workflows = []
        for i, topic in enumerate(topics):
            workflow = TurathResearchWorkflow(
                session_id=f"parallel-research-{i}",
                storage=SqliteWorkflowStorage(
                    table_name="turath_research_workflows", db_file="workflows.db"
                ),
            )
            workflows.append(
                workflow.run(
                    research_query=topic, research_type="quick", output_format="summary"
                )
            )

        # Run all workflows concurrently
        results = await asyncio.gather(*workflows)

        for i, result in enumerate(results):
            print(f"\n--- Results for: {topics[i]} ---")
            pprint_run_response(result, markdown=True)

    asyncio.run(run_parallel())


def example_cached_workflow():
    """Example: Demonstrating workflow caching"""
    print("💾 Example 6: Workflow Caching")

    workflow = TurathResearchWorkflow(
        session_id="cached-workflow-demo",  # Same session_id = shared cache
        storage=SqliteWorkflowStorage(
            table_name="turath_research_workflows", db_file="workflows.db"
        ),
    )

    query = "أحكام صلاة المسافر"

    print("First run (will process fully):")
    response1 = workflow.run(
        research_query=query, research_type="comprehensive", use_cache=True
    )
    pprint_run_response(response1, markdown=True, show_time=True)

    print("\nSecond run (should use cache):")
    response2 = workflow.run(
        research_query=query, research_type="comprehensive", use_cache=True
    )
    pprint_run_response(response2, markdown=True, show_time=True)


def example_custom_configuration():
    """Example: Custom workflow configuration"""
    print("⚙️ Example 7: Custom Configuration")

    # Research workflow with specific configuration
    research_workflow = TurathResearchWorkflow(
        session_id="custom-config-research",
        storage=SqliteWorkflowStorage(
            table_name="custom_research_workflows", db_file="custom_workflows.db"
        ),
        debug_mode=True,  # Enable detailed logging
    )

    # Publication workflow with different config
    publication_workflow = TurathPublicationWorkflow(
        session_id="custom-config-publication",
        storage=SqliteWorkflowStorage(
            table_name="custom_publication_workflows", db_file="custom_workflows.db"
        ),
    )

    # Research stage
    research_response = research_workflow.run(
        research_query="الذكاء الاصطناعي ومستقبل الفتوى",
        research_type="academic",
        output_format="article",
        include_scientific=True,
        include_web_sources=True,
    )

    print("Research phase completed. Starting publication phase...")

    # Publication stage using research results
    publication_response = publication_workflow.run(
        publication_topic="الذكاء الاصطناعي ومستقبل الفتوى: دراسة فقهية معاصرة",
        publication_type="academic_paper",
        citation_style="islamic_traditional",
        peer_review_rounds=2,
    )

    pprint_run_response(publication_response, markdown=True)


def example_workflow_monitoring():
    """Example: Monitoring workflow progress"""
    print("📊 Example 8: Workflow Progress Monitoring")

    workflow = TurathResearchWorkflow(
        session_id="monitored-workflow",
        storage=SqliteWorkflowStorage(
            table_name="monitored_workflows", db_file="workflows.db"
        ),
    )

    # Monitor each stage of the workflow
    response_stream = workflow.run(
        research_query="التكييف الفقهي للذكاء الاصطناعي التوليدي",
        research_type="comprehensive",
        output_format="article",
    )

    stage_count = 0
    for response in response_stream:
        if response.event.value == "workflow_progress":
            stage_count += 1
            print(f"Stage {stage_count}: {response.content}")
        elif response.event.value == "workflow_completed":
            print("🎉 Workflow completed!")
            print(
                response.content[:500] + "..."
                if len(response.content) > 500
                else response.content
            )


def run_all_examples():
    """Run semua examples"""
    examples = [
        example_quick_research,
        example_comprehensive_research,
        example_academic_publication,
        example_book_chapter,
        example_parallel_workflows,
        example_cached_workflow,
        example_custom_configuration,
        example_workflow_monitoring,
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n{'=' * 60}")
        print(f"Running Example {i}: {example.__name__}")
        print("=" * 60)

        try:
            example()
        except Exception as e:
            print(f"❌ Error in {example.__name__}: {e}")

        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        example_num = int(sys.argv[1])
        examples = [
            example_quick_research,
            example_comprehensive_research,
            example_academic_publication,
            example_book_chapter,
            example_parallel_workflows,
            example_cached_workflow,
            example_custom_configuration,
            example_workflow_monitoring,
        ]

        if 1 <= example_num <= len(examples):
            examples[example_num - 1]()
        else:
            print(f"Example number must be between 1 and {len(examples)}")
    else:
        print("🚀 Running all workflow examples...")
        run_all_examples()
