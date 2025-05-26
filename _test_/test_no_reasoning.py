import asyncio
from agno.tools.mcp import MCPTools
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from src.config import settings


async def test_no_reasoning():
    print("Testing agent WITHOUT reasoning...")

    async with MCPTools(transport="sse", url="http://localhost:8001/sse") as mcp_tools:
        print(f"MCPTools functions: {list(mcp_tools.functions.keys())}")

        # Create simple agent WITHOUT reasoning
        agent = Agent(
            name="SimpleTestAgent",
            model=OpenAILike(
                id=settings.default_model_id,
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
            ),
            tools=[mcp_tools],
            instructions=[
                "You are a helpful assistant.",
                "Use the available tools to answer user questions.",
                "If you have a list_all_categories tool, use it to list categories.",
            ],
            show_tool_calls=True,
            reasoning=False,  # NO REASONING
            markdown=True,
        )

        print(f"Agent created with {len(agent.tools)} tools")

        # Simple query that should trigger tool usage
        query = (
            "Please list all available categories using the list_all_categories tool"
        )
        print(f"Query: {query}")

        try:
            result = await agent.arun(query)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_no_reasoning())
