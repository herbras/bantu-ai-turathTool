#!/usr/bin/env python3
"""
API Workflow Examples - Demonstrating Turath AI Workflow REST API
"""

import httpx
import asyncio
import json
import time


BASE_URL = "http://localhost:8000"  # Adjust based on your setup
WORKFLOWS_URL = f"{BASE_URL}/workflows"


async def example_quick_research_api():
    """Example: Quick research via API"""
    print("🔍 Example 1: Quick Research via API")

    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "research_query": "حكم زكاة الذهب المُدَّخر للزينة",
            "research_type": "quick",
            "output_format": "summary",
            "include_scientific": False,
            "include_web_sources": True,
            "max_sources": 5,
        }

        response = await client.post(f"{WORKFLOWS_URL}/research/run", json=payload)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Workflow completed: {result['workflow_id']}")
            print(f"📝 Result preview: {result['result'][:200]}...")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")


async def example_comprehensive_research_api():
    """Example: Comprehensive research dengan multi-source via API"""
    print("📚 Example 2: Comprehensive Research via API")

    async with httpx.AsyncClient(timeout=120.0) as client:
        payload = {
            "research_query": "penggunaan AI dalam sistem perbankan syariah",
            "research_type": "comprehensive",
            "output_format": "article",
            "include_scientific": True,
            "include_web_sources": True,
            "max_sources": 15,
            "session_id": "comprehensive-ai-banking",
        }

        response = await client.post(f"{WORKFLOWS_URL}/research/run", json=payload)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Comprehensive workflow completed: {result['workflow_id']}")
            print(f"📊 Progress stages: {len(result['progress_log'])}")
            print(f"📝 Result length: {len(result['result'])} characters")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")


async def example_streaming_research_api():
    """Example: Streaming research workflow"""
    print("🌊 Example 3: Streaming Research via API")

    async with httpx.AsyncClient(timeout=120.0) as client:
        payload = {
            "research_query": "التكييف الفقهي للذكاء الاصطناعي التوليدي",
            "research_type": "comprehensive",
            "output_format": "article",
        }

        async with client.stream(
            "POST",
            f"{WORKFLOWS_URL}/research/stream",
            json=payload,
            headers={"Accept": "text/plain"},
        ) as response:
            if response.status_code == 200:
                print("🔥 Streaming workflow started...")

                async for chunk in response.aiter_text():
                    if chunk.startswith("data: "):
                        try:
                            data = json.loads(chunk[6:])  # Remove "data: " prefix

                            if data["event"] == "workflow_progress":
                                print(f"📋 {data['content']}")
                            elif data["event"] == "workflow_completed":
                                print(
                                    f"✅ Completed! Result length: {len(data['content'])}"
                                )
                                break
                            elif data["event"] == "workflow_failed":
                                print(f"❌ Failed: {data['content']}")
                                break

                        except json.JSONDecodeError:
                            continue
            else:
                print(f"❌ Streaming error: {response.status_code}")


async def example_publication_workflow_api():
    """Example: Academic publication workflow via API"""
    print("📖 Example 4: Publication Workflow via API")

    async with httpx.AsyncClient(
        timeout=300.0
    ) as client:  # Long timeout for academic work
        payload = {
            "publication_topic": "تطبيق مقاصد الشريعة في النوازل المعاصرة",
            "publication_type": "academic_paper",
            "target_audience": "academic",
            "citation_style": "chicago",
            "peer_review_rounds": 2,
            "word_count_target": 5000,
            "session_id": "maqasid-research-paper",
        }

        response = await client.post(f"{WORKFLOWS_URL}/publication/run", json=payload)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Publication workflow completed: {result['workflow_id']}")
            print("📄 Academic paper generated")
            print(f"📊 Progress stages: {len(result['progress_log'])}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")


async def example_workflow_management_api():
    """Example: Workflow management and monitoring"""
    print("⚙️ Example 5: Workflow Management via API")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # List all workflows
        response = await client.get(f"{WORKFLOWS_URL}/")
        if response.status_code == 200:
            workflows = response.json()
            print(f"📋 Active workflows: {workflows['total']}")

            for workflow in workflows["workflows"]:
                print(
                    f"  - {workflow['workflow_id']}: {workflow['status']} ({workflow['session_id']})"
                )

        # Check workflow templates
        response = await client.get(f"{WORKFLOWS_URL}/templates")
        if response.status_code == 200:
            templates = response.json()
            print("📋 Available templates:")
            print(f"  - Research: {list(templates['research_templates'].keys())}")
            print(f"  - Publication: {list(templates['publication_templates'].keys())}")

        # Health check
        response = await client.get(f"{WORKFLOWS_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"💚 Workflow service: {health['status']}")
            print(f"🔧 Features: {', '.join(health['features'])}")


async def example_quick_endpoint_api():
    """Example: Using the quick research endpoint"""
    print("⚡ Example 6: Quick Research Endpoint")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Simple query parameter approach
        params = {"query": "أحكام صلاة المسافر"}

        response = await client.post(f"{WORKFLOWS_URL}/research/quick", params=params)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Quick research completed: {result['workflow_id']}")
            print(f"📝 Quick answer: {result['result'][:300]}...")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")


async def example_parallel_workflows_api():
    """Example: Running multiple workflows in parallel via API"""
    print("⚡ Example 7: Parallel Workflows via API")

    topics = [
        "حكم التجارة الإلكترونية",
        "ضوابط الاستثمار في العملات الرقمية",
        "فقه النوازل في الطب الحديث",
    ]

    async def run_single_research(client: httpx.AsyncClient, topic: str):
        payload = {
            "research_query": topic,
            "research_type": "quick",
            "output_format": "summary",
            "max_sources": 5,
        }

        response = await client.post(f"{WORKFLOWS_URL}/research/run", json=payload)
        return topic, response

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Run all workflows concurrently
        tasks = [run_single_research(client, topic) for topic in topics]
        results = await asyncio.gather(*tasks)

        print("📊 Parallel workflows completed:")
        for topic, response in results:
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ {topic}: {result['workflow_id']} - {result['status']}")
            else:
                print(f"  ❌ {topic}: Failed ({response.status_code})")


async def example_caching_demo_api():
    """Example: Demonstrating workflow caching via API"""
    print("💾 Example 8: Caching Demo via API")

    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "research_query": "أحكام صلاة المسافر",
            "research_type": "comprehensive",
            "session_id": "caching-demo-session",
            "use_cache": True,
        }

        # First run
        print("🔄 First run (should process fully)...")
        start_time = time.time()
        response1 = await client.post(f"{WORKFLOWS_URL}/research/run", json=payload)
        first_time = time.time() - start_time

        if response1.status_code == 200:
            result1 = response1.json()
            print(
                f"✅ First run completed in {first_time:.1f}s: {result1['workflow_id']}"
            )

        # Second run (should use cache)
        print("🔄 Second run (should use cache)...")
        start_time = time.time()
        response2 = await client.post(f"{WORKFLOWS_URL}/research/run", json=payload)
        second_time = time.time() - start_time

        if response2.status_code == 200:
            result2 = response2.json()
            print(
                f"⚡ Second run completed in {second_time:.1f}s: {result2['workflow_id']}"
            )
            print(f"🚀 Speed improvement: {first_time / second_time:.1f}x faster!")


async def example_error_handling_api():
    """Example: Error handling and edge cases"""
    print("🛡️ Example 9: Error Handling via API")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test invalid workflow ID
        response = await client.get(f"{WORKFLOWS_URL}/invalid-workflow-id")
        print(f"❌ Invalid workflow ID: {response.status_code} - {response.json()}")

        # Test missing required field
        invalid_payload = {
            "research_type": "quick"  # Missing research_query
        }

        response = await client.post(
            f"{WORKFLOWS_URL}/research/run", json=invalid_payload
        )
        print(f"❌ Missing field: {response.status_code}")

        # Test workflow cancellation
        # Start a workflow first
        payload = {
            "research_query": "test query for cancellation",
            "research_type": "quick",
        }

        response = await client.post(f"{WORKFLOWS_URL}/research/run", json=payload)
        if response.status_code == 200:
            workflow_id = response.json()["workflow_id"]

            # Try to cancel/delete it
            delete_response = await client.delete(f"{WORKFLOWS_URL}/{workflow_id}")
            if delete_response.status_code == 200:
                print(f"✅ Workflow cancelled: {delete_response.json()}")


async def run_all_api_examples():
    """Run all API examples"""
    examples = [
        example_quick_research_api,
        example_comprehensive_research_api,
        example_streaming_research_api,
        example_publication_workflow_api,
        example_workflow_management_api,
        example_quick_endpoint_api,
        example_parallel_workflows_api,
        example_caching_demo_api,
        example_error_handling_api,
    ]

    print("🚀 Running all API workflow examples...")
    print("=" * 60)

    for i, example in enumerate(examples, 1):
        print(f"\n{'=' * 60}")
        print(f"Running Example {i}: {example.__name__}")
        print("=" * 60)

        try:
            await example()
            print("✅ Example completed successfully")
        except Exception as e:
            print(f"❌ Example failed: {e}")

        if i < len(examples):
            print("\n⏳ Waiting 2 seconds before next example...")
            await asyncio.sleep(2)

    print("\n" + "=" * 60)
    print("🎉 All API examples completed!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        example_num = int(sys.argv[1])
        examples = [
            example_quick_research_api,
            example_comprehensive_research_api,
            example_streaming_research_api,
            example_publication_workflow_api,
            example_workflow_management_api,
            example_quick_endpoint_api,
            example_parallel_workflows_api,
            example_caching_demo_api,
            example_error_handling_api,
        ]

        if 1 <= example_num <= len(examples):
            asyncio.run(examples[example_num - 1]())
        else:
            print(f"Example number must be between 1 and {len(examples)}")
    else:
        asyncio.run(run_all_api_examples())
